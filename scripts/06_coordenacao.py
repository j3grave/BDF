"""
06_coordenacao.py - Teste de coordenação entre contas (Bloco 6 da Fase 2, a validar com o Luís).

Objetivo:
    Procurar a assinatura de contas coordenadas: o MESMO filme recebe a MESMA nota extrema de
    VÁRIOS utilizadores distintos na MESMA hora, e essa nota está longe da média do filme.
    Uma "rajada" é um grupo (filme, lado, hora UTC) com:
      - pelo menos U utilizadores distintos, U em {3, 5, 10, 20}, cuja nota está no lado
        (ex.: nota = 0,5) e a pelo menos D da média do filme, D em {1,5; 2}
        (média sobre todas as avaliações do filme).
    A hora é a hora de relógio em UTC (floor(timestamp / 3600)), não uma janela deslizante.

    Lados (grupos de notas extremas) por dataset:
      - 1M (escala inteira): 1 e 5.
      - small e 32M: análise principal com 0,5 e 5,0; análise de sensibilidade com <= 1,0
        (0,5 e 1,0 juntos, porque o 0,5 é pouco usado e um ataque de "afundar" pode usar 1,0)
        e 5,0. O lado 5,0 é o mesmo nas duas análises e só se conta uma vez.

    Linha de base (obrigatória): os timestamps são permutados DENTRO de cada filme. Cada filme
    mantém exatamente o mesmo conjunto de timestamps (quantas avaliações teve em cada hora), mas
    a ligação entre a avaliação (utilizador e nota) e o momento é quebrada. O script verifica
    isto na primeira permutação para todos os filmes e mostra um filme como exemplo.
    Para cada comparação (análise, notas, U, D): n.º real, média, desvio-padrão, p95 e máximo nas
    permutações, z = (real - média) / desvio-padrão e o valor-p empírico
    (1 + n.º de permutações >= real) / (1 + R). Bonferroni: limiar 0,05 / n.º de comparações;
    uma comparação só conta como sinal se o valor-p ficar abaixo desse limiar.

    As 10 rajadas reais mais fortes da análise principal (mais utilizadores; desempate pelo
    desvio) são caracterizadas conta a conta: antiguidade, n.º de avaliações, se a rajada caiu
    nas primeiras 24 h da conta (registo), se a conta voltou a avaliar, Jaccard entre as contas
    (filmes em comum) e se a rajada coincide com a "estreia" do filme no dataset (primeira
    avaliação). Também a distribuição das rajadas por ano, real vs permutações, ao lado do n.º
    de contas novas (primeira avaliação) nesse ano.

Entradas:
    data/<dataset>/parquet/ratings.parquet e movies.parquet
    results/<dataset>/analises/10_flag_bots.csv (opcional: classificação das contas do Bloco 5)

Saídas (em results/<dataset>/bots_coordenacao/):
    rajadas.csv                  rajadas reais com U >= 3 e D >= 1,5, em todos os lados
    linha_base.csv               n.º de rajadas em cada permutação, por comparação
    teste.csv                    real vs linha de base, com valor-p, z e Bonferroni
    rajadas_por_ano.csv          rajadas por ano (análise principal, U >= 3, D >= 1,5) e contas novas
    verificacao_permutacao.csv   um filme antes e depois da permutação 1
    top10_rajadas.csv            as 10 rajadas mais fortes, com o resumo das contas
    top10_contas.csv             uma linha por conta de cada uma dessas rajadas
    coordenacao_relatorio.md     relatório (inclui tempos e verificação da permutação)

Como correr:
    python scripts/06_coordenacao.py --dataset 1m
    python scripts/06_coordenacao.py --dataset 32m --repeticoes 200 --memoria 12GB

Notas:
    - A permutação ordena as avaliações de cada filme por hash(userId, movieId, semente), com
      uma semente diferente por repetição (1..R), e dá-lhes os timestamps desse filme por ordem.
      É o equivalente a setseed + random(), mas reprodutível com várias threads.
    - A sessão DuckDB fica em UTC; as horas e os dias vêm de epoch_ms (sem fuso).
    - memory_limit (--memoria) e uma pasta temporária em data/<dataset>/duckdb_tmp/ para o DuckDB
      poder escrever para disco se a memória não chegar (apagada no fim).
"""
import argparse
import shutil
import time

