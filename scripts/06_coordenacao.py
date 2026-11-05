"""
06_coordenacao.py - Teste de coordenação entre contas (Bloco 6 da Fase 2, a validar com o Luís).

Objetivo:
    Procurar a assinatura de contas coordenadas: o MESMO filme recebe a MESMA nota extrema de
    VÁRIOS utilizadores distintos na MESMA hora, e essa nota está longe da média do filme.
    Uma "rajada" é um grupo (filme, nota extrema, hora UTC) com:
      - pelo menos U utilizadores distintos, U em {3, 5, 10};
      - |nota - média do filme| >= D, D em {1,5; 2} (média sobre todas as avaliações do filme).
    A hora é a hora de relógio em UTC (floor(timestamp / 3600)), não uma janela deslizante.

    Linha de base (obrigatória): os timestamps são permutados DENTRO de cada filme. Cada filme
    mantém exatamente os mesmos momentos de atividade (quantas avaliações teve em cada hora),
    mas a ligação entre a nota e o momento é quebrada. Se as rajadas reais forem tantas como
    nas permutações, explicam-se pela atividade do filme e não por coordenação.
    Para cada combinação (nota, U, D) reporta-se o n.º real, a média e o p95 nas permutações e o
    valor-p empírico (1 + n.º de permutações >= real) / (1 + n.º de permutações).

    As 10 rajadas reais mais fortes (mais utilizadores; desempate pelo desvio) são
    caracterizadas conta a conta: antiguidade, n.º de avaliações, se a rajada caiu nas primeiras
    24 h da conta (registo), se a conta voltou a avaliar, Jaccard entre as contas (filmes em
    comum) e se a rajada coincide com a "estreia" do filme no dataset (primeira avaliação).

Entradas:
    data/<dataset>/parquet/ratings.parquet e movies.parquet
    results/<dataset>/analises/10_flag_bots.csv (opcional: classificação das contas do Bloco 5)

Saídas (em results/<dataset>/bots_coordenacao/):
    rajadas.csv              todas as rajadas reais com U >= 3 e D >= 1,5
    linha_base.csv           n.º de rajadas em cada permutação, por combinação (nota, U, D)
    teste.csv                real vs linha de base: média, p95, valor-p, por combinação
    top10_rajadas.csv        as 10 rajadas mais fortes, com o resumo das contas
    top10_contas.csv         uma linha por conta de cada uma dessas rajadas
    coordenacao_relatorio.md relatório

Como correr:
    python scripts/06_coordenacao.py --dataset 1m
    python scripts/06_coordenacao.py --dataset 32m --repeticoes 10     (só com autorização)

Notas:
    - Notas extremas: 1 e 5 no 1M (escala inteira); 0,5 e 5,0 no small e no 32M.
    - A permutação ordena as avaliações de cada filme por hash(userId, movieId, semente), com
      uma semente diferente por repetição (1..R). É o equivalente a setseed + random(), mas
      reprodutível também com várias threads (random() no DuckDB não o garante).
    - A sessão DuckDB fica em UTC; as horas e os dias vêm de epoch_ms (sem fuso).
"""
import argparse
import time

import duckdb
import pandas as pd

from common import DATASETS, ROOT, load_config

NOTAS_EXTREMAS = {'small': (0.5, 5.0), '1m': (1.0, 5.0), '32m': (0.5, 5.0)}
LIMIARES_UTILIZADORES = (3, 5, 10)
LIMIARES_DESVIO = (1.5, 2.0)
TOP = 10
AMOSTRA_JACCARD = 1000   # contas ao acaso para o Jaccard de referência entre pares quaisquer


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dataset', choices=list(DATASETS), help='sobrepõe o valor de config.yaml')
    ap.add_argument('--repeticoes', type=int, default=20,
                    help='n.º de permutações da linha de base (20 por omissão; 10 no 32M se for lento)')
    return ap.parse_args()


def ligar(cfg):
    """Ligação DuckDB em UTC com a tabela r (userId, movieId, rating, ts) e a view movies."""
    con = duckdb.connect()
    con.execute("SET TimeZone = 'UTC'")
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
    return con


def sql_rajadas(tabela, lo, hi):
    """Grupos (filme, nota extrema, hora) com >= 3 utilizadores e desvio >= 1,5 (o mínimo testado)."""
    return f"""
        SELECT t.movieId, t.rating AS nota, t.ts // 3600 AS hora,
               COUNT(DISTINCT t.userId)              AS utilizadores,
               MAX(abs(t.rating - f.media_filme))    AS desvio,
               MAX(f.media_filme)                    AS media_filme
        FROM {tabela} t JOIN filme f USING (movieId)
        WHERE t.rating IN ({lo}, {hi})
        GROUP BY t.movieId, t.rating, t.ts // 3600
        HAVING COUNT(DISTINCT t.userId) >= {min(LIMIARES_UTILIZADORES)}
           AND MAX(abs(t.rating - f.media_filme)) >= {min(LIMIARES_DESVIO)}"""


