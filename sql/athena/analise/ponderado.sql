-- ponderado.sql (Athena) - equivalente a sql/analise/ponderado.sql
-- Origem: notebook do Luís, célula 108 ("novo-queries"), consultas_sql()["ponderado"].
--
-- Diferenças para o DuckDB:
-- - CAST(... AS double) nas duas frações: no Athena (Trino), bigint / bigint é divisão
--   inteira e daria 0 sem erro (era o problema da versão da célula 90), e 100.0 / bigint
--   seria uma divisão decimal arredondada à escala do literal (1 casa);
-- - JOIN ... ON com nomes qualificados; os nomes de colunas saem em minúsculas.
-- LIMIT 10 justificado: é um top 10 (a pergunta pede só os 10 primeiros).
-- Não usa o timestamp, por isso não há questões de fuso horário.
--
-- Parâmetros: ${ratings}, ${movies} (substituídos como em scripts/athena_benchmark.py)
WITH s AS (SELECT r.movieid, AVG(r.rating) AS media_filme, COUNT(*) AS v
           FROM ${ratings} AS r GROUP BY r.movieid),
     p AS (SELECT AVG(r.rating) AS media_global FROM ${ratings} AS r)
SELECT s.movieid, m.title, s.media_filme AS avg_rating, s.v AS num_ratings,
       CAST(s.v AS double) / (s.v + 100) * s.media_filme
         + CAST(100 AS double) / (s.v + 100) * p.media_global AS weighted,
       p.media_global
FROM s CROSS JOIN p
JOIN ${movies} AS m ON s.movieid = m.movieid
ORDER BY weighted DESC, s.movieid
LIMIT 10
