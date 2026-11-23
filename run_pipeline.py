"""
run_pipeline.py - Ponto de entrada do pipeline MovieLens (BDF 2026).

Objetivo:
    Correr, por ordem, os passos do pipeline para um dataset. Cada passo corre um ou mais
    scripts de scripts/, numerados pela ordem em que correm:
        ingest     01_ingest.py           descarregar e normalizar para CSV
        parquet    02_to_parquet.py       converter para Parquet (sem partição e por ano)
        benchmark  03_benchmark.py        medir o tempo das queries de sql/
        analise    04_analise.py          EDA e queries de sql/analise/
    E o bloco cloud, que só corre quando é escolhido no menu (usa a AWS e tem custos):
        cloud      05_prepare_cloud.py    ficheiros para o S3, em data/cloud/
                   06_upload_s3.py        buckets e upload
                   07_athena_setup.py     catálogo no Glue e validação das contagens
                   08_athena_benchmark.py benchmark DuckDB vs Athena

Entradas:
    config.yaml e as respostas ao menu: dataset (small | 1m | 32m), o que correr e onde gravar
    os resultados. Para o bloco cloud, as credenciais do Learner Lab, pedidas no terminal só
    quando as que estão em .aws/credentials (na pasta do projeto) não existem ou expiraram.

Saídas:
    As de cada script (ver o cabeçalho de cada um), mais
    results/pipeline_runs.csv   tempo de cada passo (acrescenta linhas)
    Se no menu se escolher não atualizar o repositório, tudo o que iria para results/ vai para
    results_local/, que não está no git: assim uma corrida de teste não deixa alterações para commit.

Como correr:
    python run_pipeline.py      e responder às perguntas
"""

import os
import subprocess
import sys
import time
from getpass import getpass
from pathlib import Path

# O common.py está em scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
from common import DATASETS, ROOT, append_row, load_config, now  # noqa: E402

# Credenciais AWS dentro do projeto (a pasta .aws/ está no .gitignore). Os scripts correm em
# processos separados e herdam esta variável, por isso o boto3 lê sempre este ficheiro.
CREDENCIAIS = ROOT / ".aws" / "credentials"
os.environ["AWS_SHARED_CREDENTIALS_FILE"] = str(CREDENCIAIS)

# Passos disponíveis, pela ordem em que correm, e os scripts de cada um
STEPS = {
    "ingest": ["01_ingest.py"],
    "parquet": ["02_to_parquet.py"],
    "benchmark": ["03_benchmark.py"],
    "analise": ["04_analise.py"],
    "cloud": [
        "05_prepare_cloud.py",
        "06_upload_s3.py",
        "07_athena_setup.py",
        "08_athena_benchmark.py",
    ],
}
# O passo cloud usa a AWS (credenciais e custos), por isso só corre quando é escolhido no menu
STEPS_OMISSAO = ["ingest", "parquet", "benchmark", "analise"]


def escolher(pergunta, opcoes, omissao):
    """Mostra as opções numeradas e devolve o valor da escolhida (Enter escolhe a opção omissao)."""
    print(pergunta, f"(escolhe o número da opção - de 1 a {len(opcoes)})")
    for i, (rotulo, _) in enumerate(opcoes, 1):
        marca = "  (Enter)" if i == omissao else ""
        print(f"  {i}. {rotulo}{marca}")
    while True:
        resposta = input("> ").strip()
        if resposta == "":
            return opcoes[omissao - 1][1]
        if resposta.isdigit() and 1 <= int(resposta) <= len(opcoes):
            return opcoes[int(resposta) - 1][1]
        print(f"  Escolhe um número de 1 a {len(opcoes)}.")


def limpar(texto):
    """Tira espaços e caracteres invisíveis que o browser às vezes junta ao copiar (as chaves AWS só têm ASCII visível)."""
    return "".join(c for c in texto if 32 < ord(c) < 127)


