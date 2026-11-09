-- evolucao_filmes.sql (DuckDB) - filmes cuja média mais subiu ou desceu entre dois períodos de 5 anos
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 112 (id "novo-advanced"), SQL_AVANCADO["evolucao_filmes"]. Autor: Luís Pousada (e51d050).
--
-- Pergunta: comparando os 5 anos anteriores com os 5 anos mais recentes, que filmes (com pelo
-- menos 10 avaliações em cada período) mudaram mais de média?
--
-- Alterações face ao original (relatório, P1 e P3):
-- - OPÇÃO USADA: SÓ ANOS COMPLETOS. O original terminava o período recente em MAX(ano), que é
--   um ano parcial (small: 2018 até 24/09; 32M: 2023 até 13/10; 1M: 2003 até 28/02), e
--   comparava 5 anos com pouco mais de 4. Aqui o último ano só conta se o último rating for
--   de 31 de dezembro (UTC); senão o fim passa para o ano anterior. Não se anualiza: as
--   médias de um ano parcial não precisam de anualização, mas o período ficaria desigual.
--   As colunas periodo_anterior, periodo_recente e criterio dizem, em cada linha, que anos
--   foram usados e que ano foi excluído;
-- - year de ${ratings} (UTC) em vez de year(to_timestamp(timestamp)) calculado 4 vezes por
--   linha (fuso, P1), e WHERE com os 10 anos usados (partition pruning no ratings_part);
-- - colunas pela ordem: movieId, title, contagens, médias, variação, posições, períodos.
-- No 1M (2000-04-25 a 2003-02-28) não há 10 anos completos: o resultado é vazio, como o
-- do original (que também não tinha dados no período anterior).
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
           WHERE n_anterior >= 10 AND n_recente >= 10)
SELECT e.movieId, m.title, e.n_anterior, e.n_recente, e.media_anterior, e.media_recente,
       e.variacao, e.posicao_anterior, e.posicao_recente,
       CAST(f.ano - 9 AS VARCHAR) || '–' || CAST(f.ano - 5 AS VARCHAR) AS periodo_anterior,
       CAST(f.ano - 4 AS VARCHAR) || '–' || CAST(f.ano AS VARCHAR)     AS periodo_recente,
       CASE WHEN f.ano < f.ano_max
            THEN 'só anos completos: exclui ' || CAST(f.ano_max AS VARCHAR) || ' (parcial, último rating ' || f.ultimo_dia || ')'
            ELSE 'só anos completos: o último ano está completo' END AS criterio
FROM e CROSS JOIN fim f
JOIN ${movies} m ON e.movieId = m.movieId
ORDER BY e.variacao DESC, e.movieId;
