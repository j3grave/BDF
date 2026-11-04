"""
athena_common.py - Configuração e funções partilhadas pelos scripts da fase 2 que usam o Athena.

Objetivo:
    Reunir num só sítio o que o athena_setup.py e o athena_benchmark.py usam: as opções
    da linha de comandos da AWS (região, buckets), a leitura dos .sql de sql/athena/ e
    uma pequena classe que submete uma query ao Athena, espera que termine e devolve as
    estatísticas (tempo e bytes lidos).

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
MENSAGEM_CREDENCIAIS = (
    'Erro: as credenciais AWS não existem, expiraram ou são inválidas.\n'
    'No AWS Academy Learner Lab: "Start Lab", depois "AWS Details" > "AWS CLI: Show", e copiar\n'
    'o bloco [default] (com aws_session_token) para ~/.aws/credentials. As credenciais\n'
    'mudam a cada sessão do laboratório. Testar com: aws sts get-caller-identity')


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


def require_buckets(aws):
    """Termina com erro se faltar o nome de algum bucket (exceto em --dry-run, que não os usa)."""
    em_falta = [nome for nome in ('bucket_dados', 'bucket_resultados') if not aws.get(nome)]
    if em_falta:
        opcoes = ', '.join('--' + nome.replace('_', '-') for nome in em_falta)
        raise SystemExit(f'Erro: falta o nome do bucket ({opcoes}). '
                         'Indica-o na linha de comandos ou na secção aws do config.yaml.')


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
            try:
                import boto3
            except ImportError:
                raise SystemExit('Erro: falta o boto3. Instala-o com: pip install -r requirements.txt') from None
            session = boto3.Session(region_name=aws['region'])
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
            codigo = getattr(erro, 'response', {}).get('Error', {}).get('Code', '')
            if codigo in ERROS_CREDENCIAIS or type(erro).__name__ in ('NoCredentialsError', 'PartialCredentialsError'):
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
