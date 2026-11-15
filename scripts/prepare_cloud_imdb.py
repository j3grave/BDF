"""
prepare_cloud_imdb.py - Fase 3: preparar localmente os ficheiros do IMDb que vão para o S3.

Objetivo:
    Criar em data/cloud/imdb/ um espelho exato do que vai para s3://<bucket-dados>/imdb/, para
    o Athena comparar os bytes lidos em TSV comprimido e em Parquet. O IMDb é o mesmo para os
    três datasets do MovieLens, por isso tem uma pasta própria (e não uma por dataset).
    Uma pasta por tabela, como no prepare_cloud.py:
        title_ratings/title_ratings.parquet       Parquet zstd (tipos do 07_imdb.py)
        title_basics/title_basics.parquet         idem
        title_ratings_tsv/title.ratings.tsv.gz     cópia byte a byte do ficheiro do IMDb
        title_basics_tsv/title.basics.tsv.gz       idem
    Este script não faz nenhuma chamada à AWS.

Entradas:
    data/imdb/parquet/*.parquet e data/imdb/raw/*.tsv.gz (criados pelo 07_imdb.py)

Saídas:
    data/cloud/imdb/ (apagada e recriada em cada execução)
    reports/cloud_manifest_imdb.md (só se as verificações passarem)

Como correr:
    python scripts/prepare_cloud_imdb.py
    (o passo cloud corre-o sozinho quando existe data/imdb/parquet/)
"""
import shutil
import sys
import time

import duckdb

from common import ROOT, now, size_on_disk

RAW = ROOT / 'data' / 'imdb' / 'raw'
PARQUET = ROOT / 'data' / 'imdb' / 'parquet'
DESTINO = ROOT / 'data' / 'cloud' / 'imdb'
MANIFESTO = ROOT / 'reports' / 'cloud_manifest_imdb.md'

# tabela -> ficheiro original do IMDb
TABELAS = {'title_ratings': 'title.ratings.tsv.gz', 'title_basics': 'title.basics.tsv.gz'}


def contar_tsv(con, caminho):
    """N.º de linhas de um TSV do IMDb (sem o cabeçalho), lido como no 07_imdb.py."""
    return con.execute(f"""SELECT COUNT(*) FROM read_csv('{caminho.as_posix()}', delim='\\t', header=true,
                                                      quote='', escape='', nullstr='\\N', all_varchar=true)""").fetchone()[0]


def main():
    """Copia o Parquet (em zstd) e o TSV.gz para data/cloud/imdb/, verifica e escreve o manifesto."""
    for tabela, ficheiro in TABELAS.items():
        if not (PARQUET / f'{tabela}.parquet').exists() or not (RAW / ficheiro).exists():
            sys.exit('Erro: falta o IMDb em data/imdb/. Corre primeiro: '
                     'python run_pipeline.py --dataset small --steps imdb')

    # Idempotência: apaga e recria a pasta, e só escreve o manifesto no fim, se tudo estiver certo
    if MANIFESTO.exists():
        MANIFESTO.unlink()
    if DESTINO.exists():
        shutil.rmtree(DESTINO)
    t0 = time.perf_counter()
    con = duckdb.connect()
    con.execute('SET preserve_insertion_order = false')

    linhas_manifesto = []
    problemas = []
    for tabela, ficheiro in TABELAS.items():
        # Parquet: reescrito em zstd, como as tabelas do MovieLens na fase 2 (SELECT * mantém os tipos)
        pq_origem = PARQUET / f'{tabela}.parquet'
        pq_destino = DESTINO / tabela / f'{tabela}.parquet'
        pq_destino.parent.mkdir(parents=True)
        con.execute(f"""COPY (SELECT * FROM read_parquet('{pq_origem.as_posix()}'))
                        TO '{pq_destino.as_posix()}' (FORMAT parquet, COMPRESSION zstd)""")

        # TSV comprimido: cópia byte a byte (o Athena lê .gz diretamente)
        tsv_destino = DESTINO / f'{tabela}_tsv' / ficheiro
        tsv_destino.parent.mkdir(parents=True)
        shutil.copyfile(RAW / ficheiro, tsv_destino)

        # Verificações: o mesmo n.º de linhas nas três versões
        n_origem = con.execute(f"SELECT COUNT(*) FROM read_parquet('{pq_origem.as_posix()}')").fetchone()[0]
        n_pq = con.execute(f"SELECT COUNT(*) FROM read_parquet('{pq_destino.as_posix()}')").fetchone()[0]
        n_tsv = contar_tsv(con, tsv_destino)
        if not (n_origem == n_pq == n_tsv):
            problemas.append(f'{tabela}: {n_origem} linhas na origem, {n_pq} no Parquet zstd, {n_tsv} no TSV')
        mb_pq, mb_tsv = size_on_disk(pq_destino) / 1e6, size_on_disk(tsv_destino) / 1e6
        print(f'  {tabela:14} {n_pq:>12,} linhas  Parquet zstd {mb_pq:8.1f} MB  TSV.gz {mb_tsv:8.1f} MB'.replace(',', ' '))
        linhas_manifesto.append(f'| {tabela} | `imdb/{tabela}/` | {mb_pq:.1f} | `imdb/{tabela}_tsv/` | {mb_tsv:.1f} | {n_pq:,} |'
                                .replace(',', ' '))
    con.close()

    if problemas:
        print('[prepare_cloud_imdb] ERRO: as verificações falharam; o manifesto não foi gerado.', file=sys.stderr)
        for p in problemas:
            print(f'  - {p}', file=sys.stderr)
        sys.exit(1)

    texto = ['# Manifesto para a cloud: imdb', '',
             f'- Gerado em: {now()} (DuckDB {duckdb.__version__}, {time.perf_counter() - t0:.1f} s)',
             '- Pasta local: `data/cloud/imdb/` -> `s3://<bucket-dados>/imdb/` (a mesma para os três datasets)',
             '- Verificações: o mesmo n.º de linhas na origem, no Parquet zstd e no TSV.gz. Todas passaram.', '',
             '| Tabela | Parquet (zstd) | MB | TSV comprimido (gzip) | MB | Linhas |', '|---|---|---:|---|---:|---:|']
    texto += linhas_manifesto
    texto += ['', 'No Athena, as tabelas `imdb_title_ratings_tsv` e `imdb_title_basics_tsv` leem o TSV.gz '
              '(`\\N` = nulo, `skip.header.line.count` = 1) e as tabelas sem `_tsv` leem o Parquet.']
    MANIFESTO.write_text('\n'.join(texto) + '\n', encoding='utf-8')
    print(f'[prepare_cloud_imdb] verificações OK; manifesto em {MANIFESTO.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
