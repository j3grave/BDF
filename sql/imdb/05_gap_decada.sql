-- 05_gap_decada.sql (DuckDB) - P1: onde divergem? Gap por década de estreia.
--
-- Como funciona: a década vem do ano de estreia no IMDb (startYear), que é mais fiável do que
-- o ano entre parênteses no título do MovieLens. Ex.: 1994 -> 1990. Filmes sem startYear
-- ficam de fora.
--
-- Parâmetros: ${filmes}, ${min_ml}, ${min_imdb}
WITH f AS (
    SELECT CAST(floor(ano_estreia / 10) * 10 AS INTEGER) AS decada, nota_ml_10, nota_imdb, gap
    FROM ${filmes}
    WHERE nota_imdb IS NOT NULL AND n_ml >= ${min_ml} AND votos_imdb >= ${min_imdb}
      AND ano_estreia IS NOT NULL
),
r AS (
    SELECT decada, nota_ml_10, nota_imdb, gap,
           rank() OVER (PARTITION BY decada ORDER BY nota_ml_10)
             + (COUNT(*) OVER (PARTITION BY decada, nota_ml_10) - 1) / 2.0 AS rank_ml,
           rank() OVER (PARTITION BY decada ORDER BY nota_imdb)
             + (COUNT(*) OVER (PARTITION BY decada, nota_imdb) - 1) / 2.0  AS rank_imdb
    FROM f
)
SELECT decada,
       COUNT(*)                                              AS filmes,
       AVG(nota_ml_10)                                       AS media_ml_10,
       AVG(nota_imdb)                                        AS media_imdb,
       AVG(gap)                                              AS gap_medio,
       AVG(gap) - 1.96 * STDDEV_SAMP(gap) / SQRT(COUNT(*))   AS gap_ic95_inf,
       AVG(gap) + 1.96 * STDDEV_SAMP(gap) / SQRT(COUNT(*))   AS gap_ic95_sup,
       CORR(nota_ml_10, nota_imdb)                           AS pearson,
       CORR(rank_ml, rank_imdb)                              AS spearman
FROM r
GROUP BY decada
ORDER BY decada;
