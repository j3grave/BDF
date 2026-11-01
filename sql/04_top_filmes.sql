-- Pergunta 7.4: quais são os filmes com a média de avaliação mais alta?
-- Só filmes com pelo menos 100 avaliações; ordena pela média exata, não pela arredondada.
-- Parâmetros: ${ratings}, ${movies}
SELECT m.title, ROUND(AVG(r.rating), 2) AS avg_rating, COUNT(*) AS num_ratings
FROM ${ratings} r
JOIN ${movies} m USING (movieId)
GROUP BY m.movieId, m.title
HAVING COUNT(*) >= 100
ORDER BY AVG(r.rating) DESC
LIMIT 10;