def pedir_credenciais():
    """Pede as três chaves do Learner Lab, uma a uma, e grava-as em .aws/credentials. Nunca as mostra."""
    print(
        'No Learner Lab: "Start Lab", esperar pelo indicador verde e abrir "AWS Details" > "AWS CLI: Show".\n'
        "Copia cada valor (só o que está depois do sinal =) e cola-o aqui. A chave secreta e o token não aparecem no ecrã."
    )
    chave = limpar(input("aws_access_key_id > "))
    secreta = limpar(getpass("aws_secret_access_key > "))
    token = limpar(getpass("aws_session_token > "))
    CREDENCIAIS.parent.mkdir(exist_ok=True)
    CREDENCIAIS.write_text(
        f"[default]\naws_access_key_id = {chave}\naws_secret_access_key = {secreta}\n"
        f"aws_session_token = {token}\n",
        encoding="utf-8",
    )
    CREDENCIAIS.chmod(0o600)  # só o próprio utilizador lê o ficheiro, como faz a AWS CLI
    print(f"Credenciais gravadas em {CREDENCIAIS.relative_to(ROOT)}.\n")


def confirmar_credenciais(region):
    """Confirma as credenciais AWS antes de começar; só as pede se não existirem ou não forem válidas."""
    from athena_common import account_id, boto3_session

    while True:
        try:
            account_id(boto3_session(region))
            print("Credenciais AWS válidas.\n")
            return
        except SystemExit:
            print("\nAs credenciais AWS não existem, expiraram ou são inválidas.")
            # As variáveis de ambiente têm prioridade sobre o ficheiro: com elas, as chaves novas seriam ignoradas
            if "AWS_ACCESS_KEY_ID" in os.environ:
                print("Atenção: há AWS_ACCESS_KEY_ID no ambiente e o boto3 usa essas em vez das do ficheiro.")
            pedir_credenciais()
        except Exception as erro:
            # Ex.: sem rede ou um proxy a bloquear o acesso à AWS (não é um problema das credenciais)
            sys.exit(f"Não consegui contactar a AWS: {type(erro).__name__}: {erro}")


def perguntar():
    """Pergunta o dataset, o que correr e onde gravar os resultados. Devolve (dataset, passos, locais)."""
    cfg = load_config()
    datasets = list(DATASETS)
    dataset = escolher(
        "Que dataset queres usar?",
        [(d, d) for d in datasets],
        datasets.index(cfg["dataset"]) + 1,
    )
    steps = escolher(
        "\nO que queres correr?",
        [
            ("pipeline local (blocos 1 a 3)", STEPS_OMISSAO),
            (
                "pipeline local e cloud (blocos 1 a 4, usa a AWS)",
                STEPS_OMISSAO + ["cloud"],
            ),
            ("só a cloud (bloco 4, usa a AWS)", ["cloud"]),
        ],
        1,
    )
    locais = escolher(
        "\nQueres atualizar os resultados do repositório (results/)?",
        [
            ("não: grava em results_local/, fora do git (para testar)", True),
            ("sim: grava em results/ e ficam alterações para commit", False),
        ],
        1,
    )
    print()
    if "cloud" in steps:
        confirmar_credenciais(cfg["aws"]["region"])
    return dataset, steps, locais


def main():
    """Pergunta o que correr e corre cada passo, registando o tempo em results/pipeline_runs.csv."""
    try:
        dataset, steps, locais = perguntar()
    except (KeyboardInterrupt, EOFError):
        sys.exit("\nCancelado.")
    # Os scripts correm em processos separados e herdam estas variáveis (ver common.load_config)
    os.environ["BDF_DATASET"] = dataset
    if locais:
        os.environ["BDF_RESULTS_DIR"] = "results_local"
    cfg = load_config()
    print(f"Resultados em {cfg['paths']['results'].relative_to(ROOT)}/\n", flush=True)

    for step in steps:
        t0 = time.perf_counter()
        for script in STEPS[step]:
            # Cada script corre num processo separado, como se fosse chamado à mão no terminal.
            # Se um falhar, o pipeline pára, para não continuar com dados incompletos.
            resultado = subprocess.run([sys.executable, str(ROOT / "scripts" / script)])
            if resultado.returncode != 0:
                # Sem traceback: o script já explicou o erro
                sys.exit(
                    f"[{step}] {script} falhou (código {resultado.returncode}); pipeline parado."
                )
        seconds = round(time.perf_counter() - t0, 2)

        append_row(
            cfg["paths"]["results"] / "pipeline_runs.csv",
            {
                "run_at": now(),
                "dataset": cfg["dataset"],
                "step": step,
                "seconds": seconds,
            },
        )
        # Inclui o arranque do Python e os imports, como no pipeline_runs.csv
        print(
            f"[{step}] tempo total do passo (processo completo): {seconds:.2f} s\n",
            flush=True,
        )


if __name__ == "__main__":
    main()
