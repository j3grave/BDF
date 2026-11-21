-- anual.sql (DuckDB) - avaliações, média e utilizadores ativos por ano
--
-- Pergunta: como evolui, ano a ano, o volume de avaliações, a média e o n.º de utilizadores
-- que avaliaram pelo menos um filme nesse ano?
--
-- Notas:
-- - o ano é a coluna year de ${ratings}, calculada em UTC com epoch_ms; no Parquet
--   particionado vem do nome das pastas e o timestamp nem é lido;
-- - é parecida com sql/05_ratings_por_ano.sql (a do benchmark), mas acrescenta os
--   utilizadores ativos e não arredonda a média.
--
-- Parâmetros: ${ratings}
SELECT year AS ano,
       COUNT(*)               AS num_ratings,
       AVG(rating)            AS media,
       COUNT(DISTINCT userId) AS utilizadores
FROM ${ratings}
GROUP BY year
ORDER BY year;
