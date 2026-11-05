-- distribuicao.sql (Athena) - equivalente a sql/analise/distribuicao.sql
-- Origem: notebook do Luís, célula 108 ("novo-queries"), consultas_sql()["distribuicao"].
--
-- Resultado agregado (no máximo 10 linhas, uma por valor). A tabela (utilizador, valor), que no
-- 32M teria ~1,5 M linhas, só existe como CTE e nunca é devolvida ao cliente.
-- Divisões: sempre com CAST(... AS double). No Trino, bigint / bigint é divisão inteira e
-- uma divisão com um literal decimal (100.0 * x / y) fica com a escala do literal (1 casa).
-- Não usa o timestamp, por isso não há questões de fuso horário.
--
-- Parâmetros: ${ratings}
WITH d AS (SELECT r.userid, r.rating, COUNT(*) AS n FROM ${ratings} AS r GROUP BY r.userid, r.rating),
     t AS (SELECT d.userid, SUM(d.n) AS total FROM d GROUP BY d.userid),
     g AS (SELECT COUNT(*) AS utilizadores, SUM(t.total) AS avaliacoes FROM t)
SELECT d.rating,
       COUNT(*)                                                    AS utilizadores_que_usam,
       100 * CAST(COUNT(*) AS double) / g.utilizadores             AS pct_utilizadores,
       SUM(d.n)                                                    AS num_ratings,
       100 * CAST(SUM(d.n) AS double) / g.avaliacoes               AS pct_ratings,
       SUM(CAST(d.n AS double) / t.total) / g.utilizadores         AS prop_media_utilizador
FROM d JOIN t ON d.userid = t.userid CROSS JOIN g
GROUP BY d.rating, g.utilizadores, g.avaliacoes
ORDER BY d.rating