import duckdb
import pandas as pd

from common import DATASETS, ROOT, load_config

# Lados: nome -> condição SQL sobre rating
LADOS = {
    '1m':    {'1': 'rating = 1', '5': 'rating = 5'},
    'small': {'0.5': 'rating = 0.5', '<=1.0': 'rating <= 1.0', '5.0': 'rating = 5.0'},
    '32m':   {'0.5': 'rating = 0.5', '<=1.0': 'rating <= 1.0', '5.0': 'rating = 5.0'},
}
# Comparações: (análise, rótulo das notas, lados que entram). Cada lado conta uma vez.
COMPARACOES = {
    '1m': [('principal', '1', ['1']), ('principal', '5', ['5']), ('principal', '1 e 5', ['1', '5'])],
    '32m': [('principal', '0.5', ['0.5']), ('principal', '5.0', ['5.0']),
            ('principal', '0.5 e 5.0', ['0.5', '5.0']),
            ('sensibilidade', '<=1.0', ['<=1.0']), ('sensibilidade', '<=1.0 e 5.0', ['<=1.0', '5.0'])],
}
COMPARACOES['small'] = COMPARACOES['32m']
LIMIARES_UTILIZADORES = (3, 5, 10, 20)
LIMIARES_DESVIO = (1.5, 2.0)
ALFA = 0.05
TOP = 10
AMOSTRA_JACCARD = 1000   # contas ao acaso para o Jaccard de referência entre pares quaisquer


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dataset', choices=list(DATASETS), help='sobrepõe o valor de config.yaml')
    ap.add_argument('--repeticoes', type=int, default=20,
                    help='n.º de permutações da linha de base (20 por omissão)')
    ap.add_argument('--memoria', default='12GB', help='memory_limit do DuckDB (12GB por omissão)')
    return ap.parse_args()


def ligar(cfg, memoria):
    """Ligação DuckDB em UTC com a tabela r (userId, movieId, rating, ts), a view movies e filme."""
    con = duckdb.connect()
    con.execute("SET TimeZone = 'UTC'")
    con.execute(f"SET memory_limit = '{memoria}'")
    tmp = cfg['paths']['base'] / 'duckdb_tmp'
    con.execute(f"SET temp_directory = '{tmp.as_posix()}'")
    pasta = cfg['paths']['parquet']
    for t in ('ratings', 'movies'):
        if not (pasta / f'{t}.parquet').exists():
            raise SystemExit(f'Não encontrei {(pasta / f"{t}.parquet").relative_to(ROOT)}. '
                             'Corre primeiro run_pipeline.py --steps ingest parquet.')
    con.execute(f"""CREATE TABLE r AS
                    SELECT userId, movieId, rating, timestamp AS ts
                    FROM read_parquet('{(pasta / 'ratings.parquet').as_posix()}')""")
    con.execute(f"CREATE VIEW movies AS SELECT * FROM read_parquet('{(pasta / 'movies.parquet').as_posix()}')")
    # Média e "estreia" (primeira avaliação no dataset) de cada filme: não mudam com a permutação
    con.execute("""CREATE TABLE filme AS
                   SELECT movieId, AVG(rating) AS media_filme, COUNT(*) AS avaliacoes_filme,
                          MIN(ts) AS estreia_ts
                   FROM r GROUP BY movieId""")
    return con, tmp


