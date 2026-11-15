-- anual.sql (DuckDB) - avaliações, média e utilizadores ativos por ano
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 108 (id "novo-queries"), consultas_sql()["anual"]. Autor: Luís Pousada (e51d050).
--
-- Pergunta: como evolui, ano a ano, o volume de avaliações, a média e o n.º de utilizadores
-- que avaliaram pelo menos um filme nesse ano?
--
-- Alterações face ao original:
-- - year(to_timestamp(timestamp)) passa a ser a coluna year de ${ratings}, calculada em UTC
--   com epoch_ms (fase 1). to_timestamp depende do fuso da sessão (ver o relatório, P1);
-- - no Parquet particionado, year vem do nome das pastas e o timestamp nem é lido.
-- Fica próxima de sql/05_ratings_por_ano.sql (que continua no benchmark); acrescenta os
-- utilizadores ativos e não arredonda a média.
--
-- Parâmetros: ${ratings}
SELECT year AS ano,
       COUNT(*)               AS num_ratings,
       AVG(rating)            AS media,
       COUNT(DISTINCT userId) AS utilizadores
FROM ${ratings}
GROUP BY year
ORDER BY year;
