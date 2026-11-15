-- 01_generos.sql (Athena) - equivalente a sql/01_generos.sql
-- Pergunta 7.1: quais são os géneros de filmes no dataset?
--
-- Diferença para o DuckDB: em Trino/Athena, partir uma lista em linhas faz-se com
-- CROSS JOIN UNNEST(...) AS t(coluna), em vez de unnest() dentro do SELECT.
-- O Athena cobra no mínimo 10 MB por query, e movies tem ~1.4 MB: esta query paga o mínimo.
--
-- Parâmetros: ${movies}
SELECT DISTINCT t.genre
FROM ${movies} AS m
CROSS JOIN UNNEST(split(m.genres, '|')) AS t(genre)
ORDER BY t.genre
