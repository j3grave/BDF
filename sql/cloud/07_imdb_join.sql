-- 07_imdb_join.sql (DuckDB) - query extra do benchmark da fase 3: join MovieLens x IMDb.
-- Está em sql/cloud/ (e não em sql/) para não alterar o benchmark da fase 1.
-- A versão para o Athena está em sql/athena/queries/07_imdb_join.sql.
--
-- Pergunta: quantos filmes ligam ao IMDb e quanto concordam (gap médio e Pearson), só com os
-- filmes com pelo menos 50 avaliações no MovieLens e 1000 votos no IMDb (os limiares do
-- config.yaml, fixos aqui para o benchmark ser sempre a mesma query).
-- A explicação da ligação (tconst e lpad) está em sql/imdb/00_filmes.sql.
--
-- Ligação às aulas:
-- - Parquet: do title.basics (13 milhões de linhas e 9 colunas) só se leem tconst e titleType;
--   no TSV.gz é preciso descomprimir e ler o ficheiro inteiro.
-- - O resultado é uma só linha: o que se mede é a leitura e o join, não a escrita do resultado.
--
-- Parâmetros: ${ratings}, ${links}, ${imdb_ratings}, ${imdb_basics}
WITH ml AS (
    SELECT movieId, COUNT(*) AS n_ml, AVG(rating) AS media_ml
    FROM ${ratings}
    GROUP BY movieId
),
lk AS (
    SELECT movieId, 'tt' || CASE WHEN length(imdbId) < 7 THEN lpad(imdbId, 7, '0') ELSE imdbId END AS tconst
    FROM ${links}
    WHERE imdbId IS NOT NULL
),
j AS (
    SELECT ml.n_ml, ml.media_ml * 2 AS nota_ml_10, b.titleType, i.averageRating AS nota_imdb, i.numVotes
    FROM ml
    JOIN lk ON lk.movieId = ml.movieId
    JOIN ${imdb_basics} b ON b.tconst = lk.tconst
    JOIN ${imdb_ratings} i ON i.tconst = lk.tconst
)
SELECT COUNT(*)                          AS filmes_ligados,
       count_if(titleType = 'movie')     AS filmes_tipo_movie,
       AVG(nota_imdb - nota_ml_10)       AS gap_medio,
       CORR(nota_ml_10, nota_imdb)       AS pearson
FROM j
WHERE n_ml >= 50 AND numVotes >= 1000;
