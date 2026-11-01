-- Query temporal: número de ratings e média por ano.
-- A coluna year vem das pastas year=AAAA no Parquet particionado e é calculada a partir do
-- timestamp (UTC) no Parquet sem partição.
-- Parâmetros: ${ratings}
SELECT year,
       COUNT(*)                 AS num_ratings,
       ROUND(AVG(rating), 3)    AS avg_rating
FROM ${ratings}
GROUP BY year
ORDER BY year;
