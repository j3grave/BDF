-- perfis_cumulativos.sql (DuckDB) - perfis de uso da escala na população acumulada
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 109 (id "novo-analytics"), consultas_complementares()["perfis_cumulativos"]. Autor: Luís Pousada (e51d050).
--
-- Pergunta: como perfis_ativos, mas cada utilizador conta em todos os anos desde que entrou
-- (mesmo nos anos sem atividade), com o histórico acumulado até esse ano.
--
-- Alterações face ao original:
-- - year de ${ratings} (UTC) em vez de year(to_timestamp(timestamp)) (fuso, P1);
-- - count_if, janela por extenso e GROUP BY 1, 2, como na versão Athena;
-- - rótulo "Só não inteiros" (P8).
-- A grelha utilizadores x anos é intencional (no 32M, 200 948 x 29 = 5,8 M linhas), mas só
-- existe como CTE: o resultado devolvido é agregado (no máximo 3 linhas por ano).
--
-- Parâmetros: ${ratings}
WITH limites AS (SELECT MIN(year) AS a, MAX(year) AS b FROM ${ratings}),
     anos AS (SELECT unnest(range(a, b + 1)) AS ano FROM limites),
     y AS (SELECT userId, year AS ano,
                  count_if(rating = floor(rating))  AS i,
                  count_if(rating != floor(rating)) AS ni
           FROM ${ratings}
           GROUP BY userId, year),
     grelha AS (SELECT u.userId, a.ano, COALESCE(y.i, 0) AS i, COALESCE(y.ni, 0) AS ni
                FROM (SELECT DISTINCT userId FROM ${ratings}) u
                CROSS JOIN anos a
                LEFT JOIN y ON u.userId = y.userId AND a.ano = y.ano),
     c AS (SELECT ano,
                  SUM(i)  OVER (PARTITION BY userId ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS i,
                  SUM(ni) OVER (PARTITION BY userId ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ni
           FROM grelha)
SELECT ano,
       CASE WHEN ni = 0 THEN 'Só inteiros' WHEN i = 0 THEN 'Só não inteiros' ELSE 'Misto' END AS perfil,
       COUNT(*) AS utilizadores
FROM c
WHERE i + ni >= 2
GROUP BY 1, 2
ORDER BY 1, 2;
