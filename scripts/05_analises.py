"""
05_analises.py - Passo 5 do pipeline: análises extra (queries do notebook do Luís, revistas).

Objetivo:
    Correr as queries de sql/analise/ sobre um dataset e gravar o resultado de cada uma em
    CSV. As queries vêm do notebook do Luís (células 108, 109 e 112), extraídas para ficheiros
    .sql e corrigidas onde foi preciso (ver docs/validacao_queries_colega.md).
    Tal como no 04_eda.py, as agregações são feitas no DuckDB: o resultado vai diretamente do
    DuckDB para o CSV (COPY), sem passar pelo Python. Só os resultados pequenos (uma linha, ou
    uma linha por utilizador) são lidos pelo Python para as verificações.

    Verificações que fazem o script falhar (as mesmas asserções do notebook, mais o 04_eda.py):
    - qualidade: 0 linhas com nulos e 0 valores fora da escala (no 1M, também só inteiros 1-5);
    - integridade: 0 ids de filmes repetidos e 0 avaliações sem filme;
    - linhas, utilizadores, filmes avaliados e média global iguais aos de
      results/<dataset>/eda/eda_indicadores.csv (se o 04_eda.py já tiver corrido);
    - a soma das avaliações por ano (anual) igual ao total de linhas.

Entradas:
    sql/analise/*.sql                    queries com os marcadores ${ratings}, ${movies} (e ${suspeitos})
    data/<dataset>/parquet/              Parquet sem partição (--fonte parquet, por omissão)
    data/<dataset>/csv/                  CSV normalizados (--fonte csv)
    sql/athena/analise/*.sql             versões Athena (só com --emular-athena)

Saídas (em results/<dataset>/analises/):
    <query>.csv                          resultado de cada query
    analises_resumo.csv                  n.º de linhas e tempo de cada query
    analises_relatorio.md                fontes, verificações e resumo
    athena_emulado/<query>.csv           com --emular-athena: resultado das versões Athena
                                         emuladas no DuckDB
    athena_emulado/comparacao.csv        com --emular-athena: DuckDB vs Athena emulado

Como correr:
    python scripts/05_analises.py --dataset small
    python scripts/05_analises.py --dataset 1m --fonte csv
    python scripts/05_analises.py --dataset small --emular-athena
    python scripts/05_analises.py --dataset small --queries anual qualidade
    (ou, dentro do pipeline: python run_pipeline.py --dataset small --steps analises)

Notas:
    - A ligação fixa SET TimeZone = 'UTC'; o ano vem da coluna year de ${ratings}, calculada
      com epoch_ms (sem fuso), como no 03_benchmark.py. Nenhum resultado depende da máquina.
    - ${suspeitos} é a tabela por utilizador de 10_flag_bots.sql. O script corre essa query
      primeiro e guarda-a numa tabela temporária; no Athena seria um CTAS em Parquet.
    - A emulação do Athena valida a lógica e os resultados das versões Athena (com divisão
      inteira entre inteiros, como no Trino, e macros para from_unixtime, date_format,
      sequence e approx_percentile). NÃO valida a sintaxe do Trino: isso só na AWS.
"""
import argparse
import math
import time
from pathlib import Path
from string import Template

import duckdb
import pandas as pd

from common import DATASETS, ROOT, SCHEMAS, duckdb_columns, load_config

PASTA_SQL = ROOT / 'sql' / 'analise'
PASTA_SQL_ATHENA = ROOT / 'sql' / 'athena' / 'analise'

# Queries cujo resultado outras queries usam: nome do ficheiro -> nome da tabela temporária.
# 10_flag_bots corre primeiro (a ordem alfabética já o põe à frente, por começar por um dígito).
MATERIALIZAR = {'10_flag_bots': 'suspeitos'}
DEPENDENCIAS = {'eventos': ['10_flag_bots']}


def parse_args():
    """Lê --dataset, --fonte, --queries e --emular-athena."""
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dataset', choices=list(DATASETS), help='sobrepõe o valor de config.yaml')
    ap.add_argument('--fonte', default='parquet', choices=['parquet', 'csv'],
                    help='ler o Parquet sem partição (por omissão) ou os CSV normalizados')
    ap.add_argument('--queries', nargs='+', metavar='NOME',
                    help='correr só estas queries (nomes dos ficheiros sem .sql)')
    ap.add_argument('--emular-athena', action='store_true',
                    help='correr também as versões de sql/athena/analise/ emuladas no DuckDB e comparar')
    return ap.parse_args()


