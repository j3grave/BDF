-- 01_generos.sql
-- Pergunta 7.1: quais são os géneros de filmes no dataset?
--
-- Como funciona: a coluna genres guarda vários géneros num só texto ("Action|Comedy").
-- string_split parte o texto numa lista e unnest transforma cada elemento da lista
-- numa linha; DISTINCT fica com cada género uma só vez.
--
-- Ligação às aulas:
-- - Formato colunar: o Parquet guarda cada coluna em separado. Esta query só usa
--   genres, por isso o DuckDB lê só essa coluna do ficheiro e ignora movieId e title
--   (projection pushdown).
-- - Partições: não se aplicam; só usa movies, que não está particionado.
--
-- Parâmetros: ${movies} (substituído pela leitura do Parquet em 03_benchmark.py)
SELECT DISTINCT genre
FROM (SELECT unnest(string_split(genres, '|')) AS genre FROM ${movies})
ORDER BY genre;
