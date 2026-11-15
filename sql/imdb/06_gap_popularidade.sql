-- 06_gap_popularidade.sql (DuckDB) - P1: onde divergem? Gap por popularidade no IMDb.
--
-- Como funciona: os filmes são divididos em ${n_quantis} grupos do mesmo tamanho pelo n.º de
-- votos no IMDb (ntile; 1 = menos votados). O desempate por movieId torna a divisão sempre igual.
-- Para cada grupo: votos mínimos e máximos, gap médio com IC 95%, Pearson e Spearman.
--
-- Parâmetros: ${filmes}, ${min_ml}, ${min_imdb}, ${n_quantis}
WITH f AS (
    SELECT movieId, votos_imdb, nota_ml_10, nota_imdb, gap,
           ntile(${n_quantis}) OVER (ORDER BY votos_imdb, movieId) AS quantil
    FROM ${filmes}
    WHERE nota_imdb IS NOT NULL AND n_ml >= ${min_ml} AND votos_imdb >= ${min_imdb}
),
r AS (
    SELECT quantil, votos_imdb, nota_ml_10, nota_imdb, gap,
           rank() OVER (PARTITION BY quantil ORDER BY nota_ml_10)
             + (COUNT(*) OVER (PARTITION BY quantil, nota_ml_10) - 1) / 2.0 AS rank_ml,
           rank() OVER (PARTITION BY quantil ORDER BY nota_imdb)
             + (COUNT(*) OVER (PARTITION BY quantil, nota_imdb) - 1) / 2.0  AS rank_imdb
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
ORDER BY quantil;
