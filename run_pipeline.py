"""
run_pipeline.py - Ponto de entrada do pipeline local MovieLens (BDF 2026).

Objetivo:
    Correr, por ordem, os passos do pipeline para um dataset, cada um no seu script:
        ingest     scripts/01_ingest.py      descarregar e normalizar para CSV
        parquet    scripts/02_to_parquet.py  converter para Parquet (sem partição e por ano)
        benchmark  scripts/03_benchmark.py   medir o tempo das queries de sql/
        eda        scripts/04_eda.py         análise exploratória (figuras e relatório)

Entradas:
    config.yaml e a opção --dataset (small | 1m | 32m).

Saídas:
    As de cada passo (ver o cabeçalho de cada script), mais
    results/pipeline_runs.csv   tempo de cada passo (acrescenta linhas)

Como correr:
    python run_pipeline.py --dataset small                       todos os passos
    python run_pipeline.py --dataset 1m --steps ingest parquet   só alguns passos
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

# Versão mínima de Python: o polars>=1.37 do requirements.txt não instala abaixo do 3.10.
# Verificamos já aqui, antes de importar o resto, para o erro ser claro em vez de um
# ImportError ou SyntaxError difícil de perceber mais à frente.
PYTHON_MINIMO = (3, 10)
if sys.version_info < PYTHON_MINIMO:
    sys.exit(f'Erro: este pipeline requer Python {PYTHON_MINIMO[0]}.{PYTHON_MINIMO[1]} ou superior, '
             f'mas está a correr com Python {sys.version.split()[0]} ({sys.executable}).\n'
             'Cria o ambiente com uma versão mais recente, por exemplo "python3.12 -m venv .venv", '
             'e vê a secção "Ambiente" do README.')

# O common.py está na pasta scripts/. Acrescentamo-la à lista de pastas onde o Python
# procura módulos, para o "from common import ..." funcionar a partir da raiz.
sys.path.insert(0, str(Path(__file__).resolve().parent / 'scripts'))
from common import DATASETS, ROOT, append_row, load_config, now  # noqa: E402

# Passos disponíveis, pela ordem em que correm por omissão
STEPS = {
    'ingest': 'scripts/01_ingest.py',
    'parquet': 'scripts/02_to_parquet.py',
    'benchmark': 'scripts/03_benchmark.py',
    'eda': 'scripts/04_eda.py',
}


def main():
    """Lê as opções e corre cada passo pedido, registando o tempo em results/pipeline_runs.csv."""
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dataset', choices=list(DATASETS), help='sobrepõe o valor de config.yaml')
    parser.add_argument('--steps', nargs='+', choices=list(STEPS), default=list(STEPS))
    args = parser.parse_args()
    cfg = load_config(args.dataset)

    for step in args.steps:
        # Cada passo corre num processo Python separado (o mesmo Python deste script,
        # sys.executable), tal como se fosse chamado à mão no terminal.
        # check=True faz o pipeline parar se um passo falhar, em vez de continuar com dados incompletos.
        comando = [sys.executable, str(ROOT / STEPS[step]), '--dataset', cfg['dataset']]
        t0 = time.perf_counter()
        subprocess.run(comando, check=True)
        seconds = round(time.perf_counter() - t0, 2)

        append_row(cfg['paths']['results'] / 'pipeline_runs.csv',
                   {'run_at': now(), 'dataset': cfg['dataset'], 'step': step, 'seconds': seconds})
        # flush=True escreve já no ecrã, para a linha não aparecer fora de ordem
        # em relação ao que o passo imprimiu. É o tempo total do processo (arranque do
        # Python, imports e trabalho), o mesmo que fica em pipeline_runs.csv.
        print(f'[{step}] tempo total do passo (processo completo): {seconds:.2f} s\n', flush=True)


if __name__ == '__main__':
    main()
