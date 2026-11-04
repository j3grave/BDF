"""
common.py - Configuração e funções partilhadas pelos scripts do pipeline.

Objetivo:
    Reunir num só sítio o que todos os passos usam: a lista de datasets, o esquema
    das tabelas, a leitura do config.yaml, os caminhos das pastas e a escrita dos
    CSV de resultados. Assim, cada script só tem a lógica do seu próprio passo.

Entradas:
    config.yaml (na raiz do projeto).

Saídas:
    Nenhuma diretamente; é importado pelos outros scripts com `from common import ...`.

Como correr:
    Não se corre sozinho. Os scripts de scripts/ e o run_pipeline.py importam-no.
"""
import argparse
import csv
from datetime import datetime
from pathlib import Path

import yaml

# Raiz do projeto: a pasta acima de scripts/. Todos os caminhos partem daqui,
# por isso os scripts funcionam seja qual for a pasta onde são chamados.
ROOT = Path(__file__).resolve().parent.parent

# Os três tamanhos do MovieLens: de onde se descarregam, o nome da pasta dentro
# do zip e o formato dos ficheiros (o 1M é o único que vem em .dat).
DATASETS = {
    'small': {'url': 'https://files.grouplens.org/datasets/movielens/ml-latest-small.zip',
              'folder': 'ml-latest-small', 'format': 'csv'},
    '1m':    {'url': 'https://files.grouplens.org/datasets/movielens/ml-1m.zip',
              'folder': 'ml-1m', 'format': 'dat'},
    '32m':   {'url': 'https://files.grouplens.org/datasets/movielens/ml-32m.zip',
              'folder': 'ml-32m', 'format': 'csv'},
}

# Esquema comum aos três datasets: nome e tipo de cada coluna.
# Fixar os tipos (em vez de deixar o DuckDB adivinhá-los) garante que o Parquet
# do small, do 1M e do 32M tem exatamente as mesmas colunas e tipos.
SCHEMAS = {
    'ratings': {'userId': 'INTEGER', 'movieId': 'INTEGER', 'rating': 'DOUBLE', 'timestamp': 'BIGINT'},
    'movies':  {'movieId': 'INTEGER', 'title': 'VARCHAR', 'genres': 'VARCHAR'},
    'tags':    {'userId': 'INTEGER', 'movieId': 'INTEGER', 'tag': 'VARCHAR', 'timestamp': 'BIGINT'},
    'links':   {'movieId': 'INTEGER', 'imdbId': 'VARCHAR', 'tmdbId': 'INTEGER'},
}


def load_config(dataset=None):
    """Lê o config.yaml, aplica o --dataset (se vier) e acrescenta os caminhos das pastas."""
    cfg = yaml.safe_load((ROOT / 'config.yaml').read_text())

    # O --dataset da linha de comandos tem prioridade sobre o valor do config.yaml
    if dataset:
        cfg['dataset'] = dataset
    if cfg['dataset'] not in DATASETS:
        nomes_validos = ', '.join(DATASETS)
        raise SystemExit(f"dataset inválido: {cfg['dataset']} (usar: {nomes_validos})")

    # Cada dataset tem a sua pasta em data/<dataset>/, com uma subpasta por fase
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
    """Lê a opção --dataset da linha de comandos (comum a todos os scripts)."""
    # RawDescriptionHelpFormatter mostra o cabeçalho do script no --help tal como está escrito
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dataset', choices=list(DATASETS), help='sobrepõe o valor de config.yaml')
    return parser.parse_args()


def duckdb_columns(schema):
    """Escreve o esquema no formato que o read_csv do DuckDB aceita: {'col': 'TIPO', ...}."""
    partes = []
    for coluna, tipo in schema.items():
        partes.append(f"'{coluna}': '{tipo}'")
    return '{' + ', '.join(partes) + '}'


def size_on_disk(path):
    """Tamanho em bytes de um ficheiro, ou da soma de todos os ficheiros de uma pasta."""
    path = Path(path)
    if path.is_file():
        return path.stat().st_size

    # Uma pasta (ex.: o Parquet particionado) pode ter subpastas: percorre-as todas
    total = 0
    for f in path.rglob('*'):
        if f.is_file():
            total += f.stat().st_size
    return total


def append_row(csv_path, row):
    """Acrescenta uma linha (dicionário) a um CSV de resultados, criando o cabeçalho se for novo.

    Se o ficheiro existir com outras colunas, é reescrito com as colunas novas (vazias nas linhas antigas).
    """
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    # Quando um script passa a registar uma coluna nova, o CSV antigo tem outro cabeçalho.
    # Em vez de escrever linhas desalinhadas, reescrevemos o ficheiro com as colunas atualizadas.
    if csv_path.exists():
        with csv_path.open(newline='') as f:
            reader = csv.DictReader(f)
            old_fields = reader.fieldnames or []
            old_rows = list(reader)

        if old_fields != list(row):
            # Colunas novas primeiro; colunas antigas que já não existem vão para o fim
            fields = list(row)
            for coluna in old_fields:
                if coluna not in row:
                    fields.append(coluna)

            with csv_path.open('w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fields, restval='')
                writer.writeheader()
                writer.writerows(old_rows)

            # A linha nova também tem de ter todas as colunas, pela mesma ordem
            linha_completa = {}
            for coluna in fields:
                linha_completa[coluna] = row.get(coluna, '')
            row = linha_completa

    # Abrir em modo 'a' (append) acrescenta no fim, sem apagar as execuções anteriores
    new = not csv_path.exists()
    with csv_path.open('a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(row))
        if new:
            writer.writeheader()
        writer.writerow(row)


def now():
    """Data e hora atuais, ao segundo (ex.: 2026-11-01T17:46:55), para a coluna run_at."""
    return datetime.now().isoformat(timespec='seconds')
