-- integridade.sql (DuckDB) - chaves e relações entre ratings e movies
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 109 (id "novo-analytics"), consultas_complementares()["integridade"]. Autor: Luís Pousada (e51d050).
--
-- Pergunta: movies tem ids repetidos? Há avaliações de filmes que não existem em movies?
-- O 05_analises.py falha se ids_filmes_repetidos ou ratings_sem_filme forem diferentes de 0.
--
-- Alterações face ao original (relatório, P5):
-- - o original chamava filmes_sem_metadados a um COUNT(*) de "ratings ANTI JOIN movies", ou
--   seja, contava LINHAS de avaliações, não filmes. Passa a haver duas colunas:
--   ratings_sem_filme (linhas) e filmes_sem_metadados (COUNT(DISTINCT movieId));
-- - NOT EXISTS em vez de ANTI JOIN (só existe no DuckDB), igual no Athena.
--
-- Parâmetros: ${ratings}, ${movies}
SELECT (SELECT COUNT(*) - COUNT(DISTINCT movieId) FROM ${movies})               AS ids_filmes_repetidos,
       (SELECT COUNT(*) FROM ${ratings} r
         WHERE NOT EXISTS (SELECT 1 FROM ${movies} m WHERE m.movieId = r.movieId))  AS ratings_sem_filme,
       (SELECT COUNT(DISTINCT r.movieId) FROM ${ratings} r
         WHERE NOT EXISTS (SELECT 1 FROM ${movies} m WHERE m.movieId = r.movieId))  AS filmes_sem_metadados,
       (SELECT COUNT(*) FROM ${movies} WHERE title IS NULL OR genres IS NULL)       AS filmes_com_nulos;
