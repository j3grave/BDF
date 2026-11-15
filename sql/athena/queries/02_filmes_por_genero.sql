-- 02_filmes_por_genero.sql (Athena) - equivalente a sql/02_filmes_por_genero.sql
-- Pergunta 7.2: qual é o número de filmes por género?
--
-- Diferença para o DuckDB: CROSS JOIN UNNEST em vez de unnest() no SELECT.
--
-- Parâmetros: ${movies}
WITH movie_genre AS (
    SELECT m.movieid, t.genre
    FROM ${movies} AS m
    CROSS JOIN UNNEST(split(m.genres, '|')) AS t(genre)
)
SELECT genre,
       COUNT(*)                                                         AS num_movies,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ${movies}), 1)    AS pct_movies
FROM movie_genre
GROUP BY genre
ORDER BY num_movies DESC, genre