def sql_rajadas(tabela, lados):
    """Grupos (filme, lado, hora) com >= 3 utilizadores a >= 1,5 da média (os mínimos testados).
    u_15 e u_2: utilizadores distintos do grupo a >= 1,5 e a >= 2 da média do filme."""
    partes = [f"""SELECT t.userId, t.movieId, t.rating, t.ts, '{nome}' AS lado,
                         abs(t.rating - f.media_filme) AS desvio, f.media_filme
                  FROM {tabela} t JOIN filme f USING (movieId)
                  WHERE t.{cond} AND abs(t.rating - f.media_filme) >= {min(LIMIARES_DESVIO)}"""
              for nome, cond in lados.items()]
    return f"""
        WITH ext AS ({' UNION ALL '.join(partes)})
        SELECT movieId, lado, ts // 3600 AS hora,
               COUNT(DISTINCT userId)                                AS u_15,
               COUNT(DISTINCT userId) FILTER (WHERE desvio >= 2)     AS u_2,
               MIN(rating) AS nota_min, MAX(rating) AS nota_max,
               MAX(desvio) AS desvio_max, MAX(media_filme) AS media_filme
        FROM ext
        GROUP BY movieId, lado, ts // 3600
        HAVING COUNT(DISTINCT userId) >= {min(LIMIARES_UTILIZADORES)}"""


def contar(df, comparacoes):
    """N.º de rajadas por comparação (análise, notas, U, D)."""
    linhas = []
    for analise, notas, lados in comparacoes:
        sub = df[df.lado.isin(lados)]
        for u in LIMIARES_UTILIZADORES:
            for d in LIMIARES_DESVIO:
                col = sub.u_15 if d == 1.5 else sub.u_2
                linhas.append({'analise': analise, 'notas': notas, 'min_utilizadores': u,
                               'min_desvio': d, 'rajadas': int((col >= u).sum())})
    return pd.DataFrame(linhas)


def por_ano(df, lados):
    """Rajadas por ano (U >= 3, D >= 1,5) nos lados indicados."""
    sub = df[df.lado.isin(lados)]
    return pd.to_datetime(sub.hora * 3600, unit='s').dt.year.value_counts()


def permutar(con, semente):
    """Tabela p: cada avaliação do filme recebe um dos timestamps desse filme, baralhados.
    a: avaliações do filme por ordem de hash(userId, movieId, semente) -> posição rn;
    b: timestamps do filme por ordem cronológica -> posição rn;
    a avaliação na posição k recebe o k-ésimo timestamp. O conjunto de timestamps do filme
    fica igual; muda qual o utilizador (e a nota) que fica em cada momento."""
    con.execute(f"""
        CREATE OR REPLACE TABLE p AS
        WITH a AS (SELECT userId, movieId, rating,
                          row_number() OVER (PARTITION BY movieId
                                             ORDER BY hash(userId, movieId, {semente}), userId) AS rn
                   FROM r),
             b AS (SELECT movieId, ts,
                          row_number() OVER (PARTITION BY movieId ORDER BY ts, userId) AS rn
                   FROM r)
        SELECT a.userId, a.movieId, a.rating, b.ts
        FROM a JOIN b USING (movieId, rn)""")