# ---------------------------------------------------------------------------
# Ligação aos dados
# ---------------------------------------------------------------------------
def leitor(cfg, tabela, fonte):
    """Texto SQL que lê uma tabela do dataset no formato pedido (Parquet ou CSV)."""
    if fonte == 'parquet':
        caminho = cfg['paths']['parquet'] / f'{tabela}.parquet'
        texto = f"read_parquet('{caminho.as_posix()}')"
    else:
        caminho = cfg['paths']['csv'] / f'{tabela}.csv'
        # Tipos fixos (common.SCHEMAS) e as mesmas opções do 02_to_parquet.py: os títulos podem
        # ter aspas escritas como "" (ex.: "11'09""01 - September 11 (2002)")
        texto = (f"read_csv('{caminho.as_posix()}', header = true, delim = ',', quote = '\"', "
                 f"escape = '\"', columns = {duckdb_columns(SCHEMAS[tabela])})")
    if not caminho.exists():
        raise SystemExit(f'Não encontrei {caminho.relative_to(ROOT)}. Corre primeiro a ingestão '
                         'e a conversão para Parquet (run_pipeline.py --steps ingest parquet).')
    return texto, f'{fonte}: {caminho.relative_to(ROOT).as_posix()}'


def ligar(cfg, fonte):
    """Ligação DuckDB em UTC com as views ratings_base (sem year) e movies. Devolve (ligação, origem)."""
    con = duckdb.connect()
    # Fuso fixo: to_timestamp e afins devolvem TIMESTAMP WITH TIME ZONE, e o ano ou o mês
    # dependeriam do fuso da máquina. As queries usam epoch_ms/year, mas assim fica garantido.
    con.execute("SET TimeZone = 'UTC'")
    origem = {}
    for tabela, view in (('ratings', 'ratings_base'), ('movies', 'movies')):
        texto, origem[tabela] = leitor(cfg, tabela, fonte)
        con.execute(f'CREATE VIEW {view} AS SELECT * FROM {texto}')
    return con, origem


# ${ratings} tem sempre a coluna year (em UTC), como no 03_benchmark.py.
FONTES_DUCKDB = {
    'ratings': '(SELECT *, year(epoch_ms(timestamp * 1000)) AS year FROM ratings_base)',
    'movies': 'movies',
    'suspeitos': 'suspeitos',
}

# Na emulação do Athena, ${ratings} é escrito como no athena_benchmark.py para as tabelas sem
# partição: year a partir de from_unixtime (UTC no Trino; aqui, a macro abaixo).
FONTES_ATHENA = {
    'ratings': '(SELECT x.*, year(from_unixtime(x."timestamp")) AS year FROM ratings_base AS x)',
    'movies': 'movies',
    'suspeitos': 'suspeitos',
}

MACROS_ATHENA = [
    # Trino: from_unixtime(bigint) devolve timestamp em UTC. make_timestamp (microssegundos)
    # devolve TIMESTAMP sem fuso, por isso também não depende do fuso da sessão.
    'CREATE OR REPLACE MACRO from_unixtime(x) AS make_timestamp(CAST(x AS BIGINT) * 1000000)',
    'CREATE OR REPLACE MACRO date_format(t, f) AS strftime(t, f)',
    'CREATE OR REPLACE MACRO sequence(a, b) AS range(a, b + 1)',
    # approx_percentile do Trino é aproximado; aqui usa-se o quantil exato (diferenças pequenas)
    'CREATE OR REPLACE MACRO approx_percentile(x, p) AS quantile_cont(x, p)',
]


def preparar_emulacao(con):
    """Põe a ligação a comportar-se como o Trino onde isso muda resultados."""
    # No Trino, bigint / bigint é divisão inteira; no DuckDB é real. Com esta opção o DuckDB
    # faz como o Trino, e um erro desses nas versões Athena aparece na comparação.
    con.execute('SET integer_division = true')
    for m in MACROS_ATHENA:
        con.execute(m)


# ---------------------------------------------------------------------------
# Execução das queries
# ---------------------------------------------------------------------------
def listar_queries(pasta, pedidas):
    """Ficheiros .sql de uma pasta (ordem alfabética), filtrados por --queries com as dependências."""
    ficheiros = {f.stem: f for f in sorted(pasta.glob('*.sql'))}
    if pedidas:
        desconhecidas = [q for q in pedidas if q not in ficheiros]
        if desconhecidas:
            raise SystemExit(f'Queries desconhecidas: {desconhecidas}. Existem: {list(ficheiros)}')
        nomes = set(pedidas)
        for q in pedidas:
            nomes.update(DEPENDENCIAS.get(q, []))
        ficheiros = {k: v for k, v in ficheiros.items() if k in nomes}
    return ficheiros


