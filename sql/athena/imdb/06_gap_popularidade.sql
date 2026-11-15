-- 06_gap_popularidade.sql (Athena) - equivalente a sql/imdb/06_gap_popularidade.sql.
--
-- Diferença para o DuckDB: posição média nos empates com CAST(... AS double) / 2.
--
-- Parâmetros: ${filmes}, ${min_ml}, ${min_imdb}, ${n_quantis}
WITH f AS (
    SELECT x.movieid, x.votos_imdb, x.nota_ml_10, x.nota_imdb, x.gap,
           ntile(${n_quantis}) OVER (ORDER BY x.votos_imdb, x.movieid) AS quantil
    FROM ${filmes} AS x
    WHERE x.nota_imdb IS NOT NULL AND x.n_ml >= ${min_ml} AND x.votos_imdb >= ${min_imdb}
),
r AS (
    SELECT quantil, votos_imdb, nota_ml_10, nota_imdb, gap,
           rank() OVER (PARTITION BY quantil ORDER BY nota_ml_10)
             + CAST(COUNT(*) OVER (PARTITION BY quantil, nota_ml_10) - 1 AS double) / 2 AS rank_ml,
           rank() OVER (PARTITION BY quantil ORDER BY nota_imdb)
             + CAST(COUNT(*) OVER (PARTITION BY quantil, nota_imdb) - 1 AS double) / 2  AS rank_imdb
    FROM f
)
SELECT quantil,
       COUNT(*)                                              AS filmes,
       MIN(votos_imdb)                                       AS votos_min,
       MAX(votos_imdb)                                       AS votos_max,
       AVG(nota_ml_10)                                       AS media_ml_10,
       AVG(nota_imdb)                                        AS media_imdb,
       AVG(gap)                                              AS gap_medio,
       AVG(gap) - 1.96 * STDDEV_SAMP(gap) / SQRT(COUNT(*))   AS gap_ic95_inf,
       AVG(gap) + 1.96 * STDDEV_SAMP(gap) / SQRT(COUNT(*))   AS gap_ic95_sup,
       CORR(nota_ml_10, nota_imdb)                           AS pearson,
       CORR(rank_ml, rank_imdb)                              AS spearman
FROM r
GROUP BY quantil
ORDER BY quantil
