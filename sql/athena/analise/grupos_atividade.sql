-- grupos_atividade.sql (Athena) - equivalente a sql/analise/grupos_atividade.sql
-- Origem: notebook do Luís, célula 109 ("novo-analytics"), consultas_complementares()["grupos_atividade"].
--
-- Fuso horário: year vem das pastas de ratings_part ou de year(from_unixtime("timestamp")),
-- e from_unixtime devolve UTC.
-- Faixas fixas a partir de 20 (mínimo do MovieLens): 20–49, 50–99, 100–249, 250–999, 1000+.
-- Sem ANY_VALUE (join depois de agregar); GROUP BY com as colunas, sem aliases.
-- Resultado agregado: no máximo 5 linhas por ano.
--
-- Parâmetros: ${ratings}
WITH totais AS (SELECT r.userid, COUNT(*) AS total FROM ${ratings} AS r GROUP BY r.userid),
     u AS (SELECT r.userid, r.year AS ano, AVG(r.rating) AS media_utilizador, COUNT(*) AS n
           FROM ${ratings} AS r
           GROUP BY r.userid, r.year),
     g AS (SELECT u.ano, u.media_utilizador, u.n,
                  CASE WHEN t.total < 50 THEN 20 WHEN t.total < 100 THEN 50 WHEN t.total < 250 THEN 100
                       WHEN t.total < 1000 THEN 250 ELSE 1000 END AS faixa_min
           FROM u JOIN totais AS t ON u.userid = t.userid)
SELECT ano,
       faixa_min,
       CASE faixa_min WHEN 20 THEN '20–49' WHEN 50 THEN '50–99' WHEN 100 THEN '100–249'
                      WHEN 250 THEN '250–999' ELSE '1000 ou mais' END AS grupo,
       AVG(media_utilizador) AS media,
       COUNT(*)              AS utilizadores,
       SUM(n)                AS avaliacoes
FROM g
GROUP BY ano, faixa_min
ORDER BY ano, faixa_min
