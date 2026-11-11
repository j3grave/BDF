-- valores_ano.sql (Athena) - equivalente a sql/analise/valores_ano.sql
-- Origem: notebook do Luís, célula 108 ("novo-queries"), consultas_sql()["valores_ano"].
--
-- Fuso horário: year vem das pastas de ratings_part ou de year(from_unixtime("timestamp")),
-- e from_unixtime devolve UTC. O resultado não depende do fuso da sessão.
-- Resultado agregado: no máximo 10 valores por ano.
--
-- Parâmetros: ${ratings}
SELECT r.year AS ano, r.rating, COUNT(*) AS num_ratings
FROM ${ratings} AS r
GROUP BY r.year, r.rating
ORDER BY r.year, r.rating
