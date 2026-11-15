-- 04_gap_genero.sql (Athena) - equivalente a sql/imdb/04_gap_genero.sql (explicação lá).
--
-- Diferenças para o DuckDB: CROSS JOIN UNNEST(...) AS t(genero) em vez de unnest() no SELECT;
-- posição média nos empates com CAST(... AS double) / 2.
--
-- Tipo de título: só os tipos de ${tipos} (config.yaml, imdb.tipos_titulo; por omissão só 'movie').
-- Séries, episódios, curtas e vídeos ficam de fora (ver 02_ligacao_tipos.sql).
--
-- Parâmetros: ${filmes}, ${tipos}, ${min_ml}, ${min_imdb}
WITH f AS (
    SELECT t.genero, x.nota_ml_10, x.nota_imdb, x.gap
    FROM ${filmes} AS x
    CROSS JOIN UNNEST(x.generos_ml) AS t(genero)
    WHERE x.nota_imdb IS NOT NULL AND x.n_ml >= ${min_ml} AND x.votos_imdb >= ${min_imdb}
      AND x.tipo_imdb IN ${tipos}
),
r AS (
    SELECT genero, nota_ml_10, nota_imdb, gap,
           rank() OVER (PARTITION BY genero ORDER BY nota_ml_10)
             + CAST(COUNT(*) OVER (PARTITION BY genero, nota_ml_10) - 1 AS double) / 2 AS rank_ml,
           rank() OVER (PARTITION BY genero ORDER BY nota_imdb)
             + CAST(COUNT(*) OVER (PARTITION BY genero, nota_imdb) - 1 AS double) / 2  AS rank_imdb
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
ORDER BY gap_medio DESC, genero
