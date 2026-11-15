"""
cloud_pipeline.py - Passo "cloud" do pipeline: S3 -> Glue -> Athena, com um único comando.

Objetivo:
    Reproduzir a fase 2 na conta AWS de cada aluno (AWS Academy Learner Lab) sem passos
    manuais e sem a AWS CLI (só o boto3). Por ordem:
        a. verifica as credenciais (termina com instruções se faltarem ou tiverem expirado);
        b. corre o prepare_cloud.py, se data/cloud/<pasta> não existir ou estiver desatualizada;
        c. cria os dois buckets, se ainda não existirem;
        d. envia data/cloud/<pasta>/ para s3://<bucket-dados>/<pasta>/, só os ficheiros novos
           ou com tamanho diferente (como o "aws s3 sync");
        d2. se existir o IMDb (passo imdb), prepara data/cloud/imdb/ e envia-o para
           s3://<bucket-dados>/imdb/ (a mesma pasta para os três datasets);
        e. corre o athena_setup.py --recriar (depois do upload, para o MSCK REPAIR TABLE
           ver as partições no S3) e valida as contagens;
        f. corre o athena_benchmark.py, só se a validação do setup tiver passado.
    Qualquer falha pára o pipeline com erro.

Entradas:
    data/<dataset>/parquet/ e data/<dataset>/csv/ratings.csv   (passos ingest e parquet)
    config.yaml (secção aws) e as opções --bucket-dados e --bucket-resultados. Se os buckets
    não forem indicados, os nomes são derivados do ID da conta:
    bdf26-g1-dados-<conta> e bdf26-g1-resultados-<conta>.
    Credenciais em ~/.aws/credentials (copiadas do Learner Lab em cada sessão).

Saídas:
    Buckets e objetos no S3, base de dados e tabelas no Glue Data Catalog,
    reports/cloud_manifest_<dataset>.md (se o prepare_cloud.py correr),
    reports/cloud_manifest_imdb.md (se o prepare_cloud_imdb.py correr) e
    results/cloud_benchmarks.csv. O ID da conta só aparece no ecrã.

Como correr:
    python run_pipeline.py --dataset small --steps cloud
    python scripts/cloud_pipeline.py --dataset small          (o mesmo, sem registo em pipeline_runs.csv)
"""
import argparse
import subprocess
import sys
import threading
import time

from athena_common import (MENSAGEM_CREDENCIAIS, account_id, add_aws_args, aws_settings, boto3_session,
                           is_credentials_error, resolve_buckets)
from common import DATASETS, ROOT, load_config

# Ficheiros acima deste tamanho mostram a percentagem enviada durante o upload
MOSTRAR_PROGRESSO_MB = 20


def parse_args():
    """Lê --dataset (por omissão o do config.yaml) e as opções da AWS."""
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dataset', choices=list(DATASETS), help='sobrepõe o valor de config.yaml')
    add_aws_args(parser)
    return parser.parse_args()


def prepare_needed(ds, cloud_dir, manifest, pq_dir, csv_file):
    """Devolve o motivo para (re)correr o prepare_cloud.py, ou None se data/cloud/ estiver atualizada.

    O manifesto serve de marcador: o prepare_cloud.py apaga-o ao começar e só o escreve
    no fim, se todas as verificações passarem. Se algum ficheiro da fase 1 for mais
    recente do que o manifesto, a pasta data/cloud/ foi feita com dados antigos.
    """
    if not cloud_dir.exists():
        return f'não existe {cloud_dir.relative_to(ROOT)}'
    if not manifest.exists():
        return f'não existe {manifest.relative_to(ROOT)} (preparação anterior incompleta?)'
    t_manifest = manifest.stat().st_mtime
    origens = [csv_file] + [f for f in pq_dir.rglob('*') if f.is_file()]
    mais_recentes = [f for f in origens if f.exists() and f.stat().st_mtime > t_manifest]
    if mais_recentes:
        return (f'{len(mais_recentes)} ficheiro(s) de data/{ds}/ mais recentes do que o manifesto '
                f'(ex.: {mais_recentes[0].name})')
    return None


def imdb_precisa_de_preparar():
    """Motivo para (re)correr o prepare_cloud_imdb.py, ou None se data/cloud/imdb/ estiver atualizada.

    Mesma lógica do prepare_needed: o manifesto só é escrito se as verificações passarem, e
    tem de ser mais recente do que todos os ficheiros do IMDb em data/imdb/.
    """
    manifesto = ROOT / 'reports' / 'cloud_manifest_imdb.md'
    if not (ROOT / 'data' / 'cloud' / 'imdb').exists():
        return 'não existe data/cloud/imdb'
    if not manifesto.exists():
        return 'não existe reports/cloud_manifest_imdb.md'
    origens = [f for f in (ROOT / 'data' / 'imdb').rglob('*') if f.is_file()]
    for f in origens:
        if f.stat().st_mtime > manifesto.stat().st_mtime:
            return f'{f.name} é mais recente do que o manifesto'
    return None


