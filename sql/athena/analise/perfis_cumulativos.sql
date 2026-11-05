-- perfis_cumulativos.sql (Athena) - equivalente a sql/analise/perfis_cumulativos.sql
-- Origem: notebook do Luís, célula 109 ("novo-analytics"), consultas_complementares()["perfis_cumulativos"].
--
-- Fuso horário: year vem das pastas de ratings_part ou de year(from_unixtime("timestamp")),
-- e from_unixtime devolve UTC.
-- Diferenças: UNNEST(sequence(a, b)) em vez de unnest(range(a, b + 1)); count_if; janela por
-- extenso; GROUP BY 1, 2.
-- A grelha utilizadores x anos (5,8 M linhas no 32M) fica dentro da query; o resultado
-- devolvido é agregado (no máximo 3 linhas por ano).
--
-- Parâmetros: ${ratings}
WITH limites AS (SELECT MIN(r.year) AS a, MAX(r.year) AS b FROM ${ratings} AS r),
     anos AS (SELECT t.ano FROM limites CROSS JOIN UNNEST(sequence(limites.a, limites.b)) AS t(ano)),
     y AS (SELECT r.userid, r.year AS ano,
                  count_if(r.rating = floor(r.rating))  AS i,
                  count_if(r.rating <> floor(r.rating)) AS ni
           FROM ${ratings} AS r
           GROUP BY r.userid, r.year),
     grelha AS (SELECT u.userid, a.ano, COALESCE(y.i, 0) AS i, COALESCE(y.ni, 0) AS ni
                FROM (SELECT DISTINCT r.userid FROM ${ratings} AS r) AS u
                CROSS JOIN anos AS a
                LEFT JOIN y ON u.userid = y.userid AND a.ano = y.ano),
     c AS (SELECT ano,
                  SUM(i)  OVER (PARTITION BY userid ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS i,
                  SUM(ni) OVER (PARTITION BY userid ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ni
           FROM grelha)
SELECT ano,
       CASE WHEN ni = 0 THEN 'Só inteiros' WHEN i = 0 THEN 'Só não inteiros' ELSE 'Misto' END AS perfil,
       COUNT(*) AS utilizadores
FROM c
WHERE i + ni >= 2
GROUP BY 1, 2
ORDER BY 1, 2
