-- perfis_ativos.sql (DuckDB) - por ano, utilizadores ativos com histórico só de inteiros,
-- só de não inteiros ou misto
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 109 (id "novo-analytics"), consultas_complementares()["perfis_ativos"]. Autor: Luís Pousada (e51d050).
--
-- Pergunta: entre os utilizadores que avaliaram em cada ano (e com pelo menos 2 avaliações
-- acumuladas até esse ano), quantos usaram até aí só estrelas inteiras, só valores não
-- inteiros (x,5) ou os dois?
--
-- Alterações face ao original:
-- - year de ${ratings} (UTC) em vez de year(to_timestamp(timestamp)) (fuso, P1);
-- - count_if(cond) em vez de SUM((cond)::BIGINT) e janela escrita por extenso em vez da
--   cláusula WINDOW, para ficar igual à versão Athena;
-- - rótulo "Só não inteiros" (P8: um 0,5 não é um "meio ponto" de um inteiro).
-- A lógica é a do original.
--
-- Parâmetros: ${ratings}
WITH y AS (SELECT userId, year AS ano, COUNT(*) AS n,
                  count_if(rating = floor(rating))  AS inteiros,
                  count_if(rating != floor(rating)) AS nao_inteiros
           FROM ${ratings}
           GROUP BY userId, year),
     c AS (SELECT ano,
                  SUM(n)            OVER (PARTITION BY userId ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS total,
                  SUM(inteiros)     OVER (PARTITION BY userId ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS i,
                  SUM(nao_inteiros) OVER (PARTITION BY userId ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ni
           FROM y)
SELECT ano,
       CASE WHEN ni = 0 THEN 'Só inteiros' WHEN i = 0 THEN 'Só não inteiros' ELSE 'Misto' END AS perfil,
       COUNT(*) AS utilizadores
FROM c
WHERE total >= 2
GROUP BY 1, 2
ORDER BY 1, 2;
