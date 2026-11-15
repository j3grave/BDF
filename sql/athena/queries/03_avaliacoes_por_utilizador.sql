-- 03_avaliacoes_por_utilizador.sql (Athena) - equivalente a sql/03_avaliacoes_por_utilizador.sql
-- Pergunta 7.3: qual é a distribuição das avaliações por utilizador?
--
-- Diferença para o DuckDB: o Athena não tem MEDIAN exata. approx_percentile(rating, 0.5)
-- dá uma mediana aproximada, por isso a coluna median pode diferir ligeiramente da do DuckDB
-- (o n.º de linhas, um por utilizador, é o mesmo).
--
-- Parâmetros: ${ratings}
SELECT r.userid,
       COUNT(*)                                 AS num_ratings,
       ROUND(AVG(r.rating), 3)                  AS mean,
       ROUND(STDDEV_SAMP(r.rating), 3)          AS std,
       MIN(r.rating)                            AS min,
       approx_percentile(r.rating, 0.5)         AS median,
       MAX(r.rating)                            AS max
FROM ${ratings} AS r
GROUP BY r.userid
ORDER BY r.userid
