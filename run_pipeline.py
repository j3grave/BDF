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
    Com --resultados-locais, tudo o que iria para results/ vai para results_local/, que não está
    no git: assim uma corrida de teste não deixa alterações para commit.

Como correr:
    python run_pipeline.py                                       pergunta o dataset e se corre a cloud
    python run_pipeline.py --dataset small                       passos locais
    python run_pipeline.py --dataset small --resultados-locais   o mesmo, sem mexer em results/
    python run_pipeline.py --dataset 1m --steps ingest parquet   só alguns passos
    python run_pipeline.py --dataset 1m --coordenacao            com o teste de coordenação (20 permutações)
    python run_pipeline.py --dataset 32m --coordenacao --repeticoes 800   teste conclusivo (~40 min no 32M)
    python run_pipeline.py --dataset small --steps cloud         bloco cloud (AWS Academy Learner Lab)
"""
import argparse
import os
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
        opcoes += ['--coordenacao', '--repeticoes', str(args.repeticoes)]
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


def ficheiro_credenciais():
    """Caminho do ficheiro de credenciais que o boto3 lê (o ~/.aws/credentials, salvo indicação em contrário)."""
    return Path(os.environ.get('AWS_SHARED_CREDENTIALS_FILE', Path.home() / '.aws' / 'credentials')).expanduser()


def ler_clipboard():
    """Texto copiado (macOS e Windows), ou None se não for possível lê-lo neste sistema."""
    if sys.platform == 'darwin':
        comando = ['pbpaste']
    elif sys.platform == 'win32':
        comando = ['powershell', '-NoProfile', '-Command', 'Get-Clipboard']
    else:
        return None
    try:
        return subprocess.run(comando, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None


def gravar_credenciais(texto):
    """Grava o bloco [default] copiado do Learner Lab no ficheiro de credenciais. Nunca mostra as chaves."""
    if texto is None:
        print('Neste sistema não consigo ler o que foi copiado: atualiza o ficheiro noutro terminal.')
        return False
    # As chaves AWS só têm caracteres ASCII visíveis: tira espaços e caracteres invisíveis que o
    # browser às vezes junta ao copiar (espaço não separável, espaço de largura zero, ...)
    linhas = []
    for linha in texto.splitlines():
        limpa = ''.join(c for c in linha if 32 < ord(c) < 127)
        if limpa:
            linhas.append(limpa)
    chaves = ('aws_access_key_id', 'aws_secret_access_key', 'aws_session_token')
    em_falta = []
    for chave in chaves:
        if not any(linha.startswith(chave) for linha in linhas):
            em_falta.append(chave)
    if not linhas or linhas[0] != '[default]' or em_falta:
        # Não gravar outra coisa por cima das credenciais (ex.: se entretanto se copiou outro texto)
        print('Nada gravado: o que está copiado não é o bloco [default] do Learner Lab (com aws_access_key_id,\n'
              'aws_secret_access_key e aws_session_token). Copia-o de novo em "AWS Details" > "AWS CLI: Show".')
        return False
    caminho = ficheiro_credenciais()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text('\n'.join(linhas) + '\n', encoding='utf-8')
    caminho.chmod(0o600)   # só o próprio utilizador lê o ficheiro, como faz a AWS CLI
    print(f'Bloco [default] gravado em {caminho}.')
    return True


def diagnostico_credenciais(region, erro):
    """Mostra porque é que as credenciais falharam, sem nunca mostrar as chaves."""
    from athena_common import boto3_session
    causa = erro.__cause__
    resposta = getattr(causa, 'response', None) or {}
    codigo = resposta.get('Error', {}).get('Code') or (type(causa).__name__ if causa else 'desconhecido')
    mensagem = resposta.get('Error', {}).get('Message', '')
    print(f'  Resposta da AWS: {codigo}' + (f' ({mensagem})' if mensagem else ''))
    # Variáveis de ambiente e perfis têm prioridade sobre o ficheiro de credenciais
    variaveis = [v for v in ('AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN', 'AWS_PROFILE',
                             'AWS_SHARED_CREDENTIALS_FILE', 'AWS_CONFIG_FILE') if v in os.environ]
    print(f"  Variáveis AWS_* no ambiente: {', '.join(variaveis) if variaveis else 'nenhuma'}")
    credenciais = boto3_session(region).get_credentials()
    print(f"  O boto3 está a ler as credenciais de: {credenciais.method if credenciais else 'nenhum sítio'}")
    caminho = ficheiro_credenciais()
    if caminho.exists():
        linhas = caminho.read_text(encoding='utf-8', errors='replace').splitlines()
        chaves = [c for c in ('aws_access_key_id', 'aws_secret_access_key', 'aws_session_token')
                  if any(linha.strip().startswith(c) for linha in linhas)]
        estranhos = any(not (32 <= ord(c) < 127) for linha in linhas for c in linha)
        alterado = time.strftime('%d/%m/%Y %H:%M', time.localtime(caminho.stat().st_mtime))
        print(f'  {caminho}: alterado a {alterado}, {len(linhas)} linhas, '
              f"primeira linha {linhas[0].strip() if linhas else '(vazio)'}, chaves: {', '.join(chaves) or 'nenhuma'}, "
              f"caracteres invisíveis: {'sim' if estranhos else 'não'}")
    else:
        print(f'  {caminho} não existe.')
    print(f"  Hora desta máquina (UTC): {time.strftime('%d/%m/%Y %H:%M', time.gmtime())}")


def confirmar_credenciais(region):
    """Confirma as credenciais AWS antes de começar. Se não forem válidas, espera que sejam atualizadas."""
    from athena_common import account_id, boto3_session
    while True:
        try:
            account_id(boto3_session(region))
            print('Credenciais AWS válidas.\n')
            return
        except SystemExit as erro:
            print('As credenciais AWS não existem, expiraram ou são inválidas. No Learner Lab: "Start Lab",\n'
                  'esperar pelo indicador verde e, em "AWS Details" > "AWS CLI: Show", copiar o bloco [default].\n')
            diagnostico_credenciais(region, erro)
        except Exception as erro:
            # Ex.: sem rede ou um proxy a bloquear o acesso à AWS (não é um problema das credenciais)
            print(f'Não consegui contactar a AWS para confirmar as credenciais: {type(erro).__name__}: {erro}')
        # Este terminal está à espera da resposta: um pbpaste escrito aqui não corre. Por isso, a cada
        # Enter, o pipeline lê ele próprio o que foi copiado e grava-o, se for o bloco [default].
        input('\nCopia o bloco [default] do Learner Lab e carrega Enter aqui (Ctrl+C para sair) > ')
        gravar_credenciais(ler_clipboard())


def perguntar():
    """Modo interativo: pergunta o dataset e o que correr. Devolve as opções da linha de comandos."""
    cfg = load_config()
    datasets = list(DATASETS)
    dataset = escolher('Que dataset queres usar?', [(d, d) for d in datasets], datasets.index(cfg['dataset']) + 1)
    steps = escolher('\nO que queres correr?',
                     [('pipeline local (blocos 1 a 3)', STEPS_OMISSAO),
                      ('pipeline local e cloud (blocos 1 a 4, usa a AWS)', STEPS_OMISSAO + ['cloud']),
                      ('só a cloud (bloco 4, usa a AWS)', ['cloud'])], 1)
    # 800 permutações: com 40 comparações, o valor-p mínimo 1/(R+1) só passa o limiar de Bonferroni (0,05/40) com R >= 799
    repeticoes = None
    if 'analise' in steps:
        repeticoes = escolher('\nCorrer o teste de coordenação entre contas?',
                              [('não', None),
                               ('sim, exploratório: 20 permutações (~1 min no 32M)', 20),
                               ('sim, conclusivo: 800 permutações (~40 min no 32M)', 800)], 2)
    locais = escolher('\nQueres atualizar os resultados do repositório (results/)?',
                      [('não: grava em results_local/, fora do git (para testar)', True),
                       ('sim: grava em results/ e ficam alterações para commit', False)], 1)
    print()
    if 'cloud' in steps:
        confirmar_credenciais(cfg['aws']['region'])
    opcoes = ['--dataset', dataset, '--steps'] + steps
    if locais:
        opcoes.append('--resultados-locais')
    if repeticoes:
        opcoes += ['--coordenacao', '--repeticoes', str(repeticoes)]
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
                        help='passo analise: corre também o teste de coordenação entre contas')
    parser.add_argument('--repeticoes', type=int, default=20,
                        help='com --coordenacao: n.º de permutações (20 por omissão; 800 para passar Bonferroni)')
    parser.add_argument('--resultados-locais', action='store_true',
                        help='grava os resultados em results_local/ (fora do git) em vez de results/')
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
    if args.resultados_locais:
        # Os scripts correm em processos separados e herdam esta variável (ver common.load_config)
        os.environ['BDF_RESULTS_DIR'] = 'results_local'
    cfg = load_config(args.dataset)
    print(f"Resultados em {cfg['paths']['results'].relative_to(ROOT)}/\n", flush=True)

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
