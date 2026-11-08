"""
run_pipeline.py - Ponto de entrada do pipeline local MovieLens (BDF 2026).

Objetivo:
    Correr, por ordem, os passos do pipeline para um dataset, cada um no seu script:
        ingest     scripts/01_ingest.py      descarregar e normalizar para CSV
        parquet    scripts/02_to_parquet.py  converter para Parquet (sem partição e por ano)
        benchmark  scripts/03_benchmark.py   medir o tempo das queries de sql/
        eda        scripts/04_eda.py         análise exploratória (figuras e relatório)
        analises   scripts/05_analises.py    queries de análise de sql/analise/ (CSV e relatório)
    E um passo da fase 2 que só corre quando é pedido com --steps cloud (usa a AWS e tem custos):
        cloud      scripts/cloud_pipeline.py  S3 -> Glue -> Athena: upload, catálogo e benchmark

Entradas:
    config.yaml e a opção --dataset (small | 1m | 32m).
    Só para o passo cloud: --bucket-dados e --bucket-resultados (por omissão, os do config.yaml
    ou, se aí estiverem a null, os derivados do ID da conta AWS).

Saídas:
    As de cada passo (ver o cabeçalho de cada script), mais
    results/pipeline_runs.csv   tempo de cada passo (acrescenta linhas)

Como correr:
    python run_pipeline.py --dataset small                       todos os passos
    python run_pipeline.py --dataset 1m --steps ingest parquet   só alguns passos
    python run_pipeline.py --dataset small --steps cloud         fase cloud (AWS Academy Learner Lab)
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

# Passos disponíveis, pela ordem em que correm
STEPS = {
    'ingest': 'scripts/01_ingest.py',
    'parquet': 'scripts/02_to_parquet.py',
    'benchmark': 'scripts/03_benchmark.py',
    'eda': 'scripts/04_eda.py',
    'analises': 'scripts/05_analises.py',
    'cloud': 'scripts/cloud_pipeline.py',
}
# O passo cloud fica fora dos passos por omissão: usa a AWS (credenciais e custos),
# por isso só corre quando é pedido explicitamente com --steps cloud.
STEPS_OMISSAO = [step for step in STEPS if step != 'cloud']


def main():
    """Lê as opções e corre cada passo pedido, registando o tempo em results/pipeline_runs.csv."""
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dataset', choices=list(DATASETS), help='sobrepõe o valor de config.yaml')
    parser.add_argument('--steps', nargs='+', choices=list(STEPS), default=STEPS_OMISSAO,
                        help=f"por omissão: {' '.join(STEPS_OMISSAO)} (o cloud só com --steps cloud)")
    parser.add_argument('--bucket-dados', dest='bucket_dados', help='só passo cloud: bucket com data/cloud/<pasta>/')
    parser.add_argument('--bucket-resultados', dest='bucket_resultados',
                        help='só passo cloud: bucket dos resultados do Athena')
    args = parser.parse_args()
    cfg = load_config(args.dataset)

    for step in args.steps:
        # Cada passo corre num processo Python separado (o mesmo Python deste script,
        # sys.executable), tal como se fosse chamado à mão no terminal.
        # Se um passo falhar, o pipeline pára, em vez de continuar com dados incompletos.
        comando = [sys.executable, str(ROOT / STEPS[step]), '--dataset', cfg['dataset']]
        if step == 'cloud':
            if args.bucket_dados:
                comando += ['--bucket-dados', args.bucket_dados]
            if args.bucket_resultados:
                comando += ['--bucket-resultados', args.bucket_resultados]
        t0 = time.perf_counter()
        resultado = subprocess.run(comando)
        if resultado.returncode != 0:
            # Sem traceback: o passo já explicou o erro. Para o pipeline, sem registar o tempo.
            sys.exit(f'[{step}] falhou (código {resultado.returncode}); pipeline parado.')
        seconds = round(time.perf_counter() - t0, 2)

        append_row(cfg['paths']['results'] / 'pipeline_runs.csv',
                   {'run_at': now(), 'dataset': cfg['dataset'], 'step': step, 'seconds': seconds})
        # flush=True escreve já no ecrã, para a linha não aparecer fora de ordem
        # em relação ao que o passo imprimiu. É o tempo total do processo (arranque do
        # Python, imports e trabalho), o mesmo que fica em pipeline_runs.csv.
        print(f'[{step}] tempo total do passo (processo completo): {seconds:.2f} s\n', flush=True)


if __name__ == '__main__':
    main()
