"""Configuração e caminhos partilhados pelos scripts do pipeline."""
import argparse
import csv
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

DATASETS = {
    'small': {'url': 'https://files.grouplens.org/datasets/movielens/ml-latest-small.zip',
              'folder': 'ml-latest-small', 'format': 'csv'},
    '1m':    {'url': 'https://files.grouplens.org/datasets/movielens/ml-1m.zip',
              'folder': 'ml-1m', 'format': 'dat'},
    '32m':   {'url': 'https://files.grouplens.org/datasets/movielens/ml-32m.zip',
              'folder': 'ml-32m', 'format': 'csv'},
}

# Esquema comum aos três datasets
SCHEMAS = {
    'ratings': {'userId': 'INTEGER', 'movieId': 'INTEGER', 'rating': 'DOUBLE', 'timestamp': 'BIGINT'},
    'movies':  {'movieId': 'INTEGER', 'title': 'VARCHAR', 'genres': 'VARCHAR'},
    'tags':    {'userId': 'INTEGER', 'movieId': 'INTEGER', 'tag': 'VARCHAR', 'timestamp': 'BIGINT'},
    'links':   {'movieId': 'INTEGER', 'imdbId': 'VARCHAR', 'tmdbId': 'INTEGER'},
}


def load_config(dataset=None):
    cfg = yaml.safe_load((ROOT / 'config.yaml').read_text())
    if dataset:
        cfg['dataset'] = dataset
    if cfg['dataset'] not in DATASETS:
        raise SystemExit(f"dataset inválido: {cfg['dataset']} (usar: {', '.join(DATASETS)})")
    ds = cfg['dataset']
    base = ROOT / cfg['data_dir'] / ds
    cfg['paths'] = {
        'base': base,
        'raw': base / 'raw',            # zip e ficheiros originais
        'csv': base / 'csv',            # CSV normalizados (esquema comum)
        'parquet': base / 'parquet',
        'results': ROOT / cfg['results_dir'],
    }
    cfg['source'] = DATASETS[ds]
    return cfg


def parse_args(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--dataset', choices=list(DATASETS), help='sobrepõe o valor de config.yaml')
    return parser.parse_args()


def size_on_disk(path):
    path = Path(path)
    if path.is_file():
        return path.stat().st_size
    return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())


def append_row(csv_path, row):
    """Acrescenta uma linha a um CSV de resultados, criando o cabeçalho se for novo.

    Se o ficheiro existir com outras colunas, é reescrito com as colunas novas (vazias nas linhas antigas).
    """
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    if csv_path.exists():
        with csv_path.open(newline='') as f:
            reader = csv.DictReader(f)
            old_fields, old_rows = reader.fieldnames or [], list(reader)
        if old_fields != list(row):
            fields = list(row) + [c for c in old_fields if c not in row]
            with csv_path.open('w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fields, restval='')
                writer.writeheader()
                writer.writerows(old_rows)
            row = {c: row.get(c, '') for c in fields}
    new = not csv_path.exists()
    with csv_path.open('a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(row))
        if new:
            writer.writeheader()
        writer.writerow(row)


def now():
    return datetime.now().isoformat(timespec='seconds')
