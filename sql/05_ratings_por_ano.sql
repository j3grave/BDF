-- 05_ratings_por_ano.sql
-- Query temporal: número de ratings e média por ano.
--
-- Como funciona: agrupa os ratings pela coluna year e calcula o n.º e a média em cada ano.
--
-- Ligação às aulas (é a query em que as partições fazem diferença):
-- - Parquet particionado: a coluna year vem do nome das pastas year=AAAA, por isso
--   o DuckDB não precisa de ler nem converter o timestamp; dentro dos ficheiros só lê
--   rating.
-- - Parquet sem partição: year tem de ser calculado linha a linha a partir do
--   timestamp (ver 03_benchmark.py), o que obriga a ler também essa coluna.
-- - Partition pruning: com um filtro como WHERE year >= 2015, o DuckDB nem abriria
--   as pastas dos anos anteriores. É o filter pushdown aplicado às partições.
--
-- Parâmetros: ${ratings}
SELECT year,
       COUNT(*)                 AS num_ratings,
       ROUND(AVG(rating), 3)    AS avg_rating
FROM ${ratings}
GROUP BY year
ORDER BY year;
