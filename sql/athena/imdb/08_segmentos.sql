-- 08_segmentos.sql (Athena) - equivalente a sql/imdb/08_segmentos.sql (explicação e
-- LIMITAÇÃO da P2 lá: o IMDb não tem dados por utilizador).
--
-- *** O tipo "bots" é PROVISÓRIO: as regras do 10_flag_bots.sql ainda estão a ser validadas
-- pelo Luís. *** ${flag_bots} é a tabela do CTAS descrito em sql/athena/analise/10_flag_bots.sql.
--
-- Diferenças para o DuckDB: "timestamp" entre aspas; posição média nos empates com
-- CAST(... AS double) / 2.
--
-- Tipo de título: só os tipos de ${tipos} (config.yaml, imdb.tipos_titulo; por omissão só 'movie').
-- Séries, episódios, curtas e vídeos ficam de fora (ver 02_ligacao_tipos.sql).
--
-- Parâmetros: ${ratings}, ${filmes}, ${tipos}, ${flag_bots}, ${min_seg}, ${min_imdb}, ${corte_era}
WITH u AS (
    SELECT r.userid, COUNT(*) AS total, MIN(r."timestamp") AS primeiro_ts
    FROM ${ratings} AS r
    GROUP BY r.userid
),
seg AS (
    SELECT userid, 'atividade' AS tipo,
           CASE WHEN total < 50 THEN '20–49' WHEN total < 100 THEN '50–99' WHEN total < 250 THEN '100–249'
                WHEN total < 1000 THEN '250–999' ELSE '1000 ou mais' END AS segmento,
           CASE WHEN total < 50 THEN 1 WHEN total < 100 THEN 2 WHEN total < 250 THEN 3
                WHEN total < 1000 THEN 4 ELSE 5 END AS ordem
    FROM u
    UNION ALL
    SELECT userid, 'era',
           CASE WHEN primeiro_ts < ${corte_era} THEN 'antes de 18/02/2003' ELSE 'a partir de 18/02/2003' END,
           CASE WHEN primeiro_ts < ${corte_era} THEN 1 ELSE 2 END
    FROM u
    UNION ALL
    SELECT b.userid, 'bots (PROVISÓRIO)',
           CASE WHEN b.classificacao LIKE 'suspeito%' THEN 'sinalizados' ELSE 'não sinalizados' END,
           CASE WHEN b.classificacao LIKE 'suspeito%' THEN 2 ELSE 1 END
    FROM ${flag_bots} AS b
),
utilizadores AS (
    SELECT tipo, segmento, ordem, COUNT(*) AS utilizadores
    FROM seg
    GROUP BY tipo, segmento, ordem
),
n_segmentos AS (
    SELECT tipo, COUNT(*) AS n FROM utilizadores GROUP BY tipo
),
por_filme AS (
    SELECT s.tipo, s.segmento, r.movieid, COUNT(*) AS n, AVG(r.rating) * 2 AS nota_seg_10
    FROM ${ratings} AS r
    JOIN seg AS s ON s.userid = r.userid
    GROUP BY s.tipo, s.segmento, r.movieid
),
elegiveis AS (
    SELECT p.tipo, p.segmento, p.movieid, p.n, p.nota_seg_10, f.nota_imdb,
           f.nota_imdb - p.nota_seg_10 AS gap
    FROM por_filme AS p
    JOIN ${filmes} AS f ON f.movieid = p.movieid
    WHERE p.n >= ${min_seg} AND f.nota_imdb IS NOT NULL AND f.votos_imdb >= ${min_imdb}
      AND f.tipo_imdb IN ${tipos}
),
comuns AS (
    SELECT e.tipo, e.movieid
    FROM elegiveis AS e
    JOIN n_segmentos AS s ON s.tipo = e.tipo
    GROUP BY e.tipo, e.movieid
    HAVING COUNT(*) = MAX(s.n)
),
r AS (
    SELECT e.tipo, e.segmento, e.n, e.nota_seg_10, e.nota_imdb, e.gap,
           rank() OVER (PARTITION BY e.tipo, e.segmento ORDER BY e.nota_seg_10)
             + CAST(COUNT(*) OVER (PARTITION BY e.tipo, e.segmento, e.nota_seg_10) - 1 AS double) / 2 AS rank_seg,
           rank() OVER (PARTITION BY e.tipo, e.segmento ORDER BY e.nota_imdb)
             + CAST(COUNT(*) OVER (PARTITION BY e.tipo, e.segmento, e.nota_imdb) - 1 AS double) / 2   AS rank_imdb
    FROM elegiveis AS e
    JOIN comuns AS c ON c.tipo = e.tipo AND c.movieid = e.movieid
),
metricas AS (
    SELECT tipo, segmento,
           COUNT(*)                                              AS filmes_comuns,
           SUM(n)                                                AS avaliacoes,
           AVG(nota_seg_10)                                      AS media_segmento_10,
           AVG(nota_imdb)                                        AS media_imdb,
           AVG(gap)                                              AS gap_medio,
           AVG(gap) - 1.96 * STDDEV_SAMP(gap) / SQRT(COUNT(*))   AS gap_ic95_inf,
           AVG(gap) + 1.96 * STDDEV_SAMP(gap) / SQRT(COUNT(*))   AS gap_ic95_sup,
           AVG(ABS(gap))                                         AS gap_abs_medio,
           CORR(nota_seg_10, nota_imdb)                          AS pearson,
           CORR(rank_seg, rank_imdb)                             AS spearman
    FROM r
    GROUP BY tipo, segmento
)
SELECT u.tipo, u.segmento, u.ordem, u.utilizadores,
       COALESCE(m.filmes_comuns, 0) AS filmes_comuns, m.avaliacoes,
       m.media_segmento_10, m.media_imdb, m.gap_medio, m.gap_ic95_inf, m.gap_ic95_sup,
       m.gap_abs_medio, m.pearson, m.spearman
FROM utilizadores AS u
LEFT JOIN metricas AS m ON m.tipo = u.tipo AND m.segmento = u.segmento
ORDER BY u.tipo, u.ordem
