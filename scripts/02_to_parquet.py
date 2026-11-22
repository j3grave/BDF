"""
02_to_parquet.py - Passo 2 do pipeline: converter os CSV em Parquet

Objetivo:
    Passar as tabelas CSV (texto, linha a linha) para Parquet (binário, coluna a
    coluna, comprimido) e criar uma segunda versão dos ratings particionada por ano, é a tabela com maior volume de dados e só faria sentido um particionamento por ano.
    As duas versões servem para comparar, no passo 3 - benchmark, o efeito das partições.
    A conversão é feita com o COPY do DuckDB, em streaming: dados não passampelo pandas nem precisam de caber todos na memória.

Entradas:
    data/<dataset>/csv/*.csv (criados pelo 01_ingest.py)

Saídas:
    data/<dataset>/parquet/<tabela>.parquet   uma por tabela, sem partição
    data/<dataset>/parquet/ratings_by_year/   ratings particionado: year=1996/, year=1997/, etc - (ano calculado a partir do timestamp, em UTC)
    results/sizes.csv                         tamanho do CSV, do Parquet e do Parquet por ano, e o tempo de cada conversão (acrescenta linhas)

"""
import shutil
import time

import duckdb

from common import SCHEMAS, append_row, duckdb_columns, load_config, now, parse_args, size_on_disk


def converter_tabela(con, ds, table, schema, csv_file, pq_file):
    """CSV -> Parquet sem partição. Devolve a linha para o results/sizes.csv."""
    # Aspas duplicadas "" dentro dos títulos (CSV standard) e tipos fixos, iguais nos três datasets
    t0 = time.perf_counter()
    con.execute(f"""
        COPY (SELECT * FROM read_csv('{csv_file.as_posix()}', header=true, delim=',',
                                      quote='"', escape='"', columns={duckdb_columns(schema)}))
        TO '{pq_file.as_posix()}' (FORMAT parquet)
    """)
    # As colunas "by_year" só são preenchidas para os ratings (ver particionar_ratings)
    return {
        'run_at': now(),
        'dataset': ds,
        'table': table,
        'csv_mb': round(size_on_disk(csv_file) / 1e6, 2),
        'parquet_mb': round(size_on_disk(pq_file) / 1e6, 2),
        'parquet_by_year_mb': '',
        'n_partitions': '',
        'seconds': round(time.perf_counter() - t0, 3),
        'seconds_by_year': '',
    }


def particionar_ratings(con, pq_file, part_dir, row):
    """Parquet -> Parquet particionado por ano (year=2015/...) e preenche as colunas by_year de row.

    Uma query que filtre ou agrupe por ano lê só as pastas de que precisa (partition pruning).
    """
    # O COPY particionado não substitui pastas que já existem
    if part_dir.exists():
        shutil.rmtree(part_dir)
    # epoch_ms devolve TIMESTAMP sem fuso horário (UTC), por isso o ano não depende da máquina
    t0 = time.perf_counter()
    con.execute(f"""
        COPY (SELECT *, year(epoch_ms(timestamp * 1000)) AS year
              FROM read_parquet('{pq_file.as_posix()}'))
        TO '{part_dir.as_posix()}' (FORMAT parquet, PARTITION_BY (year))
    """)
    row['seconds_by_year'] = round(time.perf_counter() - t0, 3)
    row['parquet_by_year_mb'] = round(size_on_disk(part_dir) / 1e6, 2)
    row['n_partitions'] = len(list(part_dir.glob('year=*')))


def main():
    """Converte cada CSV em Parquet, particiona os ratings por ano e regista tamanhos e tempos."""
    args = parse_args(__doc__)
    cfg = load_config(args.dataset)
    ds = cfg['dataset']
    pq_dir = cfg['paths']['parquet']
    pq_dir.mkdir(parents=True, exist_ok=True)
    print(f'[to_parquet] dataset={ds}')

    con = duckdb.connect()
    # A ordem das linhas não interessa aqui, e desligar poupa memória quando corre o 32M
    con.execute('SET preserve_insertion_order = false')

    for table, schema in SCHEMAS.items():
        csv_file = cfg['paths']['csv'] / f'{table}.csv'
        if not csv_file.exists():
            continue   # o 1M não tem tags nem links
        pq_file = pq_dir / f'{table}.parquet'

        row = converter_tabela(con, ds, table, schema, csv_file, pq_file)
        mensagem = (f"  {table:8} CSV {row['csv_mb']:>9.2f} MB -> Parquet {row['parquet_mb']:>8.2f} MB"
                    f" em {row['seconds']:.2f} s")
        if table == 'ratings':
            particionar_ratings(con, pq_file, pq_dir / 'ratings_by_year', row)
            mensagem += (f" | por ano {row['parquet_by_year_mb']:.2f} MB em {row['n_partitions']} partições,"
                         f" {row['seconds_by_year']:.2f} s")
        append_row(cfg['paths']['results'] / 'sizes.csv', row)
        print(mensagem)


if __name__ == '__main__':
    main()
