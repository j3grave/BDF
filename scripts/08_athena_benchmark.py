"""
08_athena_benchmark.py - Bloco cloud, passo 4 de 4: benchmark DuckDB (local) vs Athena (S3) sobre os mesmos ficheiros.

Objetivo:
    Correr as mesmas perguntas nos dois motores e sobre os mesmos bytes: o DuckDB lê
    data/cloud/<pasta>/ no disco local e o Athena lê a cópia exata dessa pasta no S3.
    Cada query que usa ratings corre em três formatos (CSV, Parquet e Parquet particionado
    por ano); as que só usam movies correm uma vez, em Parquet.
    Cada combinação corre 3 vezes e guarda-se a mediana do tempo. No Athena regista-se
    também o tempo no motor e os dados lidos (DataScannedInBytes, aquilo que é cobrado),
    que é a métrica que melhor mostra o efeito do formato colunar e das partições.

Entradas:
    sql/athena/queries/*.sql        queries no dialeto do Athena (Trino)
    sql/<query>.sql                 a mesma query no dialeto do DuckDB (fase 1, não alterada)
    sql/cloud/<query>.sql           queries extra só do bloco cloud (dialeto do DuckDB)
    data/cloud/<pasta>/             criado pelo 05_prepare_cloud.py
    Tabelas no Athena               criadas pelo 07_athena_setup.py

Saídas:
    results/cloud_benchmarks.csv    motor, query, formato, mediana do tempo, tempo no motor,
                                    MB lidos e n.º de linhas (acrescenta linhas)
    As linhas de uma corrida só são escritas no fim, e só se cada query devolver o mesmo
    n.º de linhas no DuckDB e no Athena. Se alguma diferir (ou o Athena falhar a meio),
    essa corrida não fica no CSV e o script termina com erro.

Como correr:
    python scripts/08_athena_benchmark.py --engines duckdb             só a parte local, sem AWS
    python scripts/08_athena_benchmark.py --dry-run                    mostra o SQL do Athena, sem AWS
    python scripts/08_athena_benchmark.py --dataset small
    python scripts/08_athena_benchmark.py --bucket-dados X --bucket-resultados Y
    (por omissão: dataset do config.yaml, os dois motores e 3 corridas; os buckets, se não
    forem indicados nem estiverem no config.yaml, são derivados do ID da conta)

Notas:
    O tempo do Athena é o TotalExecutionTimeInMillis (inclui fila e planeamento) e o
    tempo no motor é o EngineExecutionTimeInMillis. O tempo do DuckDB é medido no relógio
    local, com uma ligação nova em cada corrida, como no 03_benchmark.py.
    A query 03 usa approx_percentile no Athena (não tem MEDIAN exata), por isso a mediana
    pode diferir ligeiramente; o n.º de linhas tem de ser igual nos dois motores.
"""
import argparse
import statistics
import sys
import time
from string import Template

import duckdb

from athena_common import (ATHENA_SQL, USD_POR_TB, Athena, AthenaError, add_aws_args, aws_settings, read_sql,
                           resolve_buckets)
from common import DATASETS, ROOT, SCHEMAS, append_row, duckdb_columns, load_config, now

RUNS = 3
MINIMO_COBRADO = 10e6   # o Athena cobra pelo menos 10 MB por query
FORMATOS_RATINGS = ['csv', 'parquet', 'parquet_part']

# No Athena, ${ratings} e ${movies} passam a nomes de tabelas. Nas tabelas sem partição,
# year é calculado a partir do timestamp, para as três versões terem as mesmas colunas
# (o mesmo truque do 03_benchmark.py). from_unixtime devolve a data em UTC.
ATHENA_SOURCES = {
    'csv': {'ratings': '(SELECT x.*, year(from_unixtime(x."timestamp")) AS year FROM ratings_csv AS x)',
            'movies': 'movies'},
    'parquet': {'ratings': '(SELECT x.*, year(from_unixtime(x."timestamp")) AS year FROM ratings AS x)',
                'movies': 'movies'},
    'parquet_part': {'ratings': 'ratings_part', 'movies': 'movies'},
}


def parse_args():
    """Lê --dataset, --engines, --runs e as opções da AWS."""
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dataset', choices=list(DATASETS), help='sobrepõe o valor de config.yaml')
    parser.add_argument('--engines', nargs='+', choices=['duckdb', 'athena'], default=['duckdb', 'athena'])
    parser.add_argument('--runs', type=int, default=RUNS, help=f'corridas por query e formato (por omissão: {RUNS})')
    add_aws_args(parser)
    return parser.parse_args()


