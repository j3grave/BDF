-- valores_ano.sql (DuckDB) - distribuição dos valores de rating em cada ano
--
-- Pergunta: quantas avaliações de cada valor (0,5 a 5) houve em cada ano? Mostra, por
-- exemplo, a partir de que ano aparecem os meios pontos.
--
-- O ano é a coluna year de ${ratings} (UTC). Com year(to_timestamp(timestamp)) dependeria
-- do fuso da sessão.
--
-- Parâmetros: ${ratings}
SELECT year AS ano, rating, COUNT(*) AS num_ratings
FROM ${ratings}
GROUP BY year, rating
ORDER BY year, rating;
