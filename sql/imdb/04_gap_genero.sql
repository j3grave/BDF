-- 04_gap_genero.sql (DuckDB) - P1: onde divergem? Gap por género.
--
-- Como funciona: os géneros são os do MovieLens (os mesmos do resto do projeto). Um filme com
-- vários géneros conta em cada um deles (unnest da lista generos_ml). Os filmes sem género
-- ("(no genres listed)") ficam de fora. Para cada género: gap médio com IC 95%, Pearson e
-- Spearman (posições calculadas dentro do género, por isso o PARTITION BY genero).
--
-- Parâmetros: ${filmes}, ${min_ml}, ${min_imdb}
WITH f AS (
    SELECT unnest(generos_ml) AS genero, nota_ml_10, nota_imdb, gap
    FROM ${filmes}
    WHERE nota_imdb IS NOT NULL AND n_ml >= ${min_ml} AND votos_imdb >= ${min_imdb}
),
r AS (
    SELECT genero, nota_ml_10, nota_imdb, gap,
           rank() OVER (PARTITION BY genero ORDER BY nota_ml_10)
             + (COUNT(*) OVER (PARTITION BY genero, nota_ml_10) - 1) / 2.0 AS rank_ml,
           rank() OVER (PARTITION BY genero ORDER BY nota_imdb)
             + (COUNT(*) OVER (PARTITION BY genero, nota_imdb) - 1) / 2.0  AS rank_imdb
    FROM f
    WHERE genero <> '(no genres listed)'
)
SELECT genero,
       COUNT(*)                                              AS filmes,
       AVG(nota_ml_10)                                       AS media_ml_10,
       AVG(nota_imdb)                                        AS media_imdb,
       AVG(gap)                                              AS gap_medio,
       AVG(gap) - 1.96 * STDDEV_SAMP(gap) / SQRT(COUNT(*))   AS gap_ic95_inf,
       AVG(gap) + 1.96 * STDDEV_SAMP(gap) / SQRT(COUNT(*))   AS gap_ic95_sup,
       CORR(nota_ml_10, nota_imdb)                           AS pearson,
       CORR(rank_ml, rank_imdb)                              AS spearman
FROM r
GROUP BY genero
ORDER BY gap_medio DESC, genero;