def duckdb_sources(cloud_dir):
    """Texto SQL que substitui ${ratings} e ${movies} no DuckDB, para cada formato, em data/cloud/."""
    csv_file = (cloud_dir / 'ratings_csv' / 'ratings.csv').as_posix()
    flat = (cloud_dir / 'ratings' / '*.parquet').as_posix()
    part = (cloud_dir / 'ratings_part' / '*' / '*.parquet').as_posix()
    movies = f"read_parquet('{(cloud_dir / 'movies' / '*.parquet').as_posix()}')"
    # Mesmo cálculo do ano que o 05_prepare_cloud.py (com a sessão em UTC, ver connect_duckdb)
    year = 'year(to_timestamp("timestamp")) AS year'
    ler_csv = (f"read_csv('{csv_file}', header=true, delim=',', quote='\"', escape='\"', "
               f"columns={duckdb_columns(SCHEMAS['ratings'])})")
    return {
        'csv': {'ratings': f'(SELECT *, {year} FROM {ler_csv})', 'movies': movies},
        'parquet': {'ratings': f"(SELECT *, {year} FROM read_parquet('{flat}'))", 'movies': movies},
        'parquet_part': {'ratings': f"read_parquet('{part}', hive_partitioning=true)", 'movies': movies},
    }


def connect_duckdb():
    """Ligação nova ao DuckDB, com o fuso em UTC para o ano ser o mesmo do Athena."""
    con = duckdb.connect()
    con.execute("SET TimeZone = 'UTC'")
    return con


def load_queries():
    """Lista de (nome, sql_athena_template, sql_duckdb_template, formatos) para cada query."""
    queries = []
    for athena_file in sorted((ATHENA_SQL / 'queries').glob('*.sql')):
        nome = athena_file.stem
        # A versão DuckDB tem o mesmo nome: procura-se primeiro em sql/ (fase 1) e depois em sql/cloud/
        duckdb_file = None
        for candidato in (ROOT / 'sql' / f'{nome}.sql', ROOT / 'sql' / 'cloud' / f'{nome}.sql'):
            if candidato.exists():
                duckdb_file = candidato
                break
        if duckdb_file is None:
            sys.exit(f'Erro: {athena_file.name} não tem versão DuckDB em sql/ nem em sql/cloud/')
        texto_athena = athena_file.read_text()
        # Queries que só usam movies não dependem do formato dos ratings: correm uma vez
        if '${ratings}' in texto_athena:
            formatos = FORMATOS_RATINGS
        else:
            formatos = ['parquet']
        queries.append((nome, athena_file, duckdb_file.read_text(), formatos))
    return queries


def bench_duckdb(sql, runs):
    """Corre a query runs vezes (ligação nova em cada uma) e devolve (mediana em s, n.º de linhas)."""
    tempos = []
    for _ in range(runs):
        con = connect_duckdb()
        t0 = time.perf_counter()
        n_linhas = len(con.execute(sql).fetchall())
        tempos.append(time.perf_counter() - t0)
        con.close()
    return statistics.median(tempos), n_linhas


def bench_athena(athena, sql, database, runs):
    """Corre a query runs vezes no Athena e devolve as medianas, os MB lidos e o n.º de linhas."""
    corridas = [athena.run(sql, database) for _ in range(runs)]
    return {
        'median_s': statistics.median(c['total_s'] for c in corridas),
        'median_engine_s': statistics.median(c['engine_s'] for c in corridas),
        # Os bytes lidos são iguais em todas as corridas; fica o máximo, por segurança
        'scanned_bytes': max(c['scanned_bytes'] for c in corridas),
        'n_rows': athena.count_result_rows(corridas[0]['output']),
    }


def linha_duckdb(ds, nome, fmt, sql, runs):
    """Corre uma query no DuckDB, mostra o tempo e devolve a linha para o cloud_benchmarks.csv."""
    mediana, n = bench_duckdb(sql, runs)
    print(f'  duckdb  {nome:30} {fmt:13} {mediana * 1000:9.1f} ms  {n:>8,} linhas')
    return {'run_at': now(), 'dataset': ds, 'engine': 'duckdb', 'query': nome, 'formato': fmt,
            'runs': runs, 'median_s': round(mediana, 4), 'median_engine_s': '',
            'data_scanned_mb': '', 'n_rows': n}


