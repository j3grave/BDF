-- mensal.sql (Athena) - equivalente a sql/analise/mensal.sql
-- Origem: notebook do Luís, célula 109 ("novo-analytics"), consultas_complementares()["mensal"].
--
-- Fuso horário: from_unixtime("timestamp") devolve o instante em UTC (timestamp sem fuso da
-- sessão), por isso o mês não depende de onde a query corre.
-- date_format usa os códigos do MySQL; '%Y-%m' é igual ao do DuckDB.
-- Resultado agregado: uma linha por mês (267 no small; ~340 no 32M).
--
-- Parâmetros: ${ratings}
SELECT date_format(from_unixtime(r."timestamp"), '%Y-%m') AS mes,
       COUNT(*)      AS num_ratings,
       AVG(r.rating) AS media
FROM ${ratings} AS r
GROUP BY 1
ORDER BY 1
