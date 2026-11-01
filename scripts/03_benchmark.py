"""Corre as queries de sql/ sobre o Parquet sem partição e sobre o particionado por ano.

Cada query corre 3 vezes por formato; a mediana do tempo e o n.º de linhas são acrescentados a
results/benchmarks.csv. Nos ficheiros .sql, ${ratings} e ${movies} são substituídos pela leitura
do Parquet correspondente. Ficheiros só com comentários (ex.: 10_flag_bots.sql) são ignorados.
"""
import statistics
import time
from string import Template

import duckdb

from common import ROOT, append_row, load_config, now, parse_args

RUNS = 3


def sources(pq_dir):
    flat = (pq_dir / 'ratings.parquet').as_posix()
    by_year = (pq_dir / 'ratings_by_year' / '*' / '*.parquet').as_posix()
    movies = f"read_parquet('{(pq_dir / 'movies.parquet').as_posix()}')"
    return {
        # Nos dois formatos ${ratings} tem as mesmas colunas, incluindo year
        'parquet': {'ratings': f"(SELECT *, year(epoch_ms(timestamp * 1000)) AS year "
                               f"FROM read_parquet('{flat}'))",
                    'movies': movies},
        'parquet_by_year': {'ratings': f"read_parquet('{by_year}', hive_partitioning=true)",
                            'movies': movies},
    }


def has_sql(text):
    return any(line.strip() and not line.strip().startswith('--') for line in text.splitlines())


def main():
    args = parse_args(__doc__)
    cfg = load_config(args.dataset)
    ds = cfg['dataset']
    print(f'[benchmark] dataset={ds}')

    for sql_file in sorted((ROOT / 'sql').glob('*.sql')):
        text = sql_file.read_text()
        if not has_sql(text):
            print(f'  {sql_file.name:32} ignorado (só comentários)')
            continue
        for fmt, params in sources(cfg['paths']['parquet']).items():
            query = Template(text).substitute(params)
            times = []
            for _ in range(RUNS):
                con = duckdb.connect()   # ligação nova em cada corrida, sem cache de resultados
                t0 = time.perf_counter()
                n_rows = len(con.execute(query).fetchall())
                times.append(time.perf_counter() - t0)
                con.close()
            median = statistics.median(times)
            append_row(cfg['paths']['results'] / 'benchmarks.csv',
                       {'run_at': now(), 'dataset': ds, 'query': sql_file.stem, 'formato': fmt,
                        'median_s': round(median, 4), 'n_rows': n_rows})
            print(f'  {sql_file.stem:32} {fmt:16} {median * 1000:9.1f} ms  {n_rows:>8,} linhas')


if __name__ == '__main__':
    main()
