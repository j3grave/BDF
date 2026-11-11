-- integridade.sql (Athena) - equivalente a sql/analise/integridade.sql
-- Origem: notebook do Luís, célula 109 ("novo-analytics"), consultas_complementares()["integridade"].
--
-- NOT EXISTS (portável) em vez de ANTI JOIN; colunas qualificadas.
-- Não usa o timestamp, por isso não há questões de fuso horário.
-- Resultado agregado: uma linha.
--
-- Parâmetros: ${ratings}, ${movies}
SELECT (SELECT COUNT(*) - COUNT(DISTINCT m.movieid) FROM ${movies} AS m)          AS ids_filmes_repetidos,
       (SELECT COUNT(*) FROM ${ratings} AS r
         WHERE NOT EXISTS (SELECT 1 FROM ${movies} AS m WHERE m.movieid = r.movieid)) AS ratings_sem_filme,
       (SELECT COUNT(DISTINCT r.movieid) FROM ${ratings} AS r
         WHERE NOT EXISTS (SELECT 1 FROM ${movies} AS m WHERE m.movieid = r.movieid)) AS filmes_sem_metadados,
       (SELECT COUNT(*) FROM ${movies} AS m WHERE m.title IS NULL OR m.genres IS NULL) AS filmes_com_nulos
