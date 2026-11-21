-- integridade.sql (DuckDB) - chaves e relações entre ratings e movies
--
-- Pergunta: movies tem ids repetidos? Há avaliações de filmes que não existem em movies?
-- O 04_analise.py falha se ids_filmes_repetidos ou ratings_sem_filme forem diferentes de 0.
--
-- Notas:
-- - ratings_sem_filme conta linhas de avaliações sem filme em movies; filmes_sem_metadados
--   conta filmes distintos (COUNT(DISTINCT movieId));
-- - NOT EXISTS em vez de ANTI JOIN (só existe no DuckDB), igual no Athena.
--
-- Parâmetros: ${ratings}, ${movies}
SELECT (SELECT COUNT(*) - COUNT(DISTINCT movieId) FROM ${movies})               AS ids_filmes_repetidos,
       (SELECT COUNT(*) FROM ${ratings} r
         WHERE NOT EXISTS (SELECT 1 FROM ${movies} m WHERE m.movieId = r.movieId))  AS ratings_sem_filme,
       (SELECT COUNT(DISTINCT r.movieId) FROM ${ratings} r
         WHERE NOT EXISTS (SELECT 1 FROM ${movies} m WHERE m.movieId = r.movieId))  AS filmes_sem_metadados,
       (SELECT COUNT(*) FROM ${movies} WHERE title IS NULL OR genres IS NULL)       AS filmes_com_nulos;
