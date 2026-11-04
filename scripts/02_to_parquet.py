"""
02_to_parquet.py - Passo 2 do pipeline: converter os CSV em Parquet.

Objetivo:
    Passar as tabelas de CSV (texto, linha a linha) para Parquet (binário, coluna a
    coluna, comprimido) e criar uma segunda versão dos ratings particionada por ano.
    As duas versões servem para comparar, no passo 3, o efeito das partições.
    A conversão é feita com o COPY do DuckDB, em streaming: os dados não passam
    pelo pandas nem precisam de caber todos na memória.

Entradas:
    data/<dataset>/csv/*.csv (criados pelo 01_ingest.py)

Saídas:
    data/<dataset>/parquet/<tabela>.parquet   uma por tabela, sem partição
    data/<dataset>/parquet/ratings_by_year/   ratings particionado: year=1996/, year=1997/, ...
                                              (ano calculado a partir do timestamp, em UTC)
    results/sizes.csv                         tamanho do CSV, do Parquet e do Parquet por ano,
                                              e o tempo de cada conversão (acrescenta linhas)

Como correr:
    python scripts/02_to_parquet.py --dataset small
    (ou, para todos os passos: python run_pipeline.py --dataset small)
"""
import shutil
import time

import duckdb

from common import SCHEMAS, append_row, duckdb_columns, load_config, now, parse_args, size_on_disk


def main():
    """Converte cada CSV em Parquet, particiona os ratings por ano e regista tamanhos e tempos."""
    args = parse_args(__doc__)
    cfg = load_config(args.dataset)
    paths = cfg['paths']
    ds = cfg['dataset']
    csv_dir = paths['csv']
    pq_dir = paths['parquet']
    pq_dir.mkdir(parents=True, exist_ok=True)
    print(f'[to_parquet] dataset={ds}')

    con = duckdb.connect()
    # Por omissão o DuckDB mantém a ordem original das linhas, o que obriga a guardar mais
    # dados em memória. A ordem não interessa aqui, e desligá-la poupa memória no 32M.
    con.execute('SET preserve_insertion_order = false')

    for table, schema in SCHEMAS.items():
        csv_file = csv_dir / f'{table}.csv'
        if not csv_file.exists():
            continue   # o 1M não tem tags nem links
        pq_file = pq_dir / f'{table}.parquet'

        # 1. CSV -> Parquet sem partição.
        # As opções de aspas indicam o CSV standard (aspas duplicadas "" dentro dos títulos)
        # e os tipos fixos garantem o mesmo esquema em todos os datasets.
        columns = duckdb_columns(schema)
        t0 = time.perf_counter()
        con.execute(f"""
            COPY (SELECT * FROM read_csv('{csv_file.as_posix()}', header=true, delim=',',
                                          quote='"', escape='"', columns={columns}))
            TO '{pq_file.as_posix()}' (FORMAT parquet)
        """)
        seconds = time.perf_counter() - t0

        # Linha para results/sizes.csv. As colunas "by_year" ficam vazias nas tabelas não particionadas.
        row = {
            'run_at': now(),
            'dataset': ds,
            'table': table,
            'csv_mb': round(size_on_disk(csv_file) / 1e6, 2),
            'parquet_mb': round(size_on_disk(pq_file) / 1e6, 2),
            'parquet_by_year_mb': '',
            'n_partitions': '',
            'seconds': round(seconds, 3),
            'seconds_by_year': '',
        }

        # 2. Só os ratings: Parquet -> Parquet particionado por ano.
        # PARTITION_BY cria uma pasta por valor de year (year=2015/...). Uma query que filtre
        # ou agrupe por ano pode então ler só as pastas de que precisa (partition pruning).
        if table == 'ratings':
            part_dir = pq_dir / 'ratings_by_year'
            # Apaga a versão anterior: o COPY particionado não substitui pastas que já existem
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

        # Resumo no ecrã
        mensagem = (f"  {table:8} CSV {row['csv_mb']:>9.2f} MB -> Parquet {row['parquet_mb']:>8.2f} MB"
                    f" em {row['seconds']:.2f} s")
        if table == 'ratings':
            mensagem += (f" | por ano {row['parquet_by_year_mb']:.2f} MB em {row['n_partitions']} partições,"
                         f" {row['seconds_by_year']:.2f} s")
        print(mensagem)


if __name__ == '__main__':
    main()
