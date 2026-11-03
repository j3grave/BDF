"""
athena_setup.py - Fase 2: criar as tabelas no Glue Data Catalog (via Athena) e validá-las.

Objetivo:
    Correr o DDL de sql/athena/ddl/ para registar no Glue Data Catalog a base de dados
    movielens_<dataset> e uma tabela por pasta de data/cloud/<pasta>/ (já enviada para o S3).
    Usamos DDL escrito à mão em vez de um crawler do Glue para controlar os tipos: ficam
    exatamente os do manifesto. Antes de enviar o DDL, o script confirma, sem AWS, que as
    colunas e os tipos de cada CREATE TABLE coincidem com os ficheiros locais. Depois de
    criar as tabelas, confirma no Athena que o n.º de linhas de cada tabela (e de cada
    ano de ratings_part) é igual ao dos ficheiros locais.

Entradas:
    sql/athena/ddl/*.sql                 DDL com os marcadores ${database}, ${bucket} e ${pasta}
    data/cloud/<pasta>/                  criado pelo prepare_cloud.py (para comparar schemas e contagens)
    config.yaml (secção aws)             região e buckets (ou as opções da linha de comandos)

Saídas:
    Base de dados e tabelas no Glue Data Catalog. Localmente, só o resumo no ecrã.
    Termina com erro se o DDL não coincidir com os ficheiros ou se alguma contagem falhar.

Como correr:
    python scripts/athena_setup.py --dry-run                     sem AWS: verifica o DDL e mostra-o
    python scripts/athena_setup.py --bucket-dados X --bucket-resultados Y
    python scripts/athena_setup.py --recriar                     apaga e recria as tabelas
    (por omissão usa o dataset 32m; apagar uma tabela EXTERNAL não apaga os dados no S3)
"""
import argparse
import re
import sys

import duckdb

from athena_common import ATHENA_SQL, Athena, AthenaError, add_aws_args, aws_settings, read_sql, require_buckets
from common import DATASETS, ROOT, SCHEMAS, duckdb_columns, load_config
from prepare_cloud import ATHENA_TYPES, DATASET_OMISSAO, count_of, counts_by_year, schema_of

# Apanha o nome da tabela, a lista de colunas e (se existir) a lista de partições de um CREATE TABLE
RE_CREATE = re.compile(r'CREATE\s+EXTERNAL\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(\w+)\s*\((.*?)\)'
                       r'(?:\s*PARTITIONED\s+BY\s*\((.*?)\))?', re.IGNORECASE | re.DOTALL)


def parse_args():
    """Lê --dataset (por omissão 32m), --recriar e as opções da AWS."""
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dataset', choices=list(DATASETS), default=DATASET_OMISSAO,
                        help=f'dataset (por omissão: {DATASET_OMISSAO})')
    parser.add_argument('--recriar', action='store_true',
                        help='DROP TABLE antes de criar (não apaga os dados no S3)')
    add_aws_args(parser)
    return parser.parse_args()


def parse_columns(texto):
    """'userid int, `timestamp` bigint' -> [('userid', 'int'), ('timestamp', 'bigint')]"""
    colunas = []
    for parte in texto.split(','):
        nome, tipo = parte.split()
        colunas.append((nome.strip('`').lower(), tipo.lower()))
    return colunas


def ddl_statements(params):
    """Lista de (ficheiro, tabela ou None, sql) pela ordem dos ficheiros de sql/athena/ddl/."""
    instrucoes = []
    for path in sorted((ATHENA_SQL / 'ddl').glob('*.sql')):
        sql = read_sql(path, params)
        m = RE_CREATE.search(sql)
        instrucoes.append((path.name, m.group(1).lower() if m else None, sql))
    return instrucoes


def local_schema(con, cloud_dir, table):
    """Colunas e tipos (no formato do Athena) dos ficheiros locais de uma tabela."""
    if table == 'ratings_csv':
        colunas = list(SCHEMAS['ratings'].items())     # tipos com que o CSV é lido no pipeline
    elif table == 'ratings_part':
        colunas = schema_of(con, (cloud_dir / table / '*' / '*.parquet').as_posix(), hive=False)
    else:
        colunas = schema_of(con, (cloud_dir / table / '*.parquet').as_posix())
    return [(nome.lower(), ATHENA_TYPES[tipo]) for nome, tipo in colunas]


def local_count(con, cloud_dir, table):
    """N.º de linhas dos ficheiros locais de uma tabela."""
    if table == 'ratings_csv':
        csv_file = (cloud_dir / table / 'ratings.csv').as_posix()
        return con.execute(f"""
            SELECT count(*) FROM read_csv('{csv_file}', header=true, delim=',', quote='"', escape='"',
                                          columns={duckdb_columns(SCHEMAS['ratings'])})
        """).fetchone()[0]
    if table == 'ratings_part':
        return count_of(con, (cloud_dir / table / '*' / '*.parquet').as_posix(), hive=True)
    return count_of(con, (cloud_dir / table / '*.parquet').as_posix())


