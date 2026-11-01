"""
01_ingest.py - Passo 1 do pipeline: descarregar e normalizar o MovieLens.

Objetivo:
    Descarregar o dataset escolhido do site do GroupLens e deixar as tabelas todas
    no mesmo formato (CSV com cabeçalho, UTF-8, mesmas colunas), seja qual for o
    tamanho do dataset. Os passos seguintes podem então tratar os três da mesma forma.
    - small e 32m já vêm em CSV com este esquema: os ficheiros são só extraídos.
    - 1m vem em .dat (separador '::', sem cabeçalho, movies.dat em latin-1):
      é convertido para CSV com o DuckDB.

Entradas:
    O zip do GroupLens (descarregado só se ainda não existir em data/<dataset>/raw/).

Saídas:
    data/<dataset>/raw/                     zip e ficheiros originais
    data/<dataset>/csv/ratings.csv          userId, movieId, rating, timestamp
    data/<dataset>/csv/movies.csv           movieId, title, genres
    data/<dataset>/csv/tags.csv, links.csv  quando o dataset os tiver (small e 32m)

Como correr:
    python scripts/01_ingest.py --dataset small
    (ou, para todos os passos: python run_pipeline.py --dataset small)
"""
import shutil
import urllib.request
import zipfile

import duckdb

from common import SCHEMAS, duckdb_columns, load_config, parse_args

# Codificação de cada ficheiro .dat do 1M: o movies.dat tem títulos com acentos em latin-1
DAT_ENCODING = {'ratings': 'utf-8', 'movies': 'latin-1'}


def download(url, dest):
    """Descarrega url para dest, a não ser que dest já exista."""
    if dest.exists():
        print(f'  já existe, não descarrega: {dest.name}')
        return
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Escreve primeiro num ficheiro .part e só no fim lhe dá o nome final.
    # Se o download for interrompido, fica só o .part e a próxima execução volta a descarregar.
    tmp = dest.with_suffix(dest.suffix + '.part')
    print(f'  a descarregar {url}')
    with urllib.request.urlopen(url) as resposta:
        with tmp.open('wb') as f:
            # Copia em blocos de 1 MB, sem carregar o zip inteiro (239 MB no 32M) para a memória
            shutil.copyfileobj(resposta, f, length=1024 * 1024)
    tmp.rename(dest)
    print(f'  {dest.stat().st_size / 1e6:.1f} MB')


def extract(zip_path, raw_dir, folder):
    """Extrai o zip para raw_dir, a não ser que a pasta extraída já exista. Devolve essa pasta."""
    target = raw_dir / folder
    if target.exists():
        print(f'  já extraído: {target.name}/')
        return target
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(raw_dir)
    return target


def normalize_csv(src, csv_dir):
    """small e 32m: os CSV já têm o esquema certo, basta passá-los para a pasta csv/."""
    # Move em vez de copiar: no 32m o ratings.csv tem ~0.9 GB e uma cópia duplicaria o espaço
    for table in SCHEMAS:
        f = src / f'{table}.csv'
        if f.exists():
            shutil.move(f, csv_dir / f.name)


def normalize_dat(src, csv_dir):
    """1m: converte ratings.dat e movies.dat para CSV com cabeçalho, usando o DuckDB."""
    for table, encoding in DAT_ENCODING.items():
        dat_file = (src / f'{table}.dat').as_posix()
        csv_file = (csv_dir / f'{table}.csv').as_posix()
        columns = duckdb_columns(SCHEMAS[table])

        # O DuckDB lê e escreve em streaming, sem passar pelo pandas.
        # - delim='::'             separador do formato .dat
        # - header=false + columns  o ficheiro não tem cabeçalho, por isso damos os nomes e tipos
        # - quote='' e escape=''    os títulos podem ter aspas, que aqui não delimitam campos
        # - encoding                latin-1 no movies.dat, para os acentos saírem corretos
        duckdb.execute(f"""
            COPY (SELECT * FROM read_csv('{dat_file}',
                                         delim='::', header=false, quote='', escape='',
                                         encoding='{encoding}', columns={columns}))
            TO '{csv_file}' (HEADER, DELIMITER ',')
        """)


def main():
    """Descarrega, extrai, normaliza e mostra o n.º de linhas de cada CSV."""
    args = parse_args(__doc__)
    cfg = load_config(args.dataset)
    paths = cfg['paths']
    source = cfg['source']
    print(f"[ingest] dataset={cfg['dataset']}")

    # 1. Obter os ficheiros originais (cada fase é saltada se já tiver sido feita)
    zip_path = paths['raw'] / f"{source['folder']}.zip"
    download(source['url'], zip_path)
    src = extract(zip_path, paths['raw'], source['folder'])

    # 2. Normalizar para CSV com o esquema comum
    csv_dir = paths['csv']
    csv_dir.mkdir(parents=True, exist_ok=True)
    if source['format'] == 'dat':
        normalize_dat(src, csv_dir)
    else:
        normalize_csv(src, csv_dir)

    # 3. Verificação rápida: n.º de linhas de cada CSV (comparar com os valores oficiais do GroupLens)
    for f in sorted(csv_dir.glob('*.csv')):
        n = duckdb.execute(f"SELECT COUNT(*) FROM read_csv('{f.as_posix()}')").fetchone()[0]
        print(f'  {f.name:12} {n:>12,} linhas')


if __name__ == '__main__':
    main()
