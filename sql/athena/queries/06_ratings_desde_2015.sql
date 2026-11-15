-- 06_ratings_desde_2015.sql (Athena) - equivalente a sql/cloud/06_ratings_desde_2015.sql
-- Partition pruning: a mesma agregação da query 05, mas só a partir de 2015.
--
-- Em ratings_part, o filtro year >= 2015 é resolvido pelos nomes das pastas: o Athena
-- nem abre os ficheiros dos anos anteriores e cobra só os bytes das pastas lidas.
-- Em ratings (Parquet sem partição) tem de ler as colunas timestamp e rating do ficheiro todo;
-- em ratings_csv lê o ficheiro inteiro.
--
-- Parâmetros: ${ratings}
SELECT r.year,
       COUNT(*)                 AS num_ratings,
       ROUND(AVG(r.rating), 3)  AS avg_rating
FROM ${ratings} AS r
WHERE r.year >= 2015
GROUP BY r.year
ORDER BY r.year
