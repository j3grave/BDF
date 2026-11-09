-- qualidade.sql (Athena) - equivalente a sql/analise/qualidade.sql
-- Origem: notebook do Luís, célula 108 ("novo-queries"), consultas_sql()["qualidade"].
--
-- Diferenças para o DuckDB:
-- - COUNT(DISTINCT (a, b)) não existe no Trino: os pares distintos contam-se numa subquery
--   (lê ratings duas vezes; no 32M em Parquet são ~320 MB, ~0,002 USD);
-- - count_if(cond) em vez de COUNT(*) FILTER (WHERE cond) (os dois funcionam no Trino);
-- - "timestamp" entre aspas (palavra reservada).
-- Não converte o timestamp, por isso não há questões de fuso horário.
-- Resultado agregado: uma linha.
--
-- Parâmetros: ${ratings}
SELECT COUNT(*)                 AS linhas,
       COUNT(DISTINCT r.userid) AS utilizadores,
       COUNT(DISTINCT r.movieid) AS filmes,
       COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT d.userid, d.movieid FROM ${ratings} AS d) AS pares)
                                AS pares_repetidos,
       count_if(r.userid IS NULL OR r.movieid IS NULL OR r.rating IS NULL OR r."timestamp" IS NULL)
                                AS linhas_com_nulos,
       count_if(r.rating < 0.5 OR r.rating > 5 OR r.rating * 2 <> floor(r.rating * 2))
                                AS fora_dominio_comum,
       count_if(r.rating <> floor(r.rating)) AS nao_inteiros,
       count_if(r.rating < 1)   AS inferior_a_um
FROM ${ratings} AS r
