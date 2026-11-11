-- 06_ratings_desde_2015.sql (DuckDB) - query extra do benchmark da fase 2
-- Partition pruning: a mesma agregação da 05_ratings_por_ano.sql, mas só a partir de 2015.
-- Está em sql/cloud/ (e não em sql/) para não alterar o benchmark da fase 1.
-- A versão para o Athena está em sql/athena/queries/06_ratings_desde_2015.sql.
--
-- Ligação às aulas:
-- - Parquet particionado: com WHERE year >= 2015 o DuckDB não abre as pastas
--   year=1995 ... year=2014 (partition pruning).
-- - Parquet sem partição e CSV: year é calculado a partir do timestamp, linha a linha,
--   e o filtro só se aplica depois de ler o ficheiro.
--
-- Parâmetros: ${ratings}
SELECT year,
       COUNT(*)                 AS num_ratings,
       ROUND(AVG(rating), 3)    AS avg_rating
FROM ${ratings}
WHERE year >= 2015
GROUP BY year
ORDER BY year;
