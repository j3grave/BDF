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
    sql/analise/*.sql                    queries com os marcadores ${ratings}, ${movies} (e ${flag_bots})
    data/<dataset>/parquet/              Parquet sem partição (--fonte parquet, por omissão)
    data/<dataset>/csv/                  CSV normalizados (--fonte csv)
    sql/athena/analise/*.sql             versões Athena (só com --emular-athena)

Saídas (em results/<dataset>/analises/):
    <query>.csv                          resultado de cada query
    10_flag_bots_referencia.csv          só no small: os 5 utilizadores de referência da deteção
                                         de bots, com a classificação esperada, a obtida e a justificação
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
    - ${flag_bots} é a tabela por utilizador de 10_flag_bots.sql. O script corre essa query
      primeiro e guarda-a numa tabela temporária; no Athena é um CTAS em Parquet.
    - A emulação do Athena valida a lógica e os resultados das versões Athena (com divisão
      inteira entre inteiros, como no Trino, e macros para from_unixtime, date_format,
      sequence e approx_percentile). NÃO valida a sintaxe do Trino: isso só na AWS.
"""
import argparse
import math
import re
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
MATERIALIZAR = {'10_flag_bots': 'flag_bots'}
DEPENDENCIAS = {'eventos': ['10_flag_bots'], '10_flag_bots_calibracao': ['10_flag_bots']}


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
    'flag_bots': 'flag_bots',
}

# Na emulação do Athena, ${ratings} é escrito como no athena_benchmark.py para as tabelas sem
# partição: year a partir de from_unixtime (UTC no Trino; aqui, a macro abaixo).
FONTES_ATHENA = {
    'ratings': '(SELECT x.*, year(from_unixtime(x."timestamp")) AS year FROM ratings_base AS x)',
    'movies': 'movies',
    'flag_bots': 'flag_bots',
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


# Padrões que a emulação não reproduz: no Trino, uma divisão com um literal decimal
# (100.0 * x / y, x * 1.0 / y) fica com a escala do literal (1 casa decimal), enquanto no DuckDB
# dá um número real. Nas versões Athena usa-se CAST(... AS double); esta verificação apanha
# esquecimentos.
DECIMAL_EM_CONTA = re.compile(r'(\d+\.\d+\s*[*/])|([*/]\s*\d+\.\d+)')


def avisos_trino(texto):
    """Linhas (sem comentários) de uma query Athena com um literal decimal numa multiplicação ou divisão."""
    avisos = []
    for linha in texto.splitlines():
        codigo = linha.split('--')[0]
        if DECIMAL_EM_CONTA.search(codigo):
            avisos.append(codigo.strip())
    return avisos


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
        # Tabela temporária para as queries que dependem desta (ex.: ${flag_bots} em eventos)
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


# Utilizadores de referência da deteção de bots no small: (classificação esperada, porquê).
REFERENCIA_BOTS = {
    'small': {
        257: ('sem sinais', '20 avaliações em 11 min no registo: não pode ser sinalizado'),
        7: ('sem sinais', 'uso normal: não pode ser sinalizado'),
        89: ('suspeito (regra B)', '518 avaliações em 23 min no registo, ~2 s cada: candidato'),
        610: ('suspeito (regra A)', '566 avaliações numa hora, ~4 s cada, ~6 meses depois do registo'),
        534: ('submissão em lote', 'muitas avaliações no mesmo segundo (2016): não é bot'),
    },
}


def justificar(r):
    """Texto com os números que levam à classificação de um utilizador (linha de 10_flag_bots.csv)."""
    def inteiro(x):
        return '-' if pd.isna(x) else f'{x:.0f}'
    partes = []
    if r.regra_a:
        partes.append(f'regra A: {inteiro(r.max_eventos_10min_apos)} eventos em 10 min depois do registo '
                      f'(limiar p99,9 = {r.limiar_regra_a:.1f}), mediana de {inteiro(r.mediana_intervalo_apos_s)} s entre eventos')
    if r.regra_b:
        partes.append(f'regra B: {r.eventos_registo} eventos nas primeiras 24 h, mediana de '
                      f'{inteiro(r.mediana_intervalo_registo_s)} s entre eventos (>= 100 e <= 2 s)')
    if r.submissao_lote:
        partes.append(f'submissão em lote: até {r.max_avaliacoes_mesmo_segundo} avaliações no mesmo segundo '
                      f'({r.pct_eventos_lote:.0f}% dos eventos com 2 ou mais), primeiro dia {r.primeiro_dia}')
    if not partes:
        partes.append(f'depois do registo: máx. {inteiro(r.max_eventos_10min_apos)} eventos em 10 min (limiar '
                      f'{r.limiar_regra_a:.1f}); registo: {r.eventos_registo} eventos, mediana de '
                      f'{inteiro(r.mediana_intervalo_registo_s)} s (a regra B exige >= 100 eventos e <= 2 s); '
                      f'máx. {r.max_avaliacoes_mesmo_segundo} avaliações no mesmo segundo')
    partes.append(f'sinais complementares: {r.sinais_complementares}/3')
    return '; '.join(partes)


