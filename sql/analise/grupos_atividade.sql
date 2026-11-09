-- grupos_atividade.sql (DuckDB) - média anual por faixa de atividade total do utilizador
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 109 (id "novo-analytics"), consultas_complementares()["grupos_atividade"]. Autor: Luís Pousada (e51d050).
--
-- Pergunta: os utilizadores mais ativos (no total do seu histórico) dão notas diferentes dos
-- menos ativos? Média, em cada ano, das médias dos utilizadores de cada faixa.
--
-- Alterações face ao original (relatório, P1 e P4):
-- - faixas novas. O MovieLens só inclui utilizadores com pelo menos 20 avaliações, por isso
--   as faixas originais "Até 5" e "6–20" ficavam sempre vazias (ou só com quem tinha
--   exatamente 20). Faixas fixas a partir de 20, iguais em todos os datasets (para os
--   comparar): 20–49, 50–99, 100–249, 250–999 e 1000 ou mais. Utilizadores por faixa:
--   small 225/137/143/93/12; 1M 1743/1352/1720/1184/41; no 32M (mediana 73, p90 364,
--   máximo 33 332) também nenhuma fica vazia;
-- - faixa_min (limite inferior) para ordenar as faixas corretamente;
-- - ANY_VALUE (não existe no Athena) substituído por um join depois de agregar;
-- - year de ${ratings} (UTC) em vez de year(to_timestamp(timestamp)) (fuso).
-- A coluna utilizadores conta pares (utilizador, ano) da faixa nesse ano: é o n.º de
-- utilizadores da faixa ativos nesse ano.
--
-- Parâmetros: ${ratings}
WITH totais AS (SELECT userId, COUNT(*) AS total FROM ${ratings} GROUP BY userId),
     u AS (SELECT userId, year AS ano, AVG(rating) AS media_utilizador, COUNT(*) AS n
           FROM ${ratings}
           GROUP BY userId, year),
     g AS (SELECT u.ano, u.media_utilizador, u.n,
                  CASE WHEN t.total < 50 THEN 20 WHEN t.total < 100 THEN 50 WHEN t.total < 250 THEN 100
                       WHEN t.total < 1000 THEN 250 ELSE 1000 END AS faixa_min
           FROM u JOIN totais t ON u.userId = t.userId)
SELECT ano,
       faixa_min,
       CASE faixa_min WHEN 20 THEN '20–49' WHEN 50 THEN '50–99' WHEN 100 THEN '100–249'
                      WHEN 250 THEN '250–999' ELSE '1000 ou mais' END AS grupo,
       AVG(media_utilizador) AS media,
       COUNT(*)              AS utilizadores,
       SUM(n)                AS avaliacoes
FROM g
GROUP BY ano, faixa_min
ORDER BY ano, faixa_min;
