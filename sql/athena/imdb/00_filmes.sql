-- 00_filmes.sql (Athena) - equivalente a sql/imdb/00_filmes.sql (explicação completa lá).
--
-- COMO CORRER: o resultado tem uma linha por filme avaliado (cerca de 84 mil no 32M) e é lido
-- por todas as outras queries de sql/athena/imdb/. Corre-se como CTAS em Parquet:
--   CREATE TABLE imdb_filmes
--   WITH (format = 'PARQUET', external_location = 's3://<bucket-resultados>/ctas/imdb_filmes/')
--   AS <esta query>
-- e as outras queries usam ${filmes} = imdb_filmes.
--
-- Diferenças para o DuckDB:
-- - split(genres, '|') em vez de string_split (devolve array(varchar));
-- - lpad também corta textos maiores do que o tamanho pedido no Trino, por isso mantém-se o
--   CASE que só faz lpad aos ids com menos de 7 algarismos.
--
-- Parâmetros: ${ratings}, ${movies}, ${links}, ${imdb_basics}, ${imdb_ratings}
WITH ml AS (
    SELECT r.movieid, COUNT(*) AS n_ml, AVG(r.rating) AS media_ml
    FROM ${ratings} AS r
    GROUP BY r.movieid
),
lk AS (
    SELECT l.movieid,
           l.imdbid,
           'tt' || CASE WHEN length(l.imdbid) < 7 THEN lpad(l.imdbid, 7, '0') ELSE l.imdbid END AS tconst
    FROM ${links} AS l
    WHERE l.imdbid IS NOT NULL
)
SELECT ml.movieid,
       m.title,
       split(m.genres, '|')                 AS generos_ml,
       ml.n_ml,
       ml.media_ml,
       ml.media_ml * 2                      AS nota_ml_10,
       lk.imdbid,
       lk.tconst,
       b.tconst IS NOT NULL                 AS existe_no_imdb,
       b.titletype                          AS tipo_imdb,
       b.startyear                          AS ano_estreia,
       b.genres                             AS generos_imdb,
       i.averagerating                      AS nota_imdb,
       i.numvotes                           AS votos_imdb,
       i.averagerating - ml.media_ml * 2    AS gap
FROM ml
JOIN ${movies} AS m ON m.movieid = ml.movieid
LEFT JOIN lk ON lk.movieid = ml.movieid
LEFT JOIN ${imdb_basics} AS b ON b.tconst = lk.tconst
LEFT JOIN ${imdb_ratings} AS i ON i.tconst = lk.tconst
