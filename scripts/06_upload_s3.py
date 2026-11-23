"""
06_upload_s3.py - Bloco cloud, passo 2 de 4: enviar data/cloud/<pasta>/ para o S3.

Objetivo:
    Confirmar as credenciais, criar os dois buckets (se ainda não existirem), um para dados e outro para resultadose enviar para s3://<bucket-dados>/<pasta>/ os ficheiros novos ou alterados (outro tamanho ou data mais recente), como o
    "aws s3 sync" (mas sem precisar da AWS CLI: usa o boto3). Não apaga nada no S3!!!
    O boto3 é o SDK oficial da AWS para Python. É uma biblioteca que permite fazer por código tudo o que no lab fizemos à mão, na consola.
    Não isamos nas aulas pq os lab foram efetuados pela interface web.

Entradas:
    data/cloud/<pasta>/ (criado pelo 05_prepare_cloud.py)
    config.yaml (secção aws). Se os buckets estiverem a null, os nomes são derivados do ID da conta:
    bdf26-g1-dados-<conta> e bdf26-g1-resultados-<conta>.
    Credenciais em .aws/credentials, na pasta do projeto (o run_pipeline.py pede-as no terminal).

Saídas:
    Buckets e objetos no S3. O ID da conta só aparece no ecrã.

"""
import sys
import time

from athena_common import (MENSAGEM_CREDENCIAIS, account_id, aws_settings, boto3_session,
                           is_credentials_error, resolve_buckets)
from common import ROOT, load_config


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
                     'Escolhe outro nome em config.yaml (bucket_dados / bucket_resultados).')
        if codigo not in ('404', 'NoSuchBucket'):
            raise
    # Em us-east-1 a API não aceita LocationConstraint; nas outras regiões é obrigatório.
    kwargs = {'Bucket': bucket}
    if region != 'us-east-1':
        kwargs['CreateBucketConfiguration'] = {'LocationConstraint': region}
    s3.create_bucket(**kwargs)
    s3.get_waiter('bucket_exists').wait(Bucket=bucket)
    return True


def remote_objects(s3, bucket, prefix):
    """Dicionário {chave: (tamanho em bytes, data do upload)} dos objetos em s3://bucket/prefix (com paginação)."""
    objetos = {}
    for pagina in s3.get_paginator('list_objects_v2').paginate(Bucket=bucket, Prefix=prefix):
        for obj in pagina.get('Contents', []):
            objetos[obj['Key']] = (obj['Size'], obj['LastModified'].timestamp())
    return objetos


def sync_to_s3(s3, cloud_dir, bucket, pasta):
    """Envia data/cloud/<pasta>/ para s3://bucket/<pasta>/, só os ficheiros novos ou alterados."""
    remotos = remote_objects(s3, bucket, f'{pasta}/')
    locais = sorted(f for f in cloud_dir.rglob('*') if f.is_file() and f.name != '.DS_Store')
    enviados, saltados, bytes_enviados = 0, 0, 0
    chaves_locais = set()
    t0 = time.perf_counter()

    for f in locais:
        # Chave no S3: <pasta>/<caminho relativo>, sempre com '/' (também no Windows)
        chave = f'{pasta}/{f.relative_to(cloud_dir).as_posix()}'
        chaves_locais.add(chave)
        tamanho = f.stat().st_size
        # Como o "aws s3 sync": igual se tiver o mesmo tamanho e não tiver mudado depois do último upload.
        # Não usamos o ETag porque, acima de 8 MB, o boto3 envia por partes e o ETag deixa de ser o MD5.
        remoto = remotos.get(chave)
        if remoto and remoto[0] == tamanho and remoto[1] >= f.stat().st_mtime:
            saltados += 1
            continue
        print(f'    {chave} ({tamanho / 1e6:.2f} MB)', flush=True)
        s3.upload_file(str(f), bucket, chave)
        enviados += 1
        bytes_enviados += tamanho

    print(f'  upload: {enviados} enviado(s), {saltados} já estavam iguais no S3, '
          f'{bytes_enviados / 1e6:.1f} MB em {time.perf_counter() - t0:.1f} s')

    # Como o "aws s3 sync" sem --delete, não apaga nada; mas avisa, porque um ficheiro a mais na pasta de uma tabela é lido pelo Athena (a validação do setup apanharia a diferença).
    a_mais = sorted(set(remotos) - chaves_locais)
    if a_mais:
        print(f'  AVISO: {len(a_mais)} objeto(s) no S3 que já não existem em data/cloud/ (não foram apagados):',
              file=sys.stderr)
        for chave in a_mais[:10]:
            print(f'    s3://{bucket}/{chave}', file=sys.stderr)


def main():
    """Confirma as credenciais, cria os buckets e envia data/cloud/<pasta>/ para o S3."""
    cfg = load_config()
    ds = cfg['dataset']
    aws = aws_settings(cfg)
    pasta = aws['pasta']
    cloud_dir = ROOT / 'data' / 'cloud' / pasta
    print(f'[upload_s3] dataset={ds} pasta={pasta} região={aws["region"]}')
    if not cloud_dir.exists():
        sys.exit(f'Erro: não existe {cloud_dir.relative_to(ROOT)}. Corre primeiro o 05_prepare_cloud.py.')

    # account_id() termina com as instruções do Learner Lab se as credenciais faltarem ou tiverem expirado
    session = boto3_session(aws['region'])
    account_id(session)
    resolve_buckets(aws, session)
    print(f'  credenciais OK; buckets: {aws["bucket_dados"]} e {aws["bucket_resultados"]}')

    s3 = session.client('s3')
    for chave in ('bucket_dados', 'bucket_resultados'):
        criado = ensure_bucket(s3, aws[chave], aws['region'])
        print(f'  {aws[chave]}: {"criado" if criado else "já existia"}')

    print(f'  upload de data/cloud/{pasta}/ para s3://{aws["bucket_dados"]}/{pasta}/', flush=True)
    sync_to_s3(s3, cloud_dir, aws['bucket_dados'], pasta)


if __name__ == '__main__':
    main()
