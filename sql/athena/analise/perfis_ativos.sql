-- perfis_ativos.sql (Athena) - equivalente a sql/analise/perfis_ativos.sql
-- Origem: notebook do Luís, célula 109 ("novo-analytics"), consultas_complementares()["perfis_ativos"].
--
-- Fuso horário: year vem das pastas de ratings_part ou de year(from_unixtime("timestamp")),
-- e from_unixtime devolve UTC.
-- Diferenças para o original: count_if em vez de SUM((cond)::BIGINT); janela por extenso
-- (sem a cláusula WINDOW); GROUP BY 1, 2 (o Trino não aceita aliases no GROUP BY).
-- Resultado agregado: no máximo 3 linhas por ano.
--
-- Parâmetros: ${ratings}
WITH y AS (SELECT r.userid, r.year AS ano, COUNT(*) AS n,
                  count_if(r.rating = floor(r.rating))  AS inteiros,
                  count_if(r.rating <> floor(r.rating)) AS nao_inteiros
           FROM ${ratings} AS r
           GROUP BY r.userid, r.year),
     c AS (SELECT ano,
                  SUM(n)            OVER (PARTITION BY userid ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS total,
                  SUM(inteiros)     OVER (PARTITION BY userid ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS i,
                  SUM(nao_inteiros) OVER (PARTITION BY userid ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ni
           FROM y)
SELECT ano,
       CASE WHEN ni = 0 THEN 'Só inteiros' WHEN i = 0 THEN 'Só não inteiros' ELSE 'Misto' END AS perfil,
       COUNT(*) AS utilizadores
FROM c
WHERE total >= 2
GROUP BY 1, 2
ORDER BY 1, 2
