-- 05_gap_decada.sql (Athena) - equivalente a sql/imdb/05_gap_decada.sql (explicação lá).
--
-- Diferenças para o DuckDB: ano_estreia é inteiro, por isso ano_estreia / 10 já é divisão
-- inteira no Trino (1994 / 10 = 199); a década é (ano / 10) * 10. Posição média nos empates
-- com CAST(... AS double) / 2.
--
-- Parâmetros: ${filmes}, ${min_ml}, ${min_imdb}
WITH f AS (
    SELECT CAST(floor(x.ano_estreia / 10) * 10 AS INTEGER) AS decada, x.nota_ml_10, x.nota_imdb, x.gap
    FROM ${filmes} AS x
    WHERE x.nota_imdb IS NOT NULL AND x.n_ml >= ${min_ml} AND x.votos_imdb >= ${min_imdb}
      AND x.ano_estreia IS NOT NULL
),
r AS (
    SELECT decada, nota_ml_10, nota_imdb, gap,
           rank() OVER (PARTITION BY decada ORDER BY nota_ml_10)
             + CAST(COUNT(*) OVER (PARTITION BY decada, nota_ml_10) - 1 AS double) / 2 AS rank_ml,
           rank() OVER (PARTITION BY decada ORDER BY nota_imdb)
             + CAST(COUNT(*) OVER (PARTITION BY decada, nota_imdb) - 1 AS double) / 2  AS rank_imdb
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
ORDER BY decada
