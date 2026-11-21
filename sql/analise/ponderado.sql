-- ponderado.sql (DuckDB) - top 10 de filmes por média bayesiana (média ponderada)
--
-- Pergunta: que filmes têm a melhor média quando se "puxa" a média dos filmes com poucas
-- avaliações para a média global? weighted = v/(v+m)*R + m/(v+m)*C, com m = 100 avaliações,
-- R = média do filme, v = n.º de avaliações do filme e C = média global.
--
-- Notas:
-- - os nomes R e C passam a media_filme e media_global (no Athena, R e r seriam o mesmo nome);
-- - a coluna media_global serve para comparar a média global com a da EDA;
-- - desempate por movieId.
--
-- Parâmetros: ${ratings}, ${movies}
WITH s AS (SELECT movieId, AVG(rating) AS media_filme, COUNT(*) AS v
           FROM ${ratings} GROUP BY movieId),
     p AS (SELECT AVG(rating) AS media_global FROM ${ratings})
SELECT s.movieId, m.title, s.media_filme AS avg_rating, s.v AS num_ratings,
       s.v / (s.v + 100.0) * s.media_filme + 100.0 / (s.v + 100.0) * p.media_global AS weighted,
       p.media_global
FROM s CROSS JOIN p
JOIN ${movies} m ON s.movieId = m.movieId
ORDER BY weighted DESC, s.movieId
LIMIT 10;