def contar(con, sql, lo, hi):
    """N.º de rajadas por (nota, U, D), com nota = lo, hi e 'ambas'."""
    df = con.execute(sql).df()
    linhas = []
    for nota, sub in [(lo, df[df.nota == lo]), (hi, df[df.nota == hi]), ('ambas', df)]:
        for u in LIMIARES_UTILIZADORES:
            for d in LIMIARES_DESVIO:
                n = int(((sub.utilizadores >= u) & (sub.desvio >= d)).sum())
                linhas.append({'nota': nota, 'min_utilizadores': u, 'min_desvio': d, 'rajadas': n})
    return pd.DataFrame(linhas)


def permutar(con, semente):
    """Tabela p: as avaliações de cada filme com os timestamps desse filme baralhados."""
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


def caracterizar(con, top):
    """Uma linha por conta de cada rajada do top, e o Jaccard entre as contas de cada rajada."""
    con.register('top_df', top[['rajada', 'movieId', 'nota', 'hora']])
    contas = con.execute("""
        WITH u AS (SELECT userId, COUNT(*) AS avaliacoes_conta, MIN(ts) AS primeiro_ts, MAX(ts) AS ultimo_ts
                   FROM r GROUP BY userId),
             membros AS (SELECT t.rajada, r.userId, r.ts
                         FROM top_df t JOIN r ON r.movieId = t.movieId AND r.rating = t.nota
                                              AND r.ts // 3600 = t.hora)
        SELECT m.rajada, m.userId,
               strftime(epoch_ms(m.ts * 1000), '%Y-%m-%d %H:%M:%S')     AS momento,
               u.avaliacoes_conta,
               strftime(epoch_ms(u.primeiro_ts * 1000), '%Y-%m-%d')     AS primeiro_dia,
               ROUND((m.ts - u.primeiro_ts) / 86400.0, 2)               AS antiguidade_dias,
               m.ts - u.primeiro_ts < 86400                             AS no_registo,
               (SELECT COUNT(*) FROM r x WHERE x.userId = m.userId AND x.ts > m.ts) AS avaliacoes_depois,
               ROUND((u.ultimo_ts - m.ts) / 86400.0, 2)                 AS dias_ate_ultima,
               u.ultimo_ts - m.ts > 86400                               AS voltou_depois_24h
        FROM membros m JOIN u USING (userId)
        ORDER BY m.rajada, m.ts, m.userId""").df()
    jac = con.execute("""
        WITH membros AS (SELECT DISTINCT t.rajada, r.userId
                         FROM top_df t JOIN r ON r.movieId = t.movieId AND r.rating = t.nota
                                              AND r.ts // 3600 = t.hora),
             n AS (SELECT userId, COUNT(*) AS n FROM r GROUP BY userId),
             pares AS (SELECT a.rajada, a.userId AS u1, b.userId AS u2
                       FROM membros a JOIN membros b ON a.rajada = b.rajada AND a.userId < b.userId),
             comuns AS (SELECT p.rajada, p.u1, p.u2, COUNT(*) AS comuns
                        FROM pares p JOIN r x ON x.userId = p.u1 JOIN r y ON y.userId = p.u2 AND y.movieId = x.movieId
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
    lo, hi = NOTAS_EXTREMAS[ds]
    saida = cfg['paths']['results'] / ds / 'bots_coordenacao'
    saida.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    con = ligar(cfg)

    # 1. Rajadas reais
    rajadas = con.execute(sql_rajadas('r', lo, hi) + ' ORDER BY utilizadores DESC, desvio DESC, movieId, hora').df()
    real = contar(con, sql_rajadas('r', lo, hi), lo, hi)
    print(f'[{ds}] rajadas reais (U>=3, D>=1,5): {len(rajadas)}')

    # 2. Linha de base: R permutações dos timestamps dentro de cada filme
    base = []
    for semente in range(1, args.repeticoes + 1):
        permutar(con, semente)
        c = contar(con, sql_rajadas('p', lo, hi), lo, hi)
        c.insert(0, 'repeticao', semente)
        base.append(c)
        print(f'  permutação {semente}/{args.repeticoes}: {int(c[(c.nota == "ambas") & (c.min_utilizadores == 3) & (c.min_desvio == 1.5)].rajadas.iloc[0])} rajadas (U>=3, D>=1,5)')
    base = pd.concat(base, ignore_index=True)
    chave = ['nota', 'min_utilizadores', 'min_desvio']
    base['nota'] = base['nota'].astype(str)
    real['nota'] = real['nota'].astype(str)
    agg = base.groupby(chave, sort=False).rajadas.agg(
        media='mean', p95=lambda s: s.quantile(0.95), maximo='max').reset_index()
    teste = real.rename(columns={'rajadas': 'real'}).merge(agg, on=chave)
    teste = teste.merge(base.merge(real.rename(columns={'rajadas': 'real'}), on=chave)
                        .assign(ge=lambda d: d.rajadas >= d.real)
                        .groupby(chave, sort=False).ge.sum().rename('perm_ge_real').reset_index(), on=chave)
    R = args.repeticoes
    teste['valor_p'] = ((1 + teste.perm_ge_real) / (1 + R)).round(3)
    teste['p95'] = teste.p95.round(2)
    teste['razao_real_media'] = (teste.real / teste.media.where(teste.media > 0)).round(2)
    teste['media'] = teste.media.round(2)

    # 3. Top 10 rajadas reais
    filmes = con.execute('SELECT f.*, m.title FROM filme f JOIN movies m USING (movieId)').df()
    hora_total = con.execute("""SELECT movieId, ts // 3600 AS hora, COUNT(*) AS avaliacoes_filme_hora
                                FROM r GROUP BY 1, 2""").df()
    rajadas = (rajadas.merge(filmes[['movieId', 'title', 'avaliacoes_filme', 'estreia_ts']], on='movieId')
                      .merge(hora_total, on=['movieId', 'hora']))
    rajadas = rajadas.sort_values(['utilizadores', 'desvio', 'movieId', 'hora'],
                                  ascending=[False, False, True, True]).reset_index(drop=True)
    rajadas['inicio_hora_utc'] = pd.to_datetime(rajadas.hora * 3600, unit='s').dt.strftime('%Y-%m-%d %H:00')
    rajadas['pct_da_hora'] = (100 * rajadas.utilizadores / rajadas.avaliacoes_filme_hora).round(1)
    rajadas['dias_desde_estreia_dataset'] = ((rajadas.hora * 3600 - rajadas.estreia_ts) / 86400).round(2)
    rajadas['ano_titulo'] = rajadas.title.str.extract(r'\((\d{4})\)\s*$')[0]
    rajadas['desvio'] = rajadas.desvio.round(3)
    rajadas['media_filme'] = rajadas.media_filme.round(3)
    cols = ['movieId', 'title', 'ano_titulo', 'nota', 'inicio_hora_utc', 'utilizadores',
            'avaliacoes_filme_hora', 'pct_da_hora', 'media_filme', 'desvio', 'avaliacoes_filme',
            'dias_desde_estreia_dataset']
    rajadas[cols].to_csv(saida / 'rajadas.csv', index=False)

    top = rajadas.head(TOP).copy()
    top.insert(0, 'rajada', range(1, len(top) + 1))
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
        **({'suspeitos_bloco5': ('classificacao', lambda s: int(s.str.startswith('suspeito').sum()))}
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

    # 4. Relatório
    segundos = time.perf_counter() - t0
    md = [f'# Coordenação entre contas · MovieLens {ds}', '',
          f'Gerado por `scripts/06_coordenacao.py` em {segundos:.1f} s (sessão DuckDB em UTC). '
          '**A validar com o Luís.**', '',
          '## Definição', '',
          f'Rajada: (filme, nota extrema, hora UTC) com >= U utilizadores distintos e |nota - média do filme| >= D. '
          f'Notas extremas: {lo:g} e {hi:g}. U em {{{", ".join(map(str, LIMIARES_UTILIZADORES))}}}, '
          f'D em {{{", ".join(f"{d:g}" for d in LIMIARES_DESVIO)}}}.', '',
          f'Linha de base: {R} permutações dos timestamps dentro de cada filme (sementes 1..{R}). '
          'Valor-p empírico = (1 + n.º de permutações >= real) / (1 + R); com R = '
          f'{R} o menor valor possível é {1 / (1 + R):.3f}.', '',
          '## Real vs linha de base', '',
          tabela_md(teste[['nota', 'min_utilizadores', 'min_desvio', 'real', 'media', 'p95', 'maximo',
                           'razao_real_media', 'valor_p']]), '',
          f'## As {TOP} rajadas reais mais fortes', '',
          tabela_md(top[['rajada', 'title', 'nota', 'inicio_hora_utc', 'utilizadores', 'avaliacoes_filme_hora',
                         'pct_da_hora', 'desvio', 'dias_desde_estreia_dataset', 'antiguidade_mediana_dias',
                         'pct_no_registo', 'avaliacoes_conta_mediana', 'pct_voltaram_24h', 'jaccard_medio',
                         'jaccard_max'] + (['suspeitos_bloco5'] if 'suspeitos_bloco5' in top else [])]), '',
          f'Jaccard de referência entre pares de contas quaisquer ({AMOSTRA_JACCARD} contas ao acaso): '
          f'média {jac_ref[0]:.3f}, p95 {jac_ref[1]:.3f}.', '']
    (saida / 'coordenacao_relatorio.md').write_text('\n'.join(md), encoding='utf-8')
    print(f'Gravado em {saida.relative_to(ROOT)} ({segundos:.1f} s)')


if __name__ == '__main__':
    main()
