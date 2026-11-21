-- filmes_ano.sql (DuckDB) - série anual do filme que mais subiu e do que mais desceu (para gráfico)
--
-- Pergunta: como evoluiu, ano a ano, a média do filme com a maior subida (variação >= 0,5) e
-- do filme com a maior descida (variação <= -0,5) de evolucao_filmes?
--
-- Notas:
-- - os filmes são escolhidos como em evolucao_filmes.sql (só anos completos); as CTEs
--   limites/fim/s/e são as mesmas;
-- - ROW_NUMBER() em CTEs escolhe um filme de cada tipo (portável para o Athena), com a
--   coluna tipo;
-- - o ano é a coluna year de ${ratings} (UTC).
-- A série usa todos os anos com avaliações desses filmes.
--
-- Parâmetros: ${ratings}, ${movies}
WITH limites AS (SELECT MAX(year) AS ano_max, MAX(timestamp) AS ts_max FROM ${ratings}),
     fim AS (SELECT CASE WHEN month(epoch_ms(ts_max * 1000)) = 12 AND day(epoch_ms(ts_max * 1000)) = 31
                         THEN ano_max ELSE ano_max - 1 END AS ano,
                    ano_max,
                    strftime(epoch_ms(ts_max * 1000), '%Y-%m-%d') AS ultimo_dia
             FROM limites),
     s AS (SELECT r.movieId,
                  COUNT(*)      FILTER (WHERE r.year BETWEEN f.ano - 9 AND f.ano - 5) AS n_anterior,
                  COUNT(*)      FILTER (WHERE r.year BETWEEN f.ano - 4 AND f.ano)     AS n_recente,
                  AVG(r.rating) FILTER (WHERE r.year BETWEEN f.ano - 9 AND f.ano - 5) AS media_anterior,
                  AVG(r.rating) FILTER (WHERE r.year BETWEEN f.ano - 4 AND f.ano)     AS media_recente
           FROM ${ratings} r CROSS JOIN fim f
           WHERE r.year BETWEEN f.ano - 9 AND f.ano
           GROUP BY r.movieId),
     e AS (SELECT s.*, media_recente - media_anterior AS variacao,
                  RANK() OVER (ORDER BY media_anterior DESC) AS posicao_anterior,
                  RANK() OVER (ORDER BY media_recente DESC)  AS posicao_recente
           FROM s
           WHERE n_anterior >= 10 AND n_recente >= 10),
     sobe AS (SELECT movieId, ROW_NUMBER() OVER (ORDER BY variacao DESC, movieId) AS k FROM e WHERE variacao >= 0.5),
     desce AS (SELECT movieId, ROW_NUMBER() OVER (ORDER BY variacao, movieId) AS k FROM e WHERE variacao <= -0.5),
     escolhidos AS (SELECT movieId, 'Maior subida' AS tipo FROM sobe WHERE k = 1
                    UNION ALL
                    SELECT movieId, 'Maior descida' AS tipo FROM desce WHERE k = 1)
SELECT r.movieId, m.title, x.tipo, r.year AS ano, COUNT(*) AS avaliacoes, AVG(r.rating) AS media
FROM ${ratings} r
JOIN escolhidos x ON r.movieId = x.movieId
JOIN ${movies} m ON r.movieId = m.movieId
GROUP BY r.movieId, m.title, x.tipo, r.year
ORDER BY r.movieId, ano;
