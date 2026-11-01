"""Converte os CSV normalizados em Parquet com DuckDB (COPY, em streaming, sem pandas).

Resultado em data/<dataset>/parquet/:
- <tabela>.parquet       sem partição (ratings, movies e, quando existirem, tags e links)
- ratings_by_year/       ratings particionado por ano (year=AAAA/...), ano derivado do timestamp em UTC
Os tamanhos em disco e o tempo de cada conversão são acrescentados a results/sizes.csv.
"""
import shutil
import time

import duckdb

from common import SCHEMAS, append_row, load_config, now, parse_args, size_on_disk


def main():
    args = parse_args(__doc__)
    cfg = load_config(args.dataset)
    paths, ds = cfg['paths'], cfg['dataset']
    csv_dir, pq_dir = paths['csv'], paths['parquet']
    pq_dir.mkdir(parents=True, exist_ok=True)
    print(f'[to_parquet] dataset={ds}')

    con = duckdb.connect()
    con.execute('SET preserve_insertion_order = false')   # menos memória em ficheiros grandes

    for table, columns in SCHEMAS.items():
        csv_file = csv_dir / f'{table}.csv'
        if not csv_file.exists():
            continue
        pq_file = pq_dir / f'{table}.parquet'
        t0 = time.perf_counter()
        con.execute(f"""
            COPY (SELECT * FROM read_csv('{csv_file.as_posix()}', header=true, delim=',',
                                          quote='"', escape='"', columns={columns}))
            TO '{pq_file.as_posix()}' (FORMAT parquet)
        """)
        seconds = time.perf_counter() - t0
        csv_b, pq_b = size_on_disk(csv_file), size_on_disk(pq_file)
        row = {'run_at': now(), 'dataset': ds, 'table': table,
               'csv_mb': round(csv_b / 1e6, 2), 'parquet_mb': round(pq_b / 1e6, 2),
               'parquet_by_year_mb': '', 'n_partitions': '',
               'seconds': round(seconds, 3), 'seconds_by_year': ''}

        if table == 'ratings':
            part_dir = pq_dir / 'ratings_by_year'
            if part_dir.exists():
                shutil.rmtree(part_dir)
            # epoch_ms devolve TIMESTAMP sem fuso horário, por isso o ano não depende da máquina
            t0 = time.perf_counter()
            con.execute(f"""
                COPY (SELECT *, year(epoch_ms(timestamp * 1000)) AS year
                      FROM read_parquet('{pq_file.as_posix()}'))
                TO '{part_dir.as_posix()}' (FORMAT parquet, PARTITION_BY (year))
            """)
            row['seconds_by_year'] = round(time.perf_counter() - t0, 3)
            row['parquet_by_year_mb'] = round(size_on_disk(part_dir) / 1e6, 2)
            row['n_partitions'] = len(list(part_dir.glob('year=*')))

        append_row(paths['results'] / 'sizes.csv', row)
        print(f"  {table:8} CSV {row['csv_mb']:>9.2f} MB -> Parquet {row['parquet_mb']:>8.2f} MB"
              f" em {row['seconds']:.2f} s"
              + (f" | por ano {row['parquet_by_year_mb']:.2f} MB em {row['n_partitions']} partições,"
                 f" {row['seconds_by_year']:.2f} s" if table == 'ratings' else ''))


if __name__ == '__main__':
    main()