def check_ddl(con, cloud_dir, instrucoes):
    """Compara as colunas de cada CREATE TABLE com os ficheiros locais. Devolve a lista de problemas."""
    problemas = []
    for ficheiro, table, sql in instrucoes:
        if table is None or not (cloud_dir / table).exists():
            continue
        m = RE_CREATE.search(sql)
        no_ddl = parse_columns(m.group(2))
        nos_ficheiros = local_schema(con, cloud_dir, table)
        if no_ddl != nos_ficheiros:
            problemas.append(f'{ficheiro}: colunas {no_ddl} diferentes dos ficheiros {nos_ficheiros}')
        particoes = parse_columns(m.group(3)) if m.group(3) else []
        esperado = [('year', 'int')] if table == 'ratings_part' else []
        if particoes != esperado:
            problemas.append(f'{ficheiro}: partições {particoes}, esperado {esperado}')
    return problemas


def main():
    """Verifica o DDL, cria a base de dados e as tabelas no Athena e valida as contagens."""
    args = parse_args()
    cfg = load_config(args.dataset)
    aws = aws_settings(cfg, args)
    cloud_dir = ROOT / 'data' / 'cloud' / aws['pasta']
    print(f"[athena_setup] dataset={cfg['dataset']} base de dados={aws['database']} "
          f"região={aws['region']} {'(dry-run: sem AWS)' if args.dry_run else ''}")

    if not cloud_dir.exists():
        sys.exit(f'Erro: não existe {cloud_dir.relative_to(ROOT)}. '
                 f"Corre primeiro: python scripts/prepare_cloud.py --dataset {cfg['dataset']}")
    if not args.dry_run:
        require_buckets(aws)

    params = {'database': aws['database'], 'pasta': aws['pasta'],
              'bucket': aws.get('bucket_dados') or '<bucket-dados>'}
    # Só as tabelas que existem neste dataset (o 1M não tem tags nem links)
    instrucoes = [(f, t, s) for f, t, s in ddl_statements(params) if t is None or (cloud_dir / t).exists()]
    tabelas = [t for _, t, _ in instrucoes if t]

    # 1. Sem AWS: o DDL tem de coincidir com os ficheiros que foram (ou vão) para o S3
    con = duckdb.connect()
    problemas = check_ddl(con, cloud_dir, instrucoes)
    if problemas:
        print('[athena_setup] ERRO: o DDL não coincide com os ficheiros locais:', file=sys.stderr)
        for p in problemas:
            print(f'  - {p}', file=sys.stderr)
        sys.exit(1)
    print(f'  DDL verificado contra data/cloud/{aws["pasta"]}/: {len(tabelas)} tabelas, colunas e tipos iguais')

    if args.dry_run:
        for ficheiro, _, sql in instrucoes:
            print(f'\n-- {ficheiro}\n{sql};')
        return

    # 2. Base de dados e tabelas. A base de dados corre sem contexto; o resto dentro dela.
    athena = Athena(aws)
    try:
        for ficheiro, table, sql in instrucoes:
            if args.recriar and table:
                athena.run(f'DROP TABLE IF EXISTS `{table}`', aws['database'])
            database = None if ficheiro.startswith('00_') else aws['database']
            stats = athena.run(sql, database)
            print(f'  {ficheiro:32} OK ({stats["total_s"]:.1f} s)')

        # 3. Validação: contagens no Athena iguais às dos ficheiros locais
        print('[athena_setup] validação das contagens (Athena vs data/cloud/)')
        custo_bytes = 0
        for table in tabelas:
            stats = athena.run(f'SELECT count(*) FROM {table}', aws['database'])
            custo_bytes += stats['scanned_bytes']
            n_athena = int(athena.rows(stats['id'])[0][0])
            n_local = local_count(con, cloud_dir, table)
            estado = 'OK' if n_athena == n_local else 'DIFERENTE'
            if n_athena != n_local:
                problemas.append(f'{table}: {n_athena} linhas no Athena, {n_local} nos ficheiros')
            print(f'  {table:12} Athena {n_athena:>12,}  local {n_local:>12,}  {estado}')

        stats = athena.run('SELECT year, count(*) FROM ratings_part GROUP BY year ORDER BY year', aws['database'])
        custo_bytes += stats['scanned_bytes']
        por_ano_athena = {int(ano): int(n) for ano, n in athena.rows(stats['id'])}
        por_ano_local = counts_by_year(con, (cloud_dir / 'ratings_part' / '*' / '*.parquet').as_posix())
        if por_ano_athena != por_ano_local:
            diferentes = sorted(a for a in set(por_ano_athena) | set(por_ano_local)
                                if por_ano_athena.get(a) != por_ano_local.get(a))
            problemas.append(f'ratings_part: contagens por ano diferentes nos anos {diferentes} '
                             '(faltou o MSCK REPAIR TABLE?)')
        print(f'  ratings_part {len(por_ano_athena)} partições no Athena, {len(por_ano_local)} nos ficheiros')
    except AthenaError as erro:
        sys.exit(f'[athena_setup] ERRO no Athena: {erro}')

    print(f'  dados lidos na validação: {custo_bytes / 1e6:.1f} MB')
    if problemas:
        print('[athena_setup] ERRO: a validação falhou:', file=sys.stderr)
        for p in problemas:
            print(f'  - {p}', file=sys.stderr)
        sys.exit(1)
    print(f"[athena_setup] tabelas criadas e validadas em {aws['database']}")


if __name__ == '__main__':
    main()
