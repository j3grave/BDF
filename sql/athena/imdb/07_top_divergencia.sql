-- 07_top_divergencia.sql (Athena) - equivalente a sql/imdb/07_top_divergencia.sql.
--
-- Sem diferenças de sintaxe relevantes (row_number e UNION ALL existem no Trino).
--
-- Parâmetros: ${filmes}, ${min_ml}, ${min_imdb}
WITH f AS (
    SELECT x.movieid, x.title, x.ano_estreia, x.tipo_imdb, x.n_ml, x.nota_ml_10, x.votos_imdb, x.nota_imdb, x.gap,
           row_number() OVER (ORDER BY x.gap DESC, x.movieid) AS pos_imdb_acima,
           row_number() OVER (ORDER BY x.gap ASC, x.movieid)  AS pos_ml_acima
    FROM ${filmes} AS x
    WHERE x.nota_imdb IS NOT NULL AND x.n_ml >= ${min_ml} AND x.votos_imdb >= ${min_imdb}
)
SELECT 'IMDb acima do MovieLens' AS sentido, pos_imdb_acima AS posicao,
       movieid, title, ano_estreia, tipo_imdb, n_ml, nota_ml_10, votos_imdb, nota_imdb, gap
FROM f WHERE pos_imdb_acima <= 10
UNION ALL
SELECT 'MovieLens acima do IMDb' AS sentido, pos_ml_acima AS posicao,
       movieid, title, ano_estreia, tipo_imdb, n_ml, nota_ml_10, votos_imdb, nota_imdb, gap
FROM f WHERE pos_ml_acima <= 10
ORDER BY sentido, posicao