def correr(con, nome, ficheiro, fontes, destino):
    """Corre uma query, grava o resultado em CSV (COPY) e devolve (n.º de linhas, segundos)."""
    sql = Template(ficheiro.read_text(encoding='utf-8')).substitute(fontes).strip().rstrip(';')
    t0 = time.perf_counter()
    if nome in MATERIALIZAR:
        # Tabela temporária para as queries que dependem desta (ex.: ${suspeitos} em eventos)
        tabela = MATERIALIZAR[nome]
        con.execute(f'CREATE OR REPLACE TEMP TABLE {tabela} AS {sql}')
        sql = f'SELECT * FROM {tabela}'
    # COPY escreve diretamente do DuckDB para o ficheiro, sem passar o resultado pelo Python
    # (o COPY devolve o n.º de linhas escritas)
    linhas = con.execute(f"COPY ({sql}) TO '{destino.as_posix()}' (HEADER, DELIMITER ',')").fetchone()[0]
    return linhas, time.perf_counter() - t0


# ---------------------------------------------------------------------------
# Verificações
# ---------------------------------------------------------------------------
def ler(pasta, nome):
    """Lê o CSV de uma query, ou None se essa query não correu."""
    f = pasta / f'{nome}.csv'
    return pd.read_csv(f) if f.exists() else None


def verificar(pasta, ds):
    """Asserções sobre os resultados. Devolve uma lista de (verificação, resultado, ok)."""
    res = []
    qual = ler(pasta, 'qualidade')
    if qual is not None:
        q = qual.iloc[0]
        res.append(('qualidade: linhas com nulos = 0', int(q.linhas_com_nulos), q.linhas_com_nulos == 0))
        res.append(('qualidade: fora da escala comum = 0', int(q.fora_dominio_comum), q.fora_dominio_comum == 0))
        res.append(('qualidade: pares (utilizador, filme) repetidos', int(q.pares_repetidos), True))
        if ds == '1m':   # o 1M só tem estrelas inteiras de 1 a 5
            ok = q.nao_inteiros == 0 and q.inferior_a_um == 0
            res.append(('qualidade (1M): só inteiros de 1 a 5', f'{int(q.nao_inteiros)} / {int(q.inferior_a_um)}', ok))
    integ = ler(pasta, 'integridade')
    if integ is not None:
        i = integ.iloc[0]
        res.append(('integridade: ids de filmes repetidos = 0', int(i.ids_filmes_repetidos), i.ids_filmes_repetidos == 0))
        res.append(('integridade: avaliações sem filme = 0', int(i.ratings_sem_filme), i.ratings_sem_filme == 0))

    # Comparação com o 04_eda.py (se já correu para este dataset)
    f_ind = ROOT / 'results' / ds / 'eda' / 'eda_indicadores.csv'
    if f_ind.exists() and qual is not None:
        ind = pd.read_csv(f_ind).set_index('indicador')['valor']
        q = qual.iloc[0]
        for col, chave in (('linhas', 'n_ratings'), ('utilizadores', 'n_utilizadores'), ('filmes', 'n_filmes_avaliados')):
            res.append((f'{col} = {chave} do 04_eda.py', f'{int(q[col])} / {int(ind[chave])}', int(q[col]) == int(ind[chave])))
    pond = ler(pasta, 'ponderado')
    if f_ind.exists() and pond is not None:
        media = pond.media_global.iloc[0]
        ref = float(pd.read_csv(f_ind).set_index('indicador')['valor']['rating_media'])
        res.append(('média global = rating_media do 04_eda.py', f'{media:.3f} / {ref:.3f}', round(media, 3) == ref))
    anual = ler(pasta, 'anual')
    if anual is not None and qual is not None:
        soma = int(anual.num_ratings.sum())
        res.append(('soma de anual.num_ratings = linhas', f'{soma} / {int(qual.linhas.iloc[0])}', soma == int(qual.linhas.iloc[0])))
    return res


def iguais(a, b, tol=1e-6):
    """Compara dois resultados pela posição das colunas (no Athena os nomes saem em minúsculas)."""
    if a.shape != b.shape:
        return False, f'formas diferentes: {a.shape} vs {b.shape}'
    for j in range(a.shape[1]):
        x, y = a.iloc[:, j], b.iloc[:, j]
        if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
            for u, v in zip(x, y):
                if pd.isna(u) and pd.isna(v):
                    continue
                if pd.isna(u) or pd.isna(v) or not math.isclose(u, v, rel_tol=tol, abs_tol=tol):
                    return False, f'coluna {a.columns[j]}: {u} vs {v}'
        elif not (x.astype(str).values == y.astype(str).values).all():
            return False, f'coluna {a.columns[j]} difere'
    return True, ''