def verificar_permutacao(con):
    """Verifica, em todos os filmes, que p tem as mesmas avaliações e o mesmo conjunto de
    timestamps que r, e que os timestamps mudaram de avaliação. Devolve (resumo, exemplo)."""
    v = con.execute("""
        WITH a AS (SELECT movieId, COUNT(*) AS n, SUM(hash(ts)) AS h_ts, MIN(ts) AS mn, MAX(ts) AS mx,
                          SUM(hash(userId, rating)) AS h_av FROM r GROUP BY movieId),
             b AS (SELECT movieId, COUNT(*) AS n, SUM(hash(ts)) AS h_ts, MIN(ts) AS mn, MAX(ts) AS mx,
                          SUM(hash(userId, rating)) AS h_av FROM p GROUP BY movieId)
        SELECT COUNT(*) AS filmes,
               count_if(a.n <> b.n OR a.h_ts <> b.h_ts OR a.mn <> b.mn OR a.mx <> b.mx) AS filmes_ts_diferentes,
               count_if(a.h_av <> b.h_av) AS filmes_avaliacoes_diferentes
        FROM a FULL JOIN b USING (movieId)""").fetchone()
    mudou = con.execute("""
        SELECT COUNT(*), count_if(r.ts <> p.ts),
               count_if(r.ts // 3600 <> p.ts // 3600)
        FROM r JOIN p USING (userId, movieId)""").fetchone()
    n_r = con.execute('SELECT COUNT(*) FROM r').fetchone()[0]
    resumo = {'filmes': v[0], 'filmes_ts_diferentes': v[1], 'filmes_avaliacoes_diferentes': v[2],
              'avaliacoes': n_r, 'pares_juntos': mudou[0], 'ts_mudou': mudou[1], 'hora_mudou': mudou[2]}
    if v[1] or v[2] or mudou[0] != n_r:
        raise SystemExit(f'Permutação inválida: {resumo}')
    # Exemplo: o filme com 6 avaliações e menor movieId
    exemplo = con.execute("""
        WITH f AS (SELECT MIN(movieId) AS movieId FROM filme WHERE avaliacoes_filme = 6)
        SELECT r.movieId, r.userId, r.rating,
               strftime(epoch_ms(r.ts * 1000), '%Y-%m-%d %H:%M:%S') AS ts_original,
               strftime(epoch_ms(p.ts * 1000), '%Y-%m-%d %H:%M:%S') AS ts_permutado
        FROM r JOIN f USING (movieId) JOIN p USING (userId, movieId)
        ORDER BY r.ts, r.userId""").df()
    return resumo, exemplo


def caracterizar(con, top):
    """Uma linha por conta de cada rajada do top, e o Jaccard entre as contas de cada rajada."""
    con.register('top_df', top[['rajada', 'movieId', 'lado_cond', 'hora']])
    membros_sql = """SELECT DISTINCT t.rajada, r.userId, r.ts
                     FROM top_df t JOIN r ON r.movieId = t.movieId AND r.ts // 3600 = t.hora
                     JOIN filme f ON f.movieId = r.movieId
                     WHERE ((t.lado_cond = 'baixo' AND r.rating = (SELECT MIN(rating) FROM r))
                         OR (t.lado_cond = 'alto' AND r.rating = (SELECT MAX(rating) FROM r)))
                       AND abs(r.rating - f.media_filme) >= 1.5"""
    contas = con.execute(f"""
        WITH membros AS ({membros_sql}),
             u AS (SELECT userId, COUNT(*) AS avaliacoes_conta, MIN(ts) AS primeiro_ts, MAX(ts) AS ultimo_ts
                   FROM r WHERE userId IN (SELECT userId FROM membros) GROUP BY userId),
             depois AS (SELECT m.rajada, m.userId, COUNT(x.ts) AS avaliacoes_depois
                        FROM membros m LEFT JOIN r x ON x.userId = m.userId AND x.ts > m.ts
                        GROUP BY m.rajada, m.userId)
        SELECT m.rajada, m.userId,
               strftime(epoch_ms(m.ts * 1000), '%Y-%m-%d %H:%M:%S')     AS momento,
               u.avaliacoes_conta,
               strftime(epoch_ms(u.primeiro_ts * 1000), '%Y-%m-%d')     AS primeiro_dia,
               ROUND((m.ts - u.primeiro_ts) / 86400.0, 2)               AS antiguidade_dias,
               m.ts - u.primeiro_ts < 86400                             AS no_registo,
               d.avaliacoes_depois,
               ROUND((u.ultimo_ts - m.ts) / 86400.0, 2)                 AS dias_ate_ultima,
               u.ultimo_ts - m.ts > 86400                               AS voltou_depois_24h
        FROM membros m JOIN u USING (userId) JOIN depois d USING (rajada, userId)
        ORDER BY m.rajada, m.ts, m.userId""").df()
    jac = con.execute(f"""
        WITH membros AS (SELECT DISTINCT rajada, userId FROM ({membros_sql})),
             ru AS (SELECT userId, movieId FROM r WHERE userId IN (SELECT userId FROM membros)),
             n AS (SELECT userId, COUNT(*) AS n FROM ru GROUP BY userId),
             pares AS (SELECT a.rajada, a.userId AS u1, b.userId AS u2
                       FROM membros a JOIN membros b ON a.rajada = b.rajada AND a.userId < b.userId),
             comuns AS (SELECT p.rajada, p.u1, p.u2, COUNT(*) AS comuns
                        FROM pares p JOIN ru x ON x.userId = p.u1 JOIN ru y ON y.userId = p.u2 AND y.movieId = x.movieId
                        GROUP BY p.rajada, p.u1, p.u2)
        SELECT p.rajada,
               AVG(COALESCE(c.comuns, 0) / (n1.n + n2.n - COALESCE(c.comuns, 0)))  AS jaccard_medio,
               MAX(COALESCE(c.comuns, 0) / (n1.n + n2.n - COALESCE(c.comuns, 0)))  AS jaccard_max
        FROM pares p
        LEFT JOIN comuns c USING (rajada, u1, u2)
        JOIN n n1 ON n1.userId = p.u1 JOIN n n2 ON n2.userId = p.u2
        GROUP BY p.rajada""").df()
    return contas, jac


