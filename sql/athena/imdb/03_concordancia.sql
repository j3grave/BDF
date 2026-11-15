-- 03_concordancia.sql (Athena) - equivalente a sql/imdb/03_concordancia.sql (explicação lá).
--
-- Diferenças para o DuckDB:
-- - posição média nos empates com CAST(... AS double) / 2 (no Trino, (n - 1) / 2 com inteiros
--   seria divisão inteira);
-- - percentagem com CAST(... AS double).
-- CORR, STDDEV_SAMP e SQRT existem no Trino com o mesmo nome.
--
-- Parâmetros: ${filmes}, ${min_ml}, ${min_imdb}
WITH f AS (
    SELECT x.nota_ml_10, x.nota_imdb, x.gap
    FROM ${filmes} AS x
    WHERE x.nota_imdb IS NOT NULL AND x.n_ml >= ${min_ml} AND x.votos_imdb >= ${min_imdb}
),
r AS (
    SELECT nota_ml_10, nota_imdb, gap,
           rank() OVER (ORDER BY nota_ml_10)
             + CAST(COUNT(*) OVER (PARTITION BY nota_ml_10) - 1 AS double) / 2 AS rank_ml,
           rank() OVER (ORDER BY nota_imdb)
             + CAST(COUNT(*) OVER (PARTITION BY nota_imdb) - 1 AS double) / 2  AS rank_imdb
    FROM f
)
SELECT COUNT(*)                                              AS filmes,
       AVG(nota_ml_10)                                       AS media_ml_10,
       AVG(nota_imdb)                                        AS media_imdb,
       AVG(gap)                                              AS gap_medio,
       STDDEV_SAMP(gap)                                      AS gap_desvio_padrao,
       AVG(gap) - 1.96 * STDDEV_SAMP(gap) / SQRT(COUNT(*))   AS gap_ic95_inf,
       AVG(gap) + 1.96 * STDDEV_SAMP(gap) / SQRT(COUNT(*))   AS gap_ic95_sup,
       AVG(ABS(gap))                                         AS gap_abs_medio,
       100 * CAST(count_if(gap > 0) AS double) / COUNT(*)    AS pct_imdb_acima,
       CORR(nota_ml_10, nota_imdb)                           AS pearson,
       CORR(rank_ml, rank_imdb)                              AS spearman
FROM r