def run_script(script, args):
    """Corre um script de scripts/ com o mesmo Python e pára o pipeline se falhar."""
    comando = [sys.executable, str(ROOT / 'scripts' / script)] + args
    resultado = subprocess.run(comando)
    if resultado.returncode != 0:
        sys.exit(f'[cloud] ERRO: {script} terminou com código {resultado.returncode}; pipeline parado.')


def ensure_bucket(s3, bucket, region):
    """Cria o bucket se não existir. Devolve True se o criou, False se já existia."""
    from botocore.exceptions import ClientError
    try:
        s3.head_bucket(Bucket=bucket)
        return False
    except ClientError as erro:
        if is_credentials_error(erro):
            raise SystemExit(MENSAGEM_CREDENCIAIS) from erro
        codigo = erro.response.get('Error', {}).get('Code', '')
        if codigo == '403':
            sys.exit(f'Erro: o bucket {bucket} existe mas pertence a outra conta (ou não tens acesso). '
                     'Escolhe outro nome com --bucket-dados/--bucket-resultados.')
        if codigo not in ('404', 'NoSuchBucket'):
            raise
    # Em us-east-1 a API não aceita LocationConstraint; nas outras regiões é obrigatório.
    # Montamos os argumentos num dicionário e passamo-los com ** (cada chave vira um argumento).
    kwargs = {'Bucket': bucket}
    if region != 'us-east-1':
        kwargs['CreateBucketConfiguration'] = {'LocationConstraint': region}
    s3.create_bucket(**kwargs)
    s3.get_waiter('bucket_exists').wait(Bucket=bucket)
    return True


def remote_sizes(s3, bucket, prefix):
    """Dicionário {chave: tamanho em bytes} dos objetos em s3://bucket/prefix (com paginação)."""
    tamanhos = {}
    for pagina in s3.get_paginator('list_objects_v2').paginate(Bucket=bucket, Prefix=prefix):
        for obj in pagina.get('Contents', []):
            tamanhos[obj['Key']] = obj['Size']
    return tamanhos


class Progresso:
    """Callback do upload_file: mostra a percentagem enviada na mesma linha do terminal.

    O boto3 envia os ficheiros grandes em vários pedaços ao mesmo tempo e, depois de cada
    pedaço, chama o callback com o n.º de bytes enviados. Usamos uma classe (e não uma função)
    para guardar entre chamadas o total já enviado.
    """

    def __init__(self, nome, total):
        """Guarda o nome e o tamanho do ficheiro e começa a contagem em 0 bytes."""
        self.nome, self.total, self.enviado = nome, total, 0
        self.ultimo = -1   # última percentagem mostrada (para não repetir a mesma)
        # Como os pedaços vão em paralelo (várias threads), o lock garante que duas chamadas
        # não atualizam self.enviado ao mesmo tempo.
        self.lock = threading.Lock()

    def __call__(self, n_bytes):
        """Chamado pelo boto3 depois de cada pedaço: soma os bytes e mostra a percentagem."""
        # __call__ permite usar o objeto como se fosse uma função: progresso(n_bytes)
        # O "\r" volta ao início da linha, por isso a percentagem é reescrita no mesmo sítio.
        with self.lock:
            self.enviado += n_bytes
            pct = int(self.enviado * 100 / self.total) if self.total else 100
            if pct != self.ultimo:
                self.ultimo = pct
                print(f'\r    {self.nome}: {pct:3d}% de {self.total / 1e6:.1f} MB', end='', flush=True)


def sync_to_s3(s3, cloud_dir, bucket, pasta):
    """Envia data/cloud/<pasta>/ para s3://bucket/<pasta>/, só os ficheiros novos ou com tamanho diferente."""
    remotos = remote_sizes(s3, bucket, f'{pasta}/')
    locais = sorted(f for f in cloud_dir.rglob('*') if f.is_file() and f.name != '.DS_Store')
    enviados, saltados, bytes_enviados = 0, 0, 0
    chaves_locais = set()
    t0 = time.perf_counter()

    for f in locais:
        # Chave no S3: <pasta>/<caminho relativo>, sempre com '/' (também no Windows)
        chave = f'{pasta}/{f.relative_to(cloud_dir).as_posix()}'
        chaves_locais.add(chave)
        tamanho = f.stat().st_size
        if remotos.get(chave) == tamanho:
            saltados += 1
            continue
        if tamanho > MOSTRAR_PROGRESSO_MB * 1e6:
            s3.upload_file(str(f), bucket, chave, Callback=Progresso(chave, tamanho))
            print()
        else:
            s3.upload_file(str(f), bucket, chave)
            print(f'    {chave} ({tamanho / 1e6:.2f} MB)')
        enviados += 1
        bytes_enviados += tamanho

    print(f'  upload: {enviados} enviado(s), {saltados} já estavam iguais no S3, '
          f'{bytes_enviados / 1e6:.1f} MB em {time.perf_counter() - t0:.1f} s')

    # Como o "aws s3 sync" sem --delete, não apaga nada; mas avisa, porque um ficheiro a
    # mais na pasta de uma tabela é lido pelo Athena (a validação do setup apanharia a diferença).
    a_mais = sorted(set(remotos) - chaves_locais)
    if a_mais:
        print(f'  AVISO: {len(a_mais)} objeto(s) no S3 que já não existem em data/cloud/ (não foram apagados):',
              file=sys.stderr)
        for chave in a_mais[:10]:
            print(f'    s3://{bucket}/{chave}', file=sys.stderr)