def jaccard_referencia(con):
    """Jaccard médio entre pares de contas quaisquer (amostra fixa de contas), para comparação."""
    return con.execute(f"""
        WITH amostra AS (SELECT userId FROM (SELECT DISTINCT userId FROM r)
                         ORDER BY hash(userId, 42) LIMIT {AMOSTRA_JACCARD}),
             ra AS (SELECT r.userId, r.movieId FROM r JOIN amostra USING (userId)),
             n AS (SELECT userId, COUNT(*) AS n FROM ra GROUP BY userId),
             comuns AS (SELECT x.userId AS u1, y.userId AS u2, COUNT(*) AS comuns
                        FROM ra x JOIN ra y ON x.movieId = y.movieId AND x.userId < y.userId
                        GROUP BY 1, 2),
             pares AS (SELECT a.userId AS u1, b.userId AS u2, a.n + b.n AS soma
                       FROM n a JOIN n b ON a.userId < b.userId)
        SELECT AVG(COALESCE(c.comuns, 0) / (p.soma - COALESCE(c.comuns, 0))),
               quantile_cont(COALESCE(c.comuns, 0) / (p.soma - COALESCE(c.comuns, 0)), 0.95)
        FROM pares p LEFT JOIN comuns c USING (u1, u2)""").fetchone()


def tabela_md(df):
    cols = list(df.columns)
    linhas = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    for _, row in df.iterrows():
        linhas.append('| ' + ' | '.join('' if pd.isna(v) else str(v) for v in row) + ' |')
    return '\n'.join(linhas)


