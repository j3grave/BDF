"""
run_pipeline.py - Ponto de entrada do pipeline MovieLens (BDF 2026).

Objetivo:
    Correr, por ordem, os passos do pipeline para um dataset. Cada passo corre um ou mais
    scripts de scripts/, numerados pela ordem em que correm:
        ingest     01_ingest.py           descarregar e normalizar para CSV
        parquet    02_to_parquet.py       converter para Parquet (sem partição e por ano)
        benchmark  03_benchmark.py        medir o tempo das queries de sql/
        analise    04_analise.py          EDA, queries de sql/analise/ e, com --coordenacao,
                                          o teste de coordenação entre contas
    E o bloco cloud, que só corre quando é pedido com --steps cloud (usa a AWS e tem custos):
        cloud      05_prepare_cloud.py    ficheiros para o S3, em data/cloud/
                   06_upload_s3.py        credenciais, buckets e upload
                   07_athena_setup.py     catálogo no Glue e validação das contagens
                   08_athena_benchmark.py benchmark DuckDB vs Athena

Entradas:
    config.yaml e a opção --dataset (small | 1m | 32m).
    Só para o passo cloud: --bucket-dados e --bucket-resultados (por omissão, os do config.yaml
    ou, se aí estiverem a null, os derivados do ID da conta AWS).

Saídas:
    As de cada script (ver o cabeçalho de cada um), mais
    results/pipeline_runs.csv   tempo de cada passo (acrescenta linhas)

Como correr:
    python run_pipeline.py                                       pergunta o dataset e se corre a cloud
    python run_pipeline.py --dataset small                       passos locais
    python run_pipeline.py --dataset 1m --steps ingest parquet   só alguns passos
    python run_pipeline.py --dataset 1m --coordenacao            com o teste de coordenação
    python run_pipeline.py --dataset small --steps cloud         bloco cloud (AWS Academy Learner Lab)
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

# O common.py está em scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent / 'scripts'))
from common import DATASETS, ROOT, append_row, load_config, now  # noqa: E402

# Passos disponíveis, pela ordem em que correm, e os scripts de cada um
STEPS = {
    'ingest': ['01_ingest.py'],
    'parquet': ['02_to_parquet.py'],
    'benchmark': ['03_benchmark.py'],
    'analise': ['04_analise.py'],
    'cloud': ['05_prepare_cloud.py', '06_upload_s3.py', '07_athena_setup.py', '08_athena_benchmark.py'],
}
# O passo cloud usa a AWS (credenciais e custos), por isso só corre com --steps cloud
STEPS_OMISSAO = ['ingest', 'parquet', 'benchmark', 'analise']


def opcoes_extra(script, args):
    """Opções que o run_pipeline.py passa a cada script, além do --dataset."""
    opcoes = []
    if script == '04_analise.py' and args.coordenacao:
        opcoes.append('--coordenacao')
    if script in ('06_upload_s3.py', '07_athena_setup.py', '08_athena_benchmark.py'):
        if args.bucket_dados:
            opcoes += ['--bucket-dados', args.bucket_dados]
        if args.bucket_resultados:
            opcoes += ['--bucket-resultados', args.bucket_resultados]
    if script == '07_athena_setup.py':
        opcoes.append('--recriar')   # recria as tabelas, para o MSCK REPAIR TABLE ver o upload
    return opcoes


def escolher(pergunta, opcoes, omissao):
    """Mostra as opções numeradas e devolve o valor da escolhida (Enter escolhe a opção omissao)."""
    print(pergunta)
    for i, (rotulo, _) in enumerate(opcoes, 1):
        marca = '  (Enter)' if i == omissao else ''
        print(f'  {i}. {rotulo}{marca}')
    while True:
        resposta = input('> ').strip()
        if resposta == '':
            return opcoes[omissao - 1][1]
        if resposta.isdigit() and 1 <= int(resposta) <= len(opcoes):
            return opcoes[int(resposta) - 1][1]
        print(f'  Escolhe um número de 1 a {len(opcoes)}.')


def confirmar_credenciais(region):
    """Confirma as credenciais AWS antes de começar. Se não forem válidas, espera que sejam atualizadas."""
    # As chaves nunca são escritas no terminal: o pipeline só lê o ~/.aws/credentials
    from athena_common import account_id, boto3_session
    while True:
        try:
            account_id(boto3_session(region))
            print('Credenciais AWS válidas.\n')
            return
        except SystemExit as erro:
            print(erro)
            input('\nDepois de atualizares o ~/.aws/credentials, carrega Enter para confirmar de novo '
                  '(Ctrl+C para sair). ')


def perguntar():
    """Modo interativo: pergunta o dataset e o que correr. Devolve as opções da linha de comandos."""
    cfg = load_config()
    datasets = list(DATASETS)
    dataset = escolher('Que dataset queres usar?', [(d, d) for d in datasets], datasets.index(cfg['dataset']) + 1)
    steps = escolher('\nO que queres correr?',
                     [('pipeline local (blocos 1 a 3)', STEPS_OMISSAO),
                      ('pipeline local e cloud (blocos 1 a 4, usa a AWS)', STEPS_OMISSAO + ['cloud']),
                      ('só a cloud (bloco 4, usa a AWS)', ['cloud'])], 1)
    print()
    if 'cloud' in steps:
        confirmar_credenciais(cfg['aws']['region'])
    opcoes = ['--dataset', dataset, '--steps'] + steps
    print('Comando equivalente: python run_pipeline.py ' + ' '.join(opcoes) + '\n')
    return opcoes


def main():
    """Lê as opções e corre cada passo pedido, registando o tempo em results/pipeline_runs.csv."""
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dataset', choices=list(DATASETS), help='sobrepõe o valor de config.yaml')
    parser.add_argument('--steps', nargs='+', choices=list(STEPS), default=STEPS_OMISSAO,
                        help=f"por omissão: {' '.join(STEPS_OMISSAO)} (o cloud só com --steps cloud)")
    parser.add_argument('--coordenacao', action='store_true',
                        help='passo analise: corre também o teste de coordenação (cerca de 10 min no 32M)')
    parser.add_argument('--bucket-dados', dest='bucket_dados', help='só passo cloud: bucket com data/cloud/<pasta>/')
    parser.add_argument('--bucket-resultados', dest='bucket_resultados',
                        help='só passo cloud: bucket dos resultados do Athena')
    # Sem opções e num terminal, pergunta o que correr; com opções (ou sem terminal) usa-as tal e qual
    if len(sys.argv) == 1 and sys.stdin.isatty():
        try:
            args = parser.parse_args(perguntar())
        except (KeyboardInterrupt, EOFError):
            sys.exit('\nCancelado.')
    else:
        args = parser.parse_args()
    cfg = load_config(args.dataset)

    for step in args.steps:
        t0 = time.perf_counter()
        for script in STEPS[step]:
            # Cada script corre num processo separado, como se fosse chamado à mão no terminal.
            # Se um falhar, o pipeline pára, para não continuar com dados incompletos.
            comando = [sys.executable, str(ROOT / 'scripts' / script), '--dataset', cfg['dataset']]
            comando += opcoes_extra(script, args)
            resultado = subprocess.run(comando)
            if resultado.returncode != 0:
                # Sem traceback: o script já explicou o erro
                sys.exit(f'[{step}] {script} falhou (código {resultado.returncode}); pipeline parado.')
        seconds = round(time.perf_counter() - t0, 2)

        append_row(cfg['paths']['results'] / 'pipeline_runs.csv',
                   {'run_at': now(), 'dataset': cfg['dataset'], 'step': step, 'seconds': seconds})
        # Inclui o arranque do Python e os imports, como no pipeline_runs.csv
        print(f'[{step}] tempo total do passo (processo completo): {seconds:.2f} s\n', flush=True)


if __name__ == '__main__':
    main()
