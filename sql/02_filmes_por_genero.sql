-- 02_filmes_por_genero.sql
-- Pergunta 7.2: qual é o número de filmes por género?
--
-- Como funciona: a CTE movie_genre tem uma linha por par (filme, género). Contamos as
-- linhas de cada género e dividimos pelo total de filmes para obter a percentagem.
-- Um filme pode ter vários géneros, por isso a soma de num_movies é maior do que o n.º de filmes.
--
-- Ligação às aulas:
-- - Formato colunar: só são lidas as colunas movieId e genres (projection pushdown).
-- - Metadados do Parquet: o rodapé de cada ficheiro guarda o n.º de linhas, por isso
--   o SELECT COUNT(*) do total pode ser respondido sem ler os dados.
-- - Partições: não se aplicam (só usa movies).
--
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