def main():
    args = parse_args()
    cfg = load_config(args.dataset)
    ds = cfg['dataset']
    lados, comparacoes = LADOS[ds], COMPARACOES[ds]
    principal = [l for a, n, ls in comparacoes if a == 'principal' for l in ls]
    principal = list(dict.fromkeys(principal))
    R = args.repeticoes
    saida = cfg['paths']['results'] / ds / 'bots_coordenacao'
    saida.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    con, tmp = ligar(cfg, args.memoria)
    t_carga = time.perf_counter() - t0

    # 1. Rajadas reais
    real_df = con.execute(sql_rajadas('r', lados)).df()
    real = contar(real_df, comparacoes)
    print(f'[{ds}] rajadas reais (U>=3, D>=1,5, todos os lados): {len(real_df)}')

    # 2. Linha de base: R permutações dos timestamps dentro de cada filme
    base, anos_base, tempos = [], [], []
    verif = exemplo = None
    for semente in range(1, R + 1):
        tp = time.perf_counter()
        permutar(con, semente)
        if semente == 1:
            verif, exemplo = verificar_permutacao(con)
        pdf = con.execute(sql_rajadas('p', lados)).df()
        c = contar(pdf, comparacoes)
        c.insert(0, 'repeticao', semente)
        base.append(c)
        anos_base.append(por_ano(pdf, principal).rename(semente))
        tempos.append(time.perf_counter() - tp)
        if semente == 1 or semente % 10 == 0:
            print(f'  permutação {semente}/{R} ({tempos[-1]:.1f} s)', flush=True)
    base = pd.concat(base, ignore_index=True)
    chave = ['analise', 'notas', 'min_utilizadores', 'min_desvio']
    agg = base.groupby(chave, sort=False).rajadas.agg(
        media='mean', desvio_padrao='std', p95=lambda s: s.quantile(0.95), maximo='max').reset_index()
    teste = real.rename(columns={'rajadas': 'real'}).merge(agg, on=chave)
    ge = (base.merge(real.rename(columns={'rajadas': 'real'}), on=chave)
              .assign(ge=lambda d: d.rajadas >= d.real)
              .groupby(chave, sort=False).ge.sum().rename('perm_ge_real').reset_index())
    teste = teste.merge(ge, on=chave)
    m = len(teste)
    alfa_bonf = ALFA / m
    teste['valor_p'] = ((1 + teste.perm_ge_real) / (1 + R)).round(4)
    teste['z'] = ((teste.real - teste.media) / teste.desvio_padrao.where(teste.desvio_padrao > 0)).round(2)
    teste['sinal_bonferroni'] = teste.valor_p < alfa_bonf
    teste['razao_real_media'] = (teste.real / teste.media.where(teste.media > 0)).round(2)
    for col in ('media', 'desvio_padrao', 'p95'):
        teste[col] = teste[col].round(2)

    # 3. Rajadas por ano (análise principal, U >= 3, D >= 1,5) e contas novas por ano
    anos = pd.DataFrame({'rajadas_reais': por_ano(real_df, principal)})
    anos_b = pd.concat(anos_base, axis=1).fillna(0)
    anos = anos.join(pd.DataFrame({'media_permutacoes': anos_b.mean(axis=1).round(2),
                                   'p95_permutacoes': anos_b.quantile(0.95, axis=1).round(2)}), how='outer')
    novas = con.execute("""SELECT year(epoch_ms(MIN(ts) * 1000)) AS ano, COUNT(*) AS n
                           FROM r GROUP BY userId""").df().groupby('ano').size().rename('contas_novas')
    anos = anos.join(novas, how='outer').fillna(0).sort_index()
    anos.index.name = 'ano'
    anos = anos.astype({'rajadas_reais': int, 'contas_novas': int}).reset_index()
    anos.to_csv(saida / 'rajadas_por_ano.csv', index=False)

    # 4. Rajadas reais: detalhe e top 10 da análise principal
    con.register('real_df', real_df)
    rajadas = con.execute("""
        SELECT d.*, fm.title, fm.avaliacoes_filme, fm.estreia_ts, h.avaliacoes_filme_hora
        FROM real_df d
        JOIN (SELECT f.*, m.title FROM filme f JOIN movies m USING (movieId)) fm USING (movieId)
        JOIN (SELECT r.movieId, r.ts // 3600 AS hora, COUNT(*) AS avaliacoes_filme_hora
              FROM r SEMI JOIN (SELECT DISTINCT movieId, hora FROM real_df) k
                   ON r.movieId = k.movieId AND r.ts // 3600 = k.hora
              GROUP BY 1, 2) h USING (movieId, hora)""").df()
    rajadas = rajadas.sort_values(['u_15', 'desvio_max', 'movieId', 'hora'],
                                  ascending=[False, False, True, True]).reset_index(drop=True)
    rajadas['inicio_hora_utc'] = pd.to_datetime(rajadas.hora * 3600, unit='s').dt.strftime('%Y-%m-%d %H:00')
    rajadas['pct_da_hora'] = (100 * rajadas.u_15 / rajadas.avaliacoes_filme_hora).round(1)
    rajadas['dias_desde_estreia_dataset'] = ((rajadas.hora * 3600 - rajadas.estreia_ts) / 86400).round(2)
    rajadas['ano_titulo'] = rajadas.title.str.extract(r'\((\d{4})\)\s*$')[0]
    rajadas['desvio_max'] = rajadas.desvio_max.round(3)
    rajadas['media_filme'] = rajadas.media_filme.round(3)
    cols = ['movieId', 'title', 'ano_titulo', 'lado', 'inicio_hora_utc', 'u_15', 'u_2',
            'avaliacoes_filme_hora', 'pct_da_hora', 'media_filme', 'desvio_max', 'avaliacoes_filme',
            'dias_desde_estreia_dataset']
    rajadas[cols].to_csv(saida / 'rajadas.csv', index=False)

    top = rajadas[rajadas.lado.isin(principal)].head(TOP).copy()
    top.insert(0, 'rajada', range(1, len(top) + 1))
    # lado baixo = nota mínima da escala (0,5 ou 1); alto = 5
    top['lado_cond'] = ['alto' if l in ('5', '5.0') else 'baixo' for l in top.lado]
    contas, jac = caracterizar(con, top)
    bots_csv = cfg['paths']['results'] / ds / 'analises' / '10_flag_bots.csv'
    if bots_csv.exists():
        bots = pd.read_csv(bots_csv, usecols=['userId', 'classificacao'])
        contas = contas.merge(bots, on='userId', how='left')
    contas.to_csv(saida / 'top10_contas.csv', index=False)

    resumo = contas.groupby('rajada').agg(
        antiguidade_mediana_dias=('antiguidade_dias', 'median'),
        pct_no_registo=('no_registo', lambda s: round(100 * s.mean(), 1)),
        avaliacoes_conta_mediana=('avaliacoes_conta', 'median'),
        pct_voltaram_24h=('voltou_depois_24h', lambda s: round(100 * s.mean(), 1)),
        **({'suspeitos_bloco5': ('classificacao', lambda s: int(s.fillna('').str.startswith('suspeito').sum()))}
           if 'classificacao' in contas else {})).reset_index()
    top = top.merge(resumo, on='rajada').merge(jac, on='rajada')
    top['jaccard_medio'] = top.jaccard_medio.round(3)
    top['jaccard_max'] = top.jaccard_max.round(3)
    top['coincide_estreia_7d'] = top.dias_desde_estreia_dataset.abs() <= 7
    cols_top = ['rajada'] + cols + list(resumo.columns[1:]) + ['jaccard_medio', 'jaccard_max', 'coincide_estreia_7d']
    top = top[cols_top]
    top.to_csv(saida / 'top10_rajadas.csv', index=False)
    jac_ref = jaccard_referencia(con)

    base.to_csv(saida / 'linha_base.csv', index=False)
    teste.to_csv(saida / 'teste.csv', index=False)
    exemplo.to_csv(saida / 'verificacao_permutacao.csv', index=False)
    con.close()
    shutil.rmtree(tmp, ignore_errors=True)

    # 5. Relatório
    segundos = time.perf_counter() - t0
    p_min = 1 / (1 + R)
    md = [f'# Coordenação entre contas · MovieLens {ds}', '',
          f'Gerado por `scripts/06_coordenacao.py` (sessão DuckDB em UTC, memory_limit {args.memoria}, '
          'fonte Parquet). **A validar com o Luís.**', '',
          '## Tempos', '',
          f'- Total: {segundos:.1f} s ({segundos / 60:.1f} min).',
          f'- Carga dos dados: {t_carga:.1f} s.',
          f'- Permutações: {R}, {sum(tempos):.1f} s no total, {sum(tempos) / R:.2f} s em média '
          f'(a primeira inclui a verificação: {tempos[0]:.1f} s).', '',
          '## Definição', '',
          f'Rajada: (filme, lado, hora UTC) com >= U utilizadores distintos cuja nota está no lado e a >= D da '
          f'média do filme. Lados: {", ".join(f"`{k}` ({v})" for k, v in lados.items())}. '
          f'U em {{{", ".join(map(str, LIMIARES_UTILIZADORES))}}}, D em {{{", ".join(f"{d:g}" for d in LIMIARES_DESVIO)}}}.', '',
          f'Linha de base: {R} permutações dos timestamps dentro de cada filme (sementes 1..{R}).', '',
          '## Verificação da permutação (semente 1)', '',
          f'- Filmes: {verif["filmes"]}; com conjunto de timestamps diferente: {verif["filmes_ts_diferentes"]}; '
          f'com avaliações (utilizador, nota) diferentes: {verif["filmes_avaliacoes_diferentes"]}.',
          f'- Avaliações: {verif["avaliacoes"]}; com timestamp diferente do original: {verif["ts_mudou"]} '
          f'({100 * verif["ts_mudou"] / verif["avaliacoes"]:.1f}%); com hora diferente: {verif["hora_mudou"]} '
          f'({100 * verif["hora_mudou"] / verif["avaliacoes"]:.1f}%).', '',
          f'Exemplo (filme {exemplo.movieId.iloc[0]}, 6 avaliações):', '',
          tabela_md(exemplo), '',
          '## Real vs linha de base', '',
          f'Comparações: {m}. Bonferroni: limiar {ALFA} / {m} = {alfa_bonf:.5f}. '
          f'Menor valor-p empírico possível com {R} permutações: 1 / {R + 1} = {p_min:.5f}.'
          + (' **Com este n.º de permutações nenhuma comparação pode passar o limiar corrigido**; '
             f'seriam precisas pelo menos {int(m / ALFA)} permutações. O z é dado como informação complementar.'
             if p_min >= alfa_bonf else ''), '',
          tabela_md(teste[chave + ['real', 'media', 'desvio_padrao', 'p95', 'maximo', 'razao_real_media',
                                   'z', 'valor_p', 'sinal_bonferroni']]), '',
          f'## Rajadas por ano (análise principal, U >= 3, D >= 1,5)', '',
          tabela_md(anos), '',
          f'## As {TOP} rajadas reais mais fortes (análise principal)', '',
          tabela_md(top[['rajada', 'title', 'lado', 'inicio_hora_utc', 'u_15', 'avaliacoes_filme_hora',
                         'pct_da_hora', 'desvio_max', 'dias_desde_estreia_dataset', 'antiguidade_mediana_dias',
                         'pct_no_registo', 'avaliacoes_conta_mediana', 'pct_voltaram_24h', 'jaccard_medio',
                         'jaccard_max'] + (['suspeitos_bloco5'] if 'suspeitos_bloco5' in top else [])]), '',
          f'Jaccard de referência entre pares de contas quaisquer ({AMOSTRA_JACCARD} contas ao acaso): '
          f'média {jac_ref[0]:.3f}, p95 {jac_ref[1]:.3f}.', '']
    (saida / 'coordenacao_relatorio.md').write_text('\n'.join(md), encoding='utf-8')
    print(f'Gravado em {saida.relative_to(ROOT)} ({segundos:.1f} s)')


if __name__ == '__main__':
    main()