def main():
    """Corre os passos a-f da fase cloud para um dataset."""
    args = parse_args()
    cfg = load_config(args.dataset)
    ds = cfg['dataset']
    aws = aws_settings(cfg, args)
    pasta = aws['pasta']
    cloud_dir = ROOT / 'data' / 'cloud' / pasta
    manifest = ROOT / 'reports' / f'cloud_manifest_{ds}.md'
    print(f'[cloud] dataset={ds} pasta={pasta} região={aws["region"]}')

    # a. Credenciais (e, se faltarem, os nomes dos buckets derivados do ID da conta)
    # account_id() termina com as instruções do Learner Lab se as credenciais faltarem ou tiverem expirado.
    # Corre sempre, mesmo que os buckets venham da linha de comandos ou do config.yaml.
    session = boto3_session(aws['region'])
    account_id(session)
    resolve_buckets(aws, session)
    print(f'[cloud] a. credenciais OK; buckets: {aws["bucket_dados"]} e {aws["bucket_resultados"]}')

    # b. data/cloud/<pasta>
    motivo = prepare_needed(ds, cloud_dir, manifest, cfg['paths']['parquet'], cfg['paths']['csv'] / 'ratings.csv')
    if motivo:
        print(f'[cloud] b. a preparar data/cloud/{pasta}/: {motivo}', flush=True)
        run_script('prepare_cloud.py', ['--dataset', ds])
    else:
        print(f'[cloud] b. data/cloud/{pasta}/ já está atualizada (manifesto mais recente do que data/{ds}/)')

    # c. Buckets
    s3 = session.client('s3')
    for chave in ('bucket_dados', 'bucket_resultados'):
        criado = ensure_bucket(s3, aws[chave], aws['region'])
        print(f'[cloud] c. {aws[chave]}: {"criado" if criado else "já existia"}')

    # d. Upload
    print(f'[cloud] d. upload de data/cloud/{pasta}/ para s3://{aws["bucket_dados"]}/{pasta}/', flush=True)
    sync_to_s3(s3, cloud_dir, aws['bucket_dados'], pasta)

    # d2. IMDb (só se o passo imdb já tiver corrido): mesma pasta imdb/ para todos os datasets
    if (ROOT / 'data' / 'imdb' / 'parquet').exists():
        motivo_imdb = imdb_precisa_de_preparar()
        if motivo_imdb:
            print(f'[cloud] d2. a preparar data/cloud/imdb/: {motivo_imdb}', flush=True)
            run_script('prepare_cloud_imdb.py', [])
        print(f'[cloud] d2. upload de data/cloud/imdb/ para s3://{aws["bucket_dados"]}/imdb/', flush=True)
        sync_to_s3(s3, ROOT / 'data' / 'cloud' / 'imdb', aws['bucket_dados'], 'imdb')
    else:
        print('[cloud] d2. sem IMDb em data/imdb/parquet/ (passo imdb não corrido): salta o IMDb')

    # e. e f. Os nomes dos buckets já resolvidos passam explicitamente, para os dois scripts
    # usarem exatamente os mesmos (e não voltarem a perguntar o ID da conta).
    opcoes_aws = ['--dataset', ds, '--region', aws['region'], '--workgroup', aws['workgroup'],
                  '--bucket-dados', aws['bucket_dados'], '--bucket-resultados', aws['bucket_resultados']]
    print('[cloud] e. athena_setup.py --recriar', flush=True)
    run_script('athena_setup.py', opcoes_aws + ['--recriar'])
    print('[cloud] f. athena_benchmark.py (a validação do setup passou)', flush=True)
    run_script('athena_benchmark.py', opcoes_aws)
    print(f'[cloud] concluído: dataset {ds} no S3, catálogo movielens_{ds} validado e benchmark registado')


if __name__ == '__main__':
    main()
