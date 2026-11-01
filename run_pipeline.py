"""Ponto de entrada do pipeline local.

    python run_pipeline.py --dataset small
    python run_pipeline.py --dataset 1m --steps ingest parquet

Cada passo corre o script correspondente em scripts/ e o tempo é registado em results/pipeline_runs.csv.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'scripts'))
from common import DATASETS, ROOT, append_row, load_config, now  # noqa: E402

STEPS = {
    'ingest': 'scripts/01_ingest.py',
    'parquet': 'scripts/02_to_parquet.py',
    'benchmark': 'scripts/03_benchmark.py',
    'eda': 'scripts/04_eda.py',
}


def main():
    parser = argparse.ArgumentParser(description='Pipeline local MovieLens (BDF 2026)')
    parser.add_argument('--dataset', choices=list(DATASETS), help='sobrepõe o valor de config.yaml')
    parser.add_argument('--steps', nargs='+', choices=list(STEPS), default=list(STEPS))
    args = parser.parse_args()
    cfg = load_config(args.dataset)

    for step in args.steps:
        t0 = time.perf_counter()
        subprocess.run([sys.executable, str(ROOT / STEPS[step]), '--dataset', cfg['dataset']], check=True)
        seconds = round(time.perf_counter() - t0, 2)
        append_row(cfg['paths']['results'] / 'pipeline_runs.csv',
                   {'run_at': now(), 'dataset': cfg['dataset'], 'step': step, 'seconds': seconds})
        print(f'[{step}] {seconds:.2f} s\n', flush=True)


if __name__ == '__main__':
    main()
