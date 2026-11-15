-- 07_imdb_join.sql (Athena) - equivalente a sql/cloud/07_imdb_join.sql (explicação lá).
-- Join MovieLens x IMDb. No formato csv lê ratings_csv e as tabelas imdb_*_tsv (TSV.gz);
-- nos formatos parquet lê as tabelas Parquet. Compare o DataScannedInBytes: no TSV.gz o Athena
-- lê o ficheiro inteiro; no Parquet só as colunas usadas.
--
-- Diferenças para o DuckDB: nomes das colunas em minúsculas (titletype, averagerating, numvotes);
-- lpad corta textos maiores no Trino, por isso mantém-se o CASE.
--
-- Parâmetros: ${ratings}, ${links}, ${imdb_ratings}, ${imdb_basics}
WITH ml AS (
    SELECT r.movieid, COUNT(*) AS n_ml, AVG(r.rating) AS media_ml
    FROM ${ratings} AS r
    GROUP BY r.movieid
),
lk AS (
    SELECT l.movieid, 'tt' || CASE WHEN length(l.imdbid) < 7 THEN lpad(l.imdbid, 7, '0') ELSE l.imdbid END AS tconst
    FROM ${links} AS l
    WHERE l.imdbid IS NOT NULL
),
j AS (
    SELECT ml.n_ml, ml.media_ml * 2 AS nota_ml_10, b.titletype, i.averagerating AS nota_imdb, i.numvotes
    FROM ml
    JOIN lk ON lk.movieid = ml.movieid
    JOIN ${imdb_basics} AS b ON b.tconst = lk.tconst
    JOIN ${imdb_ratings} AS i ON i.tconst = lk.tconst
)
SELECT COUNT(*)                          AS filmes_ligados,
       count_if(titletype = 'movie')     AS filmes_tipo_movie,
       AVG(nota_imdb - nota_ml_10)       AS gap_medio,
       CORR(nota_ml_10, nota_imdb)       AS pearson
FROM j
WHERE n_ml >= 50 AND numvotes >= 1000
