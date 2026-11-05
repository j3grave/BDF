-- 04_top_filmes.sql
-- Pergunta 7.4: quais são os filmes com a média de avaliação mais alta?
--
-- Como funciona: junta ratings e movies pelo movieId, calcula a média de cada filme e
-- fica com os 10 melhores. Exige pelo menos 100 avaliações (HAVING), senão o topo
-- ficava cheio de filmes com uma única avaliação de 5 estrelas. Ordena pela média
-- exata e não pela arredondada, para o desempate ser correto. Em caso de empate na
-- média, o movieId decide a ordem, para o resultado ser sempre o mesmo (determinístico).
--
-- Ligação às aulas:
-- - Formato colunar: de ratings só se leem movieId e rating; de movies só movieId e
--   title (projection pushdown). genres e timestamp não são lidos.
-- - HAVING filtra depois de agregar (sobre COUNT(*)); um WHERE filtraria antes.
-- - Partições: não ajudam, porque a query usa todos os anos.
--
-- Parâmetros: ${ratings}, ${movies}
SELECT m.title, ROUND(AVG(r.rating), 2) AS avg_rating, COUNT(*) AS num_ratings
FROM ${ratings} r
JOIN ${movies} m USING (movieId)
GROUP BY m.movieId, m.title
HAVING COUNT(*) >= 100
ORDER BY AVG(r.rating) DESC, m.movieId
LIMIT 10;
