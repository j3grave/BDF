-- mensal.sql (DuckDB) - avaliações e média por mês
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 109 (id "novo-analytics"), consultas_complementares()["mensal"]. Autor: Luís Pousada (e51d050).
--
-- Pergunta: como se distribuem as avaliações ao longo dos meses (picos, lacunas)?
--
-- Alterações face ao original:
-- - strftime(to_timestamp(timestamp), ...) passa a strftime(epoch_ms(timestamp * 1000), ...).
--   to_timestamp devolve TIMESTAMP WITH TIME ZONE e o mês dependia do fuso da sessão: em
--   America/New_York ou Asia/Tokyo o original dava outros números (relatório, P1, e
--   testes do bloco 1). epoch_ms devolve TIMESTAMP sem fuso, ou seja, UTC;
-- - GROUP BY 1 em vez do alias.
--
-- Parâmetros: ${ratings}
SELECT strftime(epoch_ms(timestamp * 1000), '%Y-%m') AS mes,
       COUNT(*)    AS num_ratings,
       AVG(rating) AS media
FROM ${ratings}
GROUP BY 1
ORDER BY 1;
