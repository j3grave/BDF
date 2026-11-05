-- valores_ano.sql (DuckDB) - distribuição dos valores de rating em cada ano
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 108 (id "novo-queries"), consultas_sql()["valores_ano"]. Autor: Luís Pousada (e51d050).
--
-- Pergunta: quantas avaliações de cada valor (0,5 a 5) houve em cada ano? Mostra, por
-- exemplo, a partir de que ano aparecem os meios pontos.
--
-- Alterações face ao original: year de ${ratings} (UTC, fase 1) em vez de
-- year(to_timestamp(timestamp)), que depende do fuso da sessão (relatório, P1).
--
-- Parâmetros: ${ratings}
SELECT year AS ano, rating, COUNT(*) AS num_ratings
FROM ${ratings}
GROUP BY year, rating
ORDER BY year, rating;
