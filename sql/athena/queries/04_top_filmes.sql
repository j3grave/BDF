-- 04_top_filmes.sql (Athena) - equivalente a sql/04_top_filmes.sql
-- Pergunta 7.4: quais são os filmes com a média de avaliação mais alta (mín. 100 avaliações)?
--
-- Diferença para o DuckDB: JOIN ... ON em vez de USING, para poder usar m.movieid
-- qualificado no GROUP BY sem ambiguidade.
--
-- Parâmetros: ${ratings}, ${movies}
SELECT m.title, ROUND(AVG(r.rating), 2) AS avg_rating, COUNT(*) AS num_ratings
FROM ${ratings} AS r
JOIN ${movies} AS m ON r.movieid = m.movieid
GROUP BY m.movieid, m.title
HAVING COUNT(*) >= 100
ORDER BY AVG(r.rating) DESC
LIMIT 10
