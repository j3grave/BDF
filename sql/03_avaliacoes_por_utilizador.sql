-- Pergunta 7.3: qual é a distribuição das avaliações por utilizador?
-- Resumo por utilizador: n.º de avaliações, média, desvio-padrão, mínimo, mediana e máximo.
-- Parâmetros: ${ratings}
SELECT userId,
       COUNT(*)                         AS num_ratings,
       ROUND(AVG(rating), 3)            AS mean,
       ROUND(STDDEV_SAMP(rating), 3)    AS std,
       MIN(rating)                      AS min,
       MEDIAN(rating)                   AS median,
       MAX(rating)                      AS max
FROM ${ratings}
GROUP BY userId
ORDER BY userId;
