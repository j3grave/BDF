-- Pergunta 7.2: qual é o número de filmes por género?
-- Um filme pode ter vários géneros, por isso a soma de num_movies é maior do que o n.º de filmes.
-- Parâmetros: ${movies}
WITH movie_genre AS (
    SELECT movieId, unnest(string_split(genres, '|')) AS genre
    FROM ${movies}
)
SELECT genre,
       COUNT(*)                                                         AS num_movies,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ${movies}), 1)    AS pct_movies
FROM movie_genre
GROUP BY genre
ORDER BY num_movies DESC, genre;