def linha_athena(athena, database, ds, nome, fmt, sql, runs):
    """Corre uma query no Athena e devolve a linha para o CSV e os bytes lidos por corrida."""
    try:
        r = bench_athena(athena, sql, database, runs)
    except AthenaError as erro:
        sys.exit(f'[cloud_benchmark] ERRO no Athena ({nome}, {fmt}): {erro}')
    print(f"  athena  {nome:30} {fmt:13} {r['median_s'] * 1000:9.1f} ms  {r['n_rows']:>8,} linhas"
          f"  {r['scanned_bytes'] / 1e6:9.2f} MB lidos")
    linha = {'run_at': now(), 'dataset': ds, 'engine': 'athena', 'query': nome, 'formato': fmt,
             'runs': runs, 'median_s': round(r['median_s'], 4),
             'median_engine_s': round(r['median_engine_s'], 4),
             'data_scanned_mb': round(r['scanned_bytes'] / 1e6, 2), 'n_rows': r['n_rows']}
    return linha, r['scanned_bytes']


def motores_diferentes(n_linhas):
    """Pares (query, formato) que correram nos dois motores com n.º de linhas diferente.

    Os valores podem diferir (a mediana da 03 é aproximada no Athena), mas o n.º de linhas não.
    """
    diferentes = []
    for (q, f, motor) in n_linhas:
        if motor != 'duckdb' or (q, f, 'athena') not in n_linhas:
            continue
        if n_linhas[(q, f, 'duckdb')] != n_linhas[(q, f, 'athena')]:
            diferentes.append((q, f))
    return diferentes


def main():
    """Corre cada query em cada motor e formato e regista os resultados em results/cloud_benchmarks.csv."""
    args = parse_args()
    cfg = load_config(args.dataset)
    ds = cfg['dataset']
    aws = aws_settings(cfg, args)
    cloud_dir = ROOT / 'data' / 'cloud' / aws['pasta']
    usar_athena = 'athena' in args.engines and not args.dry_run
    print(f"[cloud_benchmark] dataset={ds} motores={' '.join(args.engines)} corridas={args.runs}"
          f"{' (dry-run: Athena não é contactado)' if args.dry_run else ''}")

    if not cloud_dir.exists():
        sys.exit(f'Erro: não existe {cloud_dir.relative_to(ROOT)}. '
                 f'Corre primeiro: python scripts/05_prepare_cloud.py --dataset {ds}')
    if usar_athena:
        resolve_buckets(aws)
        athena = Athena(aws)

    queries = load_queries()
    fontes_duckdb = duckdb_sources(cloud_dir)
    csv_resultados = cfg['paths']['results'] / 'cloud_benchmarks.csv'
    n_linhas = {}          # (query, formato, motor) -> n.º de linhas, para comparar os motores
    linhas_csv = []        # só são escritas no fim, se os dois motores concordarem
    bytes_athena = 0

    # Para cada query e cada formato: primeiro o DuckDB (local) e depois o Athena (S3)
    for nome, athena_file, texto_duckdb, formatos in queries:
        for fmt in formatos:
            if 'duckdb' in args.engines and not args.dry_run:
                sql = Template(texto_duckdb).substitute(fontes_duckdb[fmt])
                linha = linha_duckdb(ds, nome, fmt, sql, args.runs)
                n_linhas[(nome, fmt, 'duckdb')] = linha['n_rows']
                linhas_csv.append(linha)

            if 'athena' in args.engines:
                sql = read_sql(athena_file, ATHENA_SOURCES[fmt])
                if args.dry_run:
                    print(f'\n-- athena {nome} [{fmt}]\n{sql};')
                    continue
                linha, scanned_bytes = linha_athena(athena, aws['database'], ds, nome, fmt, sql, args.runs)
                # O Athena cobra no mínimo 10 MB por query, mesmo que leia menos
                bytes_athena += max(scanned_bytes, MINIMO_COBRADO) * args.runs
                n_linhas[(nome, fmt, 'athena')] = linha['n_rows']
                linhas_csv.append(linha)

    diferentes = motores_diferentes(n_linhas)
    if usar_athena:
        print(f'[cloud_benchmark] Athena: {bytes_athena / 1e9:.2f} GB cobrados no total, '
              f'custo estimado {bytes_athena / 1e12 * USD_POR_TB:.4f} USD')

    if diferentes:
        print('[cloud_benchmark] ERRO: n.º de linhas diferente entre os motores; '
              f'esta corrida NÃO foi escrita em {csv_resultados.relative_to(ROOT)}:', file=sys.stderr)
        for q, f in diferentes:
            print(f'  - {q} [{f}]: {n_linhas[(q, f, "duckdb")]} linhas no DuckDB, '
                  f'{n_linhas[(q, f, "athena")]} no Athena', file=sys.stderr)
        sys.exit(1)

    for linha in linhas_csv:
        append_row(csv_resultados, linha)
    if linhas_csv:
        print(f'[cloud_benchmark] {len(linhas_csv)} linhas escritas em {csv_resultados.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
