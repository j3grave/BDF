-- anual.sql (Athena) - equivalente a sql/analise/anual.sql
-- Origem: notebook do Luís, célula 108 ("novo-queries"), consultas_sql()["anual"].
--
-- Fuso horário: em ratings_part, year vem do nome das pastas (calculado em UTC no
-- prepare_cloud.py); nas tabelas sem partição, year = year(from_unixtime("timestamp")) e
-- from_unixtime devolve a data em UTC. O resultado não depende do fuso da sessão.
-- Diferenças para o DuckDB: GROUP BY pela coluna (o Trino não aceita aliases do SELECT
-- no GROUP BY); nomes de colunas em minúsculas.
-- Resultado agregado: uma linha por ano.
--
-- Parâmetros: ${ratings}
SELECT r.year AS ano,
       COUNT(*)                 AS num_ratings,
       AVG(r.rating)            AS media,
       COUNT(DISTINCT r.userid) AS utilizadores
FROM ${ratings} AS r
GROUP BY r.year
ORDER BY r.year
