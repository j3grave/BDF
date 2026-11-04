-- 05_ratings_por_ano.sql (Athena) - equivalente a sql/05_ratings_por_ano.sql
-- Query temporal: número de ratings e média por ano.
--
-- Em ratings_part, year vem do nome das pastas e o Athena só lê a coluna rating.
-- Em ratings e ratings_csv, year é calculado a partir do timestamp (ver athena_benchmark.py),
-- o que obriga a ler também essa coluna. Compare o DataScannedInBytes dos três formatos.
--
-- Parâmetros: ${ratings}
SELECT r.year,
       COUNT(*)                 AS num_ratings,
       ROUND(AVG(r.rating), 3)  AS avg_rating
FROM ${ratings} AS r
GROUP BY r.year
ORDER BY r.year
