-- evolucao_filmes.sql (Athena) - equivalente a sql/analise/evolucao_filmes.sql
-- Origem: notebook do Luís, célula 112 ("novo-advanced"), SQL_AVANCADO["evolucao_filmes"].
--
-- Opção usada: só anos completos (o último ano só conta se o último rating for de 31/12;
-- senão o fim passa para o ano anterior). As colunas periodo_anterior, periodo_recente e
-- criterio indicam os anos usados e o ano excluído.
-- Fuso horário: from_unixtime devolve UTC; year vem das pastas de ratings_part ou de
-- year(from_unixtime("timestamp")). O WHERE nos 10 anos permite partition pruning em ratings_part.
-- Tamanho do resultado: uma linha por filme com >= 10 avaliações em cada período (366 no
-- small; no 32M fica limitado ao n.º de filmes, dezenas de milhares no máximo, poucos MB).
-- É um resultado agregado (por filme) e não leva LIMIT, porque a análise usa os dois
-- extremos e a distribuição completa da variação.
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
           WHERE n_anterior >= 10 AND n_recente >= 10)
SELECT e.movieid, m.title, e.n_anterior, e.n_recente, e.media_anterior, e.media_recente,
       e.variacao, e.posicao_anterior, e.posicao_recente,
       CAST(f.ano - 9 AS varchar) || '–' || CAST(f.ano - 5 AS varchar) AS periodo_anterior,
       CAST(f.ano - 4 AS varchar) || '–' || CAST(f.ano AS varchar)     AS periodo_recente,
       CASE WHEN f.ano < f.ano_max
            THEN 'só anos completos: exclui ' || CAST(f.ano_max AS varchar) || ' (parcial, último rating ' || f.ultimo_dia || ')'
            ELSE 'só anos completos: o último ano está completo' END AS criterio
FROM e CROSS JOIN fim AS f
JOIN ${movies} AS m ON e.movieid = m.movieid
ORDER BY e.variacao DESC, e.movieid
