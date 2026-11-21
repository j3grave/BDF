-- mensal.sql (DuckDB) - avaliações e média por mês
--
-- Pergunta: como se distribuem as avaliações ao longo dos meses (picos, lacunas)?
--
-- Notas:
-- - o mês vem de strftime(epoch_ms(timestamp * 1000), ...), que dá TIMESTAMP sem fuso (UTC).
--   Com to_timestamp, o mês dependeria do fuso da sessão (em America/New_York ou Asia/Tokyo
--   os números mudavam);
-- - GROUP BY 1 em vez do alias.
--
-- Parâmetros: ${ratings}
SELECT strftime(epoch_ms(timestamp * 1000), '%Y-%m') AS mes,
       COUNT(*)    AS num_ratings,
       AVG(rating) AS media
FROM ${ratings}
GROUP BY 1
ORDER BY 1;
