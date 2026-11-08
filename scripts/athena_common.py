"""
athena_common.py - Configuração e funções partilhadas pelos scripts da fase 2 que usam o Athena.

Objetivo:
    Reunir num só sítio o que o athena_setup.py e o athena_benchmark.py usam: as opções
    da linha de comandos da AWS (região, buckets), a leitura dos .sql de sql/athena/ e
    uma pequena classe que submete uma query ao Athena, espera que termine e devolve as
    estatísticas (tempo e bytes lidos). Também resolve os nomes dos buckets: se não vierem
    da linha de comandos nem do config.yaml, são derivados do ID da conta AWS, para cada
    aluno ter os seus sem configurar nada.

Entradas:
    config.yaml (secção aws) e as opções --region, --bucket-dados, --bucket-resultados, --workgroup.
    Credenciais AWS: as do ~/.aws/credentials (no AWS Academy Learner Lab, copiadas de
    "AWS Details"). Nunca ficam no repositório.

Saídas:
    Nenhuma diretamente; é importado pelos outros scripts.

Como correr:
    Não se corre sozinho.
"""
import csv
import io
import platform
import time
from string import Template
from urllib.parse import urlparse

from common import ROOT

ATHENA_SQL = ROOT / 'sql' / 'athena'

INTERVALO_POLL = 0.5    # segundos entre cada pergunta "a query já terminou?"
TIMEOUT = 900           # segundos; acima disto a query é cancelada
USD_POR_TB = 5.0        # preço do Athena por TB lido (us-east-1), para estimar o custo

# Códigos de erro da AWS que, no Learner Lab, quase sempre querem dizer "sessão expirada"
ERROS_CREDENCIAIS = {'ExpiredTokenException', 'ExpiredToken', 'UnrecognizedClientException',
                     'InvalidClientTokenId', 'InvalidAccessKeyId', 'SignatureDoesNotMatch'}

# Nomes dos buckets quando não vêm da linha de comandos nem do config.yaml (null).
# O sufixo é o ID da conta (12 dígitos): os nomes de buckets são únicos em toda a AWS,
# por isso cada aluno precisa dos seus. O ID só aparece no ecrã, nunca nos ficheiros do repositório.
PREFIXO_BUCKETS = {'bucket_dados': 'bdf26-g1-dados', 'bucket_resultados': 'bdf26-g1-resultados'}

if platform.system() == 'Darwin':
    _COLAR = ('   e, no terminal, escrever o bloco no ficheiro das credenciais:\n'
              '     mkdir -p ~/.aws && pbpaste > ~/.aws/credentials\n')
else:
    _COLAR = ('   e colá-lo em ~/.aws/credentials (no Windows: %UserProfile%\\.aws\\credentials),\n'
              '   substituindo o conteúdo anterior.\n')
MENSAGEM_CREDENCIAIS = (
    'Erro: as credenciais AWS não existem, expiraram ou são inválidas.\n'
    'No AWS Academy Learner Lab (as credenciais mudam a cada sessão e duram cerca de 4 horas):\n'
    '1. "Start Lab" e esperar que o indicador fique verde.\n'
    '2. "AWS Details" > "AWS CLI: Show" e copiar o bloco [default] (inclui aws_session_token),\n'
    + _COLAR +
    '3. Voltar a correr o comando.')


class AthenaError(Exception):
    """Uma query terminou em FAILED ou CANCELLED."""


def add_aws_args(parser):
    """Acrescenta ao parser as opções comuns aos scripts do Athena."""
    parser.add_argument('--region', help='região AWS (sobrepõe config.yaml; Learner Lab: us-east-1)')
    parser.add_argument('--bucket-dados', dest='bucket_dados', help='bucket com data/cloud/<pasta>/')
    parser.add_argument('--bucket-resultados', dest='bucket_resultados',
                        help='bucket onde o Athena escreve os resultados das queries')
    parser.add_argument('--workgroup', help='workgroup do Athena (por omissão: primary)')
    parser.add_argument('--dry-run', action='store_true',
                        help='não contacta a AWS: só verifica e mostra o SQL que seria enviado')


def aws_settings(cfg, args):
    """Junta a secção aws do config.yaml com as opções da linha de comandos (que têm prioridade)."""
    aws = dict(cfg.get('aws') or {})
    for chave in ('region', 'bucket_dados', 'bucket_resultados', 'workgroup'):
        valor = getattr(args, chave, None)
        if valor:
            aws[chave] = valor
    aws['region'] = aws.get('region') or 'us-east-1'
    aws['workgroup'] = aws.get('workgroup') or 'primary'
    # Nomes derivados do dataset: base de dados movielens_32m e prefixo ml-32m/ no bucket
    aws['database'] = f"movielens_{cfg['dataset']}"
    aws['pasta'] = cfg['source']['folder']
    return aws


def is_credentials_error(erro):
    """True se o erro do boto3 quer dizer credenciais em falta, expiradas ou inválidas."""
    if type(erro).__name__ in ('NoCredentialsError', 'PartialCredentialsError'):
        return True
    codigo = getattr(erro, 'response', {}).get('Error', {}).get('Code', '')
    return codigo in ERROS_CREDENCIAIS


def boto3_session(region):
    """Sessão do boto3 na região indicada (termina com uma mensagem clara se faltar o boto3)."""
    try:
        import boto3
    except ImportError:
        raise SystemExit('Erro: falta o boto3. Instala-o com: pip install -r requirements.txt') from None
    return boto3.Session(region_name=region)


