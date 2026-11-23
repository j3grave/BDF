"""
07_athena_setup.py - Bloco cloud, passo 3 de 4: criar as tabelas no Glue Data Catalog (via Athena) e validá-las.

Objetivo:
    Correr o DDL de sql/athena/ddl/ para registar no Glue Data Catalog a base de dados
    movielens_<dataset> e uma tabela por pasta de data/cloud/<pasta>/ (já enviada para o S3).
    Usamos DDL escrito à mão em vez de um crawler do Glue para controlar os tipos ( ficam
    exatamente os dos ficheiros). Antes de enviar o DDL, o script confirma, sem AWS, que as
    colunas e os tipos de cada CREATE TABLE coincidem com os ficheiros locais. Depois de
    criar as tabelas, confirma no Athena que o n.º de linhas de cada tabela (e de cada
    ano de ratings_part) é igual ao dos ficheiros locais.

Porquê usar o DDL - Data Definition Language - em vês de um crawler do Glue:
    (1) Controlo do esquema - O crawler adivinha o esquema a partir dos ficheiros, com o MovieLens costuma correr mal. Os títulos em movies.csv têm vírgulas dentro de aspas (por exemplo "American President, The (1995)"), e um crawler sobre CSV tende a partir essas linhas;
    (2)pode inferir timestamp como bigint ou string, ou os IDs com tipos diferentes entre tabelas;
    (3)com DDL permite decidir o tipo de cada coluna, o SerDe (OpenCSVSerDe) e o skip.header.line.count;
    (4) Reprodutibilidade - o DDL fica guardado em ficheiros .sql no Git, e o passo cloud corre com um só comando e cria sempre as mesmas tabelas.
    (5) Benchmark - Para comparar os 877 MB em CSV, 94 MB em Parquet e 4,7 MB em Parquet particionado, as três tabelas têm de ter exatamente as mesmas colunas e tipos. Só assim a diferença se deve ao formato e não ao esquema. No caso particionado, o DDL com PARTITIONED BY (seguido de MSCK REPAIR TABLE ou partition projection) também garante que as 29 partições são reconhecidas como queres;
    (6) Custo e tempo - No Athena, as instruções DDL não são cobradas e correm em segundos. O crawler cobra por DPU-hora, com um mínimo faturado por execução, demora um ou dois minutos a correr e precisa de uma IAM role. No Learner Lab, as permissões de IAM são limitadas (fonte claude)

Nota: Faz sentido usar o crawler, quando se desconhece os dados ou o esquema muda com frequência, por exemplo pastas novas ou colunas acrescentadas. No nosso projeto o esquema é conhecido e estável, por isso o DDL escrito à mão dá mais controlo, sai mais barato e é reprodutível. 

Entradas:
    sql/athena/ddl/*.sql                 DDL com os marcadores ${database}, ${bucket} e ${pasta}
    data/cloud/<pasta>/                  criado pelo 05_prepare_cloud.py (para comparar schemas e contagens)
    config.yaml (secção aws)             região e buckets (se ficarem a null, derivados do ID da conta)

Saídas:
    Base de dados e tabelas no Glue Data Catalog. Localmente, só o resumo no ecrã.
    Termina com erro se o DDL não coincidir com os ficheiros ou se alguma contagem falhar.
    As tabelas são sempre apagadas e criadas de novo, para o MSCK REPAIR TABLE ver o upload
    (apagar uma tabela EXTERNAL não apaga os dados no S3).
"""
import re
import sys

import duckdb

from athena_common import (ATHENA_SQL, ATHENA_TYPES, Athena, AthenaError, aws_settings, count_of,
                           counts_by_year, read_sql, resolve_buckets, schema_of)
from common import ROOT, SCHEMAS, duckdb_columns, load_config

# Grupos: 1 = nome da tabela, 2 = colunas, 3 = colunas de partição (se existirem)
RE_CREATE = re.compile(r'CREATE\s+EXTERNAL\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(\w+)\s*\((.*?)\)'
                        r'(?:\s*PARTITIONED\s+BY\s*\((.*?)\))?', re.IGNORECASE | re.DOTALL)


def parse_columns(texto):
    """'userid int, `timestamp` bigint' -> [('userid', 'int'), ('timestamp', 'bigint')]"""
    colunas = []
    for parte in texto.split(','):          # uma parte por coluna: "userid int"
        nome, tipo = parte.split()
        # Tira os backticks (`timestamp`) e passa tudo a minúsculas, como no catálogo do Athena
        colunas.append((nome.strip('`').lower(), tipo.lower()))
    return colunas


def ddl_statements(params):
    """Lista de (ficheiro, tabela ou None, sql) pela ordem dos ficheiros de sql/athena/ddl/."""
    instrucoes = []
    # Os ficheiros começam por 00_, 01_, ...: a ordem alfabética é a ordem de execução
    for path in sorted((ATHENA_SQL / 'ddl').glob('*.sql')):
        sql = read_sql(path, params)
        m = RE_CREATE.search(sql)
        # Ficheiros que não são CREATE TABLE (base de dados, MSCK REPAIR) ficam com tabela None
        if m:
            tabela = m.group(1).lower()
        else:
            tabela = None
        instrucoes.append((path.name, tabela, sql))
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
        # Só os CREATE TABLE de tabelas que existem neste dataset
        if table is None or not (cloud_dir / table).exists():
            continue
        m = RE_CREATE.search(sql)
        # Colunas: as do DDL (grupo 2 da regex) têm de ser iguais às dos ficheiros
        no_ddl = parse_columns(m.group(2))
        nos_ficheiros = local_schema(con, cloud_dir, table)
        if no_ddl != nos_ficheiros:
            problemas.append(f'{ficheiro}: colunas {no_ddl} diferentes dos ficheiros {nos_ficheiros}')
        # Partições (grupo 3): só o ratings_part é particionado, por year
        if m.group(3):
            particoes = parse_columns(m.group(3))
        else:
            particoes = []
        if table == 'ratings_part':
            esperado = [('year', 'int')]
        else:
            esperado = []
        if particoes != esperado:
            problemas.append(f'{ficheiro}: partições {particoes}, esperado {esperado}')
    return problemas


