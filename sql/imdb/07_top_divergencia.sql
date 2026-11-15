-- 07_top_divergencia.sql (DuckDB) - P1: os 10 filmes com maior divergência em cada sentido.
--
-- Como funciona: row_number numera os filmes do maior gap para o menor (IMDb acima do
-- MovieLens) e do menor para o maior (MovieLens acima do IMDb); ficam os 10 primeiros de
-- cada lado. O desempate por movieId torna a lista sempre igual.
--
-- Tipo de título: só os tipos de ${tipos} (config.yaml, imdb.tipos_titulo; por omissão só 'movie').
-- Séries, episódios, curtas e vídeos ficam de fora (ver 02_ligacao_tipos.sql).
--
-- Parâmetros: ${filmes}, ${tipos}, ${min_ml}, ${min_imdb}
WITH f AS (
    SELECT movieId, title, ano_estreia, tipo_imdb, n_ml, nota_ml_10, votos_imdb, nota_imdb, gap,
           row_number() OVER (ORDER BY gap DESC, movieId) AS pos_imdb_acima,
           row_number() OVER (ORDER BY gap ASC, movieId)  AS pos_ml_acima
    FROM ${filmes}
    WHERE nota_imdb IS NOT NULL AND n_ml >= ${min_ml} AND votos_imdb >= ${min_imdb}
      AND tipo_imdb IN ${tipos}
)
SELECT 'IMDb acima do MovieLens' AS sentido, pos_imdb_acima AS posicao,
       movieId, title, ano_estreia, tipo_imdb, n_ml, nota_ml_10, votos_imdb, nota_imdb, gap
FROM f WHERE pos_imdb_acima <= 10
UNION ALL
SELECT 'MovieLens acima do IMDb' AS sentido, pos_ml_acima AS posicao,
       movieId, title, ano_estreia, tipo_imdb, n_ml, nota_ml_10, votos_imdb, nota_imdb, gap
FROM f WHERE pos_ml_acima <= 10
ORDER BY sentido, posicao;