def referencia_bots(pasta, ds):
    """Grava 10_flag_bots_referencia.csv (só datasets com referência) e devolve as verificações."""
    flags = ler(pasta, '10_flag_bots')
    if flags is None or ds not in REFERENCIA_BOTS:
        return []
    linhas, verif = [], []
    for uid, (esperado, porque) in REFERENCIA_BOTS[ds].items():
        r = flags[flags.userId == uid].iloc[0]
        ok = r.classificacao == esperado
        linhas.append({'userId': uid, 'caso': porque, 'esperado': esperado, 'obtido': r.classificacao,
                       'ok': 'sim' if ok else 'NÃO', 'justificacao': justificar(r)})
        verif.append((f'bots: utilizador {uid} = {esperado}', r.classificacao, ok))
    pd.DataFrame(linhas).to_csv(pasta / '10_flag_bots_referencia.csv', index=False)
    return verif


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
    flags, calib = ler(pasta, '10_flag_bots'), ler(pasta, '10_flag_bots_calibracao')
    if flags is not None and calib is not None:
        c = calib.iloc[0]
        L += ['', '## Deteção de bots (10_flag_bots, a validar com o Luís)', '',
              f"- Utilizadores: {int(c.utilizadores)}; suspeitos: {int(c.suspeitos)} ({c.pct_suspeitos:.2f}%) "
              f"= regra A {int(c.regra_a)} + regra B {int(c.regra_b)} (sem repetir quem tem as duas).",
              f"- Submissão em lote (reportada à parte, não é bot): {int(c.submissao_lote)} utilizadores, "
              f"dos quais {int(c.so_submissao_lote)} sem outra classificação.",
              f"- Ritmo sustentado depois do registo (máx. de eventos em 10 min), "
              f"{int(c.utilizadores_com_atividade_apos_registo)} utilizadores: p50 {c.p50:.1f}, p90 {c.p90:.1f}, "
              f"p99 {c.p99:.1f}, p99,5 {c.p99_5:.1f}, p99,9 {c.p99_9:.1f}, máximo {c.maximo:.0f}.",
              f"- Sinalizados pela regra A com o limiar no p99 / p99,5 / p99,9: {int(c.sinalizados_a_p99)} / "
              f"{int(c.sinalizados_a_p99_5)} / {int(c.sinalizados_a_p99_9)} (a query usa o p99,9).", '']
        lote = flags[flags.submissao_lote]
        if len(lote):
            decadas = (lote.primeiro_dia.str[:3] + '0s').value_counts().sort_index()
            L.append('Submissão em lote por década do primeiro rating: '
                     + ', '.join(f'{d}: {n}' for d, n in decadas.items()) + '.')
            L.append('')
        susp = flags[flags.regra_a | flags.regra_b]
        if len(susp):
            L += ['| userId | Classificação | Justificação |', '|---|---|---|']
            for r in susp.itertuples():
                L.append(f'| {r.userId} | {r.classificacao} | {justificar(r)} |')
        ref = ler(pasta, '10_flag_bots_referencia')
        if ref is not None:
            L += ['', '### Utilizadores de referência', '',
                  '| userId | Caso | Esperado | Obtido | OK | Justificação |', '|---|---|---|---|---|---|']
            for r in ref.itertuples():
                L.append(f'| {r.userId} | {r.caso} | {r.esperado} | {r.obtido} | {r.ok} | {r.justificacao} |')
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
            avisos = avisos_trino(ficheiro.read_text(encoding='utf-8'))
            if avisos:
                ok, nota = False, f'literal decimal numa conta (escala no Trino): {avisos[0]}'

            comparacao.append({'query': nome, 'linhas_duckdb': None if a is None else len(a),
                               'linhas_athena': linhas, 'iguais': 'sim' if ok else 'NÃO', 'nota': nota})
            print(f"  {nome:24} {linhas:>9,} linhas  iguais: {'sim' if ok else 'NÃO ' + nota}".replace(',', ' '))
        con.close()
        pd.DataFrame(comparacao).to_csv(destino / 'comparacao.csv', index=False)

    verif = verificar(pasta, ds) + referencia_bots(pasta, ds)
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