def criar_tabelas(athena, aws, instrucoes):
    """Corre o DDL no Athena: primeiro a base de dados, depois as tabelas dentro dela."""
    for ficheiro, table, sql in instrucoes:
        # Apaga a tabela antes de a criar (só o catálogo; os dados no S3 ficam)
        if table:
            athena.run(f'DROP TABLE IF EXISTS `{table}`', aws['database'])
        # 00_database.sql cria a base de dados, por isso ainda não pode correr "dentro" dela
        if ficheiro.startswith('00_'):
            database = None
        else:
            database = aws['database']
        stats = athena.run(sql, database)
        # Guarda depois de correr: a base de dados já existe quando o 00_ é guardado
        athena.guardar(f"{aws['database']} - ddl {ficheiro[:-4]}", sql, aws['database'],
                       f'DDL de sql/athena/ddl/{ficheiro} (07_athena_setup.py)')
        print(f'  {ficheiro:32} OK ({stats["total_s"]:.1f} s)')


def validar_contagens(athena, aws, con, cloud_dir, tabelas, problemas):
    """Compara as contagens no Athena com as dos ficheiros locais. Devolve os bytes lidos."""
    print('[athena_setup] validação das contagens (Athena vs data/cloud/)')
    custo_bytes = 0
    for table in tabelas:
        stats = athena.run(f'SELECT count(*) FROM {table}', aws['database'],
                           nome=f"{aws['database']} - validacao contagem {table}")
        custo_bytes += stats['scanned_bytes']
        n_athena = int(athena.rows(stats['id'])[0][0])
        n_local = local_count(con, cloud_dir, table)
        estado = 'OK' if n_athena == n_local else 'DIFERENTE'
        if n_athena != n_local:
            problemas.append(f'{table}: {n_athena} linhas no Athena, {n_local} nos ficheiros')
        print(f'  {table:12} Athena {n_athena:>12,}  local {n_local:>12,}  {estado}')

    # Contagens por ano: se o MSCK REPAIR TABLE não tiver visto as pastas, faltam anos
    stats = athena.run('SELECT year, count(*) FROM ratings_part GROUP BY year ORDER BY year', aws['database'],
                       nome=f"{aws['database']} - validacao contagem por ano")
    custo_bytes += stats['scanned_bytes']
    por_ano_athena = {}
    for ano, n in athena.rows(stats['id']):   # o Athena devolve texto: converte-se para int
        por_ano_athena[int(ano)] = int(n)
    por_ano_local = counts_by_year(con, (cloud_dir / 'ratings_part' / '*' / '*.parquet').as_posix())
    if por_ano_athena != por_ano_local:
        # Anos com contagens diferentes (incluindo anos que só existem num dos lados)
        diferentes = []
        for ano in sorted(set(por_ano_athena) | set(por_ano_local)):
            if por_ano_athena.get(ano) != por_ano_local.get(ano):
                diferentes.append(ano)
        problemas.append(f'ratings_part: contagens por ano diferentes nos anos {diferentes} '
                         '(faltou o MSCK REPAIR TABLE?)')
    print(f'  ratings_part {len(por_ano_athena)} partições no Athena, {len(por_ano_local)} nos ficheiros')
    return custo_bytes


def main():
    """Verifica o DDL, cria a base de dados e as tabelas no Athena e valida as contagens."""
    cfg = load_config()
    aws = aws_settings(cfg)
    cloud_dir = ROOT / 'data' / 'cloud' / aws['pasta']
    print(f"[athena_setup] dataset={cfg['dataset']} base de dados={aws['database']} região={aws['region']}")

    if not cloud_dir.exists():
        sys.exit(f'Erro: não existe {cloud_dir.relative_to(ROOT)}. Corre primeiro o 05_prepare_cloud.py.')
    resolve_buckets(aws)

    # Valores que substituem ${database}, ${pasta} e ${bucket} no DDL
    params = {'database': aws['database'], 'pasta': aws['pasta'], 'bucket': aws['bucket_dados']}
    instrucoes = ddl_statements(params)
    tabelas = []
    for _, tabela, _ in instrucoes:
        if tabela:
            tabelas.append(tabela)

    # 1. Sem AWS: o DDL tem de coincidir com os ficheiros que foram (ou vão) para o S3
    con = duckdb.connect()
    problemas = check_ddl(con, cloud_dir, instrucoes)
    if problemas:
        print('[athena_setup] ERRO: o DDL não coincide com os ficheiros locais:', file=sys.stderr)
        for p in problemas:
            print(f'  - {p}', file=sys.stderr)
        sys.exit(1)
    print(f'  DDL verificado contra data/cloud/{aws["pasta"]}/: {len(tabelas)} tabelas, colunas e tipos iguais')

    # 2 e 3. Base de dados, tabelas e validação das contagens
    athena = Athena(aws)
    try:
        criar_tabelas(athena, aws, instrucoes)
        custo_bytes = validar_contagens(athena, aws, con, cloud_dir, tabelas, problemas)
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
