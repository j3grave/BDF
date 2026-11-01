"""Descarrega o dataset MovieLens escolhido e normaliza-o para CSV com o esquema comum.

Resultado: data/<dataset>/csv/{ratings,movies[,tags,links]}.csv com cabeçalho, em UTF-8.
- small e 32m já vêm em CSV com este esquema: são só extraídos.
- 1m vem em .dat (separador '::', sem cabeçalho, movies.dat em latin-1): é convertido com DuckDB.
"""
import shutil
import urllib.request
import zipfile

import duckdb

from common import SCHEMAS, load_config, parse_args

DAT_ENCODING = {'ratings': 'utf-8', 'movies': 'latin-1'}


def download(url, dest):
    if dest.exists():
        print(f'  já existe, não descarrega: {dest.name}')
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + '.part')   # um download interrompido não conta como feito
    print(f'  a descarregar {url}')
    with urllib.request.urlopen(url) as r, tmp.open('wb') as f:
        shutil.copyfileobj(r, f, length=1 << 20)
    tmp.rename(dest)
    print(f'  {dest.stat().st_size / 1e6:.1f} MB')


def extract(zip_path, raw_dir, folder):
    target = raw_dir / folder
    if target.exists():
        print(f'  já extraído: {target.name}/')
        return target
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(raw_dir)
    return target


def normalize_csv(src, csv_dir):
    # Move em vez de copiar: no 32m o ratings.csv tem ~0.9 GB
    for table in SCHEMAS:
        f = src / f'{table}.csv'
        if f.exists():
            shutil.move(f, csv_dir / f.name)


def normalize_dat(src, csv_dir):
    for table, encoding in DAT_ENCODING.items():
        columns = SCHEMAS[table]
        duckdb.execute(f"""
            COPY (SELECT * FROM read_csv('{(src / f'{table}.dat').as_posix()}',
                                         delim='::', header=false, quote='', escape='',
                                         encoding='{encoding}', columns={columns}))
            TO '{(csv_dir / f'{table}.csv').as_posix()}' (HEADER, DELIMITER ',')
        """)


def main():
    args = parse_args(__doc__)
    cfg = load_config(args.dataset)
    paths, source = cfg['paths'], cfg['source']
    print(f"[ingest] dataset={cfg['dataset']}")

    zip_path = paths['raw'] / f"{source['folder']}.zip"
    download(source['url'], zip_path)
    src = extract(zip_path, paths['raw'], source['folder'])

    csv_dir = paths['csv']
    csv_dir.mkdir(parents=True, exist_ok=True)
    if source['format'] == 'dat':
        normalize_dat(src, csv_dir)
    else:
        normalize_csv(src, csv_dir)

    for f in sorted(csv_dir.glob('*.csv')):
        n = duckdb.sql(f"SELECT COUNT(*) FROM read_csv('{f.as_posix()}')").fetchone()[0]
        print(f'  {f.name:12} {n:>12,} linhas')


if __name__ == '__main__':
    main()
