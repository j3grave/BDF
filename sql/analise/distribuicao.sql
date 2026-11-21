-- distribuicao.sql (DuckDB) - como os utilizadores usam cada valor da escala
--
-- Pergunta: para cada valor de rating, quantos utilizadores o usam e que peso tem, em média,
-- no histórico de cada utilizador?
--
-- Notas:
-- - a tabela (utilizador, valor) só existe como CTE (no 32M teria cerca de 1,5 M linhas);
--   o resultado é agregado por valor (no máximo 10 linhas);
-- - prop_media_utilizador é a média, sobre TODOS os utilizadores (0 para quem não usa o
--   valor), da fração do histórico do utilizador com esse valor. As frações somam 1.
--
-- Parâmetros: ${ratings}
WITH d AS (SELECT userId, rating, COUNT(*) AS n FROM ${ratings} GROUP BY userId, rating),
     t AS (SELECT userId, SUM(n) AS total FROM d GROUP BY userId),
     g AS (SELECT COUNT(*) AS utilizadores, SUM(total) AS avaliacoes FROM t)
SELECT d.rating,
       COUNT(*)                                     AS utilizadores_que_usam,
       100.0 * COUNT(*) / g.utilizadores            AS pct_utilizadores,
       SUM(d.n)                                     AS num_ratings,
       100.0 * SUM(d.n) / g.avaliacoes              AS pct_ratings,
       SUM(d.n * 1.0 / t.total) / g.utilizadores    AS prop_media_utilizador
FROM d JOIN t ON d.userId = t.userId CROSS JOIN g
GROUP BY d.rating, g.utilizadores, g.avaliacoes
ORDER BY d.rating;
