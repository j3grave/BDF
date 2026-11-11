-- filmes_ano.sql (Athena) - equivalente a sql/analise/filmes_ano.sql
-- Origem: notebook do Luís, célula 112 ("novo-advanced"), consulta "filmes_ano".
--
-- Mesmas CTEs de sql/athena/analise/evolucao_filmes.sql (só anos completos); os dois filmes
-- são escolhidos com ROW_NUMBER() (em vez de UNION de subqueries com LIMIT).
-- Fuso horário: from_unixtime devolve UTC.
-- Resultado agregado: uma linha por (filme, ano), para 2 filmes (dezenas de linhas).
--
-- Parâmetros: ${ratings}, ${movies}
WITH limites AS (SELECT MAX(r.year) AS ano_max, MAX(r."timestamp") AS ts_max FROM ${ratings} AS r),
     fim AS (SELECT CASE WHEN month(from_unixtime(ts_max)) = 12 AND day(from_unixtime(ts_max)) = 31
                         THEN ano_max ELSE ano_max - 1 END AS ano,
                    ano_max,
                    date_format(from_unixtime(ts_max), '%Y-%m-%d') AS ultimo_dia
             FROM limites),
     s AS (SELECT r.movieid,
                  COUNT(*)      FILTER (WHERE r.year BETWEEN f.ano - 9 AND f.ano - 5) AS n_anterior,
                  COUNT(*)      FILTER (WHERE r.year BETWEEN f.ano - 4 AND f.ano)     AS n_recente,
                  AVG(r.rating) FILTER (WHERE r.year BETWEEN f.ano - 9 AND f.ano - 5) AS media_anterior,
                  AVG(r.rating) FILTER (WHERE r.year BETWEEN f.ano - 4 AND f.ano)     AS media_recente
           FROM ${ratings} AS r CROSS JOIN fim AS f
           WHERE r.year BETWEEN f.ano - 9 AND f.ano
           GROUP BY r.movieid),
     e AS (SELECT s.*, media_recente - media_anterior AS variacao,
                  RANK() OVER (ORDER BY media_anterior DESC) AS posicao_anterior,
                  RANK() OVER (ORDER BY media_recente DESC)  AS posicao_recente
           FROM s
           WHERE n_anterior >= 10 AND n_recente >= 10),
     sobe AS (SELECT movieid, ROW_NUMBER() OVER (ORDER BY variacao DESC, movieid) AS k FROM e WHERE variacao >= 0.5),
     desce AS (SELECT movieid, ROW_NUMBER() OVER (ORDER BY variacao, movieid) AS k FROM e WHERE variacao <= -0.5),
     escolhidos AS (SELECT movieid, 'Maior subida' AS tipo FROM sobe WHERE k = 1
                    UNION ALL
                    SELECT movieid, 'Maior descida' AS tipo FROM desce WHERE k = 1)
SELECT r.movieid, m.title, x.tipo, r.year AS ano, COUNT(*) AS avaliacoes, AVG(r.rating) AS media
FROM ${ratings} AS r
JOIN escolhidos AS x ON r.movieid = x.movieid
JOIN ${movies} AS m ON r.movieid = m.movieid
GROUP BY r.movieid, m.title, x.tipo, r.year
ORDER BY r.movieid, r.year
