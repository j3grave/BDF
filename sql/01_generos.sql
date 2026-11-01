-- Pergunta 7.1: quais são os géneros de filmes no dataset?
-- Parâmetros: ${movies} (substituído pela leitura do Parquet em 03_benchmark.py)
SELECT DISTINCT genre
FROM (SELECT unnest(string_split(genres, '|')) AS genre FROM ${movies})
ORDER BY genre;
