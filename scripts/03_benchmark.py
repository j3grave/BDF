"""
03_benchmark.py - Passo 3 do pipeline: medir o tempo das queries nos dois formatos de Parquet.

Objetivo:
    Correr cada query de sql/ sobre o Parquet sem partição e sobre o Parquet
    particionado por ano, e registar quanto tempo demora. Assim vemos em que
    queries as partições ajudam (as que filtram ou agrupam por ano) e em quais
    não fazem diferença.
    Cada query corre 3 vezes por formato e guarda-se a mediana, que é menos
    sensível do que a média a uma corrida invulgarmente lenta.

Entradas:
    sql/*.sql                        queries com os marcadores ${ratings} e ${movies}
    data/<dataset>/parquet/          criado pelo 02_to_parquet.py

Saídas:
    results/benchmarks.csv           dataset, query, formato, mediana do tempo (s), n.º de linhas
                                     (acrescenta linhas a cada execução)

Como correr:
    python scripts/03_benchmark.py --dataset small
    (ou, para todos os passos: python run_pipeline.py --dataset small)

Notas:
    Ficheiros .sql só com comentários (ex.: 10_flag_bots.sql, ainda por escrever) são ignorados.
"""
import statistics
import time
from string import Template

import duckdb

from common import ROOT, append_row, load_config, now, parse_args

RUNS = 3   # n.º de corridas por query e formato


def sources(pq_dir):
    """Texto SQL que substitui ${ratings} e ${movies} em cada um dos dois formatos."""
    flat = (pq_dir / 'ratings.parquet').as_posix()
    by_year = (pq_dir / 'ratings_by_year' / '*' / '*.parquet').as_posix()
    movies = f"read_parquet('{(pq_dir / 'movies.parquet').as_posix()}')"

    # Sem partição: o ficheiro não tem a coluna year, por isso calculamo-la a partir do timestamp.
    # Assim ${ratings} tem as mesmas colunas nos dois formatos e a mesma query serve para ambos.
    ratings_flat = f"(SELECT *, year(epoch_ms(timestamp * 1000)) AS year FROM read_parquet('{flat}'))"

    # Particionado: hive_partitioning=true transforma as pastas year=AAAA numa coluna year,
    # sem ler nada de dentro dos ficheiros.
    ratings_by_year = f"read_parquet('{by_year}', hive_partitioning=true)"

    return {
        'parquet': {'ratings': ratings_flat, 'movies': movies},
        'parquet_by_year': {'ratings': ratings_by_year, 'movies': movies},
    }


def has_sql(text):
    """True se o ficheiro tiver pelo menos uma linha que não seja comentário (--) nem vazia."""
    for line in text.splitlines():
        linha = line.strip()
        if linha and not linha.startswith('--'):
            return True
    return False


def main():
    """Corre cada query RUNS vezes em cada formato e regista a mediana e o n.º de linhas."""
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
            # Template troca ${ratings} e ${movies} pelo texto do formato atual.
            # Usa-se Template (e não .format) porque o SQL pode ter chavetas.
            query = Template(text).substitute(params)

            times = []
            for _ in range(RUNS):
                # Ligação nova em cada corrida, para que nenhuma corrida aproveite trabalho da anterior
                con = duckdb.connect()
                t0 = time.perf_counter()
                resultado = con.execute(query).fetchall()
                times.append(time.perf_counter() - t0)
                n_rows = len(resultado)
                con.close()

            median = statistics.median(times)
            append_row(cfg['paths']['results'] / 'benchmarks.csv',
                       {'run_at': now(), 'dataset': ds, 'query': sql_file.stem, 'formato': fmt,
                        'median_s': round(median, 4), 'n_rows': n_rows})
            print(f'  {sql_file.stem:32} {fmt:16} {median * 1000:9.1f} ms  {n_rows:>8,} linhas')


if __name__ == '__main__':
    main()