def account_id(session):
    """ID da conta AWS das credenciais atuais. Termina com instruções se não houver credenciais válidas."""
    try:
        return session.client('sts').get_caller_identity()['Account']
    except Exception as erro:
        if is_credentials_error(erro):
            raise SystemExit(MENSAGEM_CREDENCIAIS) from erro
        raise


def resolve_buckets(aws, session=None):
    """Preenche os nomes dos buckets que faltam com os derivados do ID da conta.

    Prioridade: linha de comandos > config.yaml > bdf26-g1-dados-<conta> / bdf26-g1-resultados-<conta>.
    Só contacta a AWS (STS) se faltar algum nome.
    """
    em_falta = [chave for chave in PREFIXO_BUCKETS if not aws.get(chave)]
    if em_falta:
        conta = account_id(session or boto3_session(aws['region']))
        for chave in em_falta:
            aws[chave] = f'{PREFIXO_BUCKETS[chave]}-{conta}'
    return aws


def read_sql(path, params):
    """Lê um .sql, tira as linhas de comentário, substitui os ${parametros} e tira o ';' final.

    O Athena aceita uma só instrução por pedido; os comentários ficam nos ficheiros para
    quem os lê, mas não são enviados (alguns comandos de DDL não os aceitam no início).
    """
    linhas = [linha for linha in path.read_text().splitlines() if not linha.strip().startswith('--')]
    sql = Template('\n'.join(linhas)).substitute(params).strip()
    return sql.rstrip(';').strip()


class Athena:
    """Cliente mínimo do Athena: submete uma query, espera pelo fim e devolve as estatísticas."""

    def __init__(self, aws, athena_client=None, s3_client=None):
        # Os clientes podem ser passados de fora (útil para testar sem AWS).
        if athena_client is None or s3_client is None:
            session = boto3_session(aws['region'])
            athena_client = athena_client or session.client('athena')
            s3_client = s3_client or session.client('s3')
        self.athena = athena_client
        self.s3 = s3_client
        self.workgroup = aws['workgroup']
        # Os resultados de cada query ficam num CSV (e um .metadata) nesta pasta do bucket de resultados
        self.output = f"s3://{aws['bucket_resultados']}/athena-results/{aws['database']}/"

    def _call(self, funcao, **kwargs):
        """Chama a API e traduz os erros de credenciais numa mensagem clara."""
        try:
            return funcao(**kwargs)
        except Exception as erro:
            if is_credentials_error(erro):
                raise SystemExit(MENSAGEM_CREDENCIAIS) from erro
            raise

    def run(self, sql, database=None):
        """Corre uma query e devolve {id, engine_s, total_s, scanned_bytes, output}.

        engine_s: tempo de execução no motor; total_s: inclui fila e planeamento.
        A reutilização de resultados do Athena (result reuse) só acontece se for pedida
        em cada query; aqui não é, por isso cada corrida lê mesmo os dados.
        """
        kwargs = {'QueryString': sql, 'WorkGroup': self.workgroup,
                  'ResultConfiguration': {'OutputLocation': self.output}}
        if database:
            kwargs['QueryExecutionContext'] = {'Database': database}
        query_id = self._call(self.athena.start_query_execution, **kwargs)['QueryExecutionId']

        inicio = time.monotonic()
        while True:
            execucao = self._call(self.athena.get_query_execution, QueryExecutionId=query_id)['QueryExecution']
            estado = execucao['Status']['State']
            if estado in ('SUCCEEDED', 'FAILED', 'CANCELLED'):
                break
            if time.monotonic() - inicio > TIMEOUT:
                self._call(self.athena.stop_query_execution, QueryExecutionId=query_id)
                raise AthenaError(f'query cancelada ao fim de {TIMEOUT} s: {sql[:200]}')
            time.sleep(INTERVALO_POLL)

        if estado != 'SUCCEEDED':
            motivo = execucao['Status'].get('StateChangeReason', 'sem motivo indicado')
            raise AthenaError(f'query terminou em {estado}: {motivo}\n--- SQL ---\n{sql}')

        stats = execucao.get('Statistics', {})
        return {
            'id': query_id,
            'engine_s': stats.get('EngineExecutionTimeInMillis', 0) / 1000,
            'total_s': stats.get('TotalExecutionTimeInMillis', 0) / 1000,
            'scanned_bytes': stats.get('DataScannedInBytes', 0),
            'output': execucao.get('ResultConfiguration', {}).get('OutputLocation', ''),
        }

    def rows(self, query_id):
        """Linhas do resultado (sem o cabeçalho), como tuplos de texto. Só para resultados pequenos."""
        resposta = self._call(self.athena.get_query_results, QueryExecutionId=query_id, MaxResults=1000)
        linhas = resposta['ResultSet']['Rows'][1:]   # a primeira linha é o cabeçalho
        return [tuple(campo.get('VarCharValue') for campo in linha['Data']) for linha in linhas]

    def count_result_rows(self, output):
        """N.º de linhas do CSV de resultado no S3 (sem o cabeçalho).

        Mais rápido do que paginar get_query_results quando o resultado é grande
        (a query 03 devolve uma linha por utilizador: ~200 mil no 32M).
        """
        url = urlparse(output)
        corpo = self._call(self.s3.get_object, Bucket=url.netloc, Key=url.path.lstrip('/'))['Body'].read()
        leitor = csv.reader(io.StringIO(corpo.decode('utf-8')))
        return max(sum(1 for _ in leitor) - 1, 0)