# ---------------------------------------------------------------------------
def escrever_relatorio(pasta, ds, origem, resumo, verif, comparacao, segundos):
    """Escreve analises_relatorio.md com as fontes, as verificações e o resumo das queries."""
    L = [f'# Análises · MovieLens {ds}', '',
         f'Gerado por `scripts/05_analises.py` em {segundos:.1f} s (sessão DuckDB em UTC).', '',
         '## Fontes', '']
    for t, o in origem.items():
        L.append(f'- **{t}** — `{o}`')
    L += ['', '## Verificações', '', '| Verificação | Valor | OK |', '|---|---|---|']
    for nome, valor, ok in verif:
        L.append(f"| {nome} | {valor} | {'sim' if ok else '**NÃO**'} |")
    L += ['', '## Queries', '', '| Query | Linhas | Segundos | CSV |', '|---|---:|---:|---|']
    for r in resumo:
        L.append(f"| {r['query']} | {r['linhas']} | {r['segundos']:.3f} | `{r['query']}.csv` |")
    if comparacao:
        L += ['', '## Versões Athena emuladas no DuckDB', '',
              'Emulação: divisão inteira entre inteiros e macros para `from_unixtime`, `date_format`, '
              '`sequence` e `approx_percentile`. Valida a lógica, não a sintaxe do Trino.', '',
              '| Query | Linhas DuckDB | Linhas Athena (emul.) | Iguais | Nota |', '|---|---:|---:|---|---|']
        for c in comparacao:
            L.append(f"| {c['query']} | {c['linhas_duckdb']} | {c['linhas_athena']} | {c['iguais']} | {c['nota']} |")
    (pasta / 'analises_relatorio.md').write_text('\n'.join(L) + '\n', encoding='utf-8')


def main():
    """Corre as queries de sql/analise/, verifica os resultados e escreve o relatório."""
    args = parse_args()
    cfg = load_config(args.dataset)
    ds = cfg['dataset']
    pasta = ROOT / 'results' / ds / 'analises'
    pasta.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()

    con, origem = ligar(cfg, args.fonte)
    print(f'[analises] dataset={ds} fonte={args.fonte}')
    resumo = []
    for nome, ficheiro in listar_queries(PASTA_SQL, args.queries).items():
        linhas, seg = correr(con, nome, ficheiro, FONTES_DUCKDB, pasta / f'{nome}.csv')
        resumo.append({'query': nome, 'linhas': linhas, 'segundos': round(seg, 4), 'fonte': args.fonte})
        print(f'  {nome:24} {seg * 1000:9.1f} ms  {linhas:>9,} linhas'.replace(',', ' '))
    con.close()
    pd.DataFrame(resumo).to_csv(pasta / 'analises_resumo.csv', index=False)

    comparacao = []
    if args.emular_athena:
        destino = pasta / 'athena_emulado'
        destino.mkdir(exist_ok=True)
        con, _ = ligar(cfg, args.fonte)
        preparar_emulacao(con)
        print('[analises] versões Athena emuladas no DuckDB')
        for nome, ficheiro in listar_queries(PASTA_SQL_ATHENA, args.queries).items():
            linhas, seg = correr(con, nome, ficheiro, FONTES_ATHENA, destino / f'{nome}.csv')
            a = ler(pasta, nome)
            b = ler(destino, nome)
            if a is None:
                ok, nota = False, 'sem versão DuckDB'
            else:
                ok, nota = iguais(a, b)
            comparacao.append({'query': nome, 'linhas_duckdb': None if a is None else len(a),
                               'linhas_athena': linhas, 'iguais': 'sim' if ok else 'NÃO', 'nota': nota})
            print(f"  {nome:24} {linhas:>9,} linhas  iguais: {'sim' if ok else 'NÃO ' + nota}".replace(',', ' '))
        con.close()
        pd.DataFrame(comparacao).to_csv(destino / 'comparacao.csv', index=False)

    verif = verificar(pasta, ds)
    segundos = time.perf_counter() - t0
    escrever_relatorio(pasta, ds, origem, resumo, verif, comparacao, segundos)
    for nome, valor, ok in verif:
        print(f"  [{'ok' if ok else 'FALHA'}] {nome}: {valor}")
    print(f'[analises] {len(resumo)} queries em {pasta.relative_to(ROOT)} ({segundos:.1f} s)')

    falhas = [v for v in verif if not v[2]]
    diferentes = [c for c in comparacao if c['iguais'] != 'sim']
    if falhas or diferentes:
        raise SystemExit(f'[analises] {len(falhas)} verificações falharam e {len(diferentes)} versões '
                         'Athena emuladas diferem (ver analises_relatorio.md)')


if __name__ == '__main__':
    main()
