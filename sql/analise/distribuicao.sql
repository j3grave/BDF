-- distribuicao.sql (DuckDB) - como os utilizadores usam cada valor da escala
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 108 (id "novo-queries"), consultas_sql()["distribuicao"]. Autor: Luís Pousada (e51d050).
--
-- Pergunta: para cada valor de rating, quantos utilizadores o usam e que peso tem, em média,
-- no histórico de cada utilizador?
--
-- Alterações face ao original:
-- - o original devolvia uma linha por (utilizador, valor): 3 976 linhas no small e ~1,5 M no
--   32M, só para alimentar o heatmap do notebook. A tabela (utilizador, valor) passa a ser
--   uma CTE e o resultado é agregado por valor (no máximo 10 linhas);
-- - prop_media_utilizador é a média, sobre TODOS os utilizadores (0 para quem não usa o
--   valor), da fração do histórico do utilizador com esse valor. As frações somam 1.
-- Os números podem ser reconstruídos a partir da saída original (validado no small e no 1M).
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
