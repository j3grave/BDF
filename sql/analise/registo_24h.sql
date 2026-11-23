-- registo_24h.sql (DuckDB) - o que acontece nas primeiras 24 h de cada utilizador
--
-- Pergunta: quantos utilizadores avaliam pelo menos 20 filmes logo no registo, e em quanto tempo?
-- Justifica que a regra A de 10_flag_bots.sql ignore as primeiras 24 h: o site pedia avaliações
-- ao criar a conta e o GroupLens só inclui utilizadores com 20 ou mais, por isso um pico de
-- atividade no registo é o comportamento normal e não distingue um bot de uma pessoa.
--
-- Colunas (percentagens sobre todos os utilizadores):
--   pct_20_nas_24h          com >= 20 avaliações nas primeiras 24 h
--   pct_20a_em_10min        chegam à 20.ª avaliação em menos de 10 min desde a primeira
--   pct_20a_em_1h           chegam à 20.ª avaliação em menos de 1 h
--   mediana_min_ate_20a     tempo mediano (minutos) entre a 1.ª e a 20.ª avaliação
--   pct_tudo_nas_24h        com toda a atividade nas primeiras 24 h (a regra A não os vê)
--
-- Parâmetros: ${ratings}
WITH o AS (SELECT userId,
                  timestamp - MIN(timestamp) OVER (PARTITION BY userId)        AS desde_inicio_s,
                  ROW_NUMBER() OVER (PARTITION BY userId ORDER BY timestamp)   AS ordem
           FROM ${ratings}),
     u AS (SELECT userId,
                  count_if(desde_inicio_s < 86400)                AS nas_24h,
                  COUNT(*)                                        AS total,
                  MAX(desde_inicio_s) FILTER (WHERE ordem = 20)   AS ate_20a_s
           FROM o GROUP BY userId)
SELECT COUNT(*)                                                 AS utilizadores,
       ROUND(100.0 * count_if(nas_24h >= 20) / COUNT(*), 1)     AS pct_20_nas_24h,
       ROUND(100.0 * count_if(ate_20a_s < 600) / COUNT(*), 1)   AS pct_20a_em_10min,
       ROUND(100.0 * count_if(ate_20a_s < 3600) / COUNT(*), 1)  AS pct_20a_em_1h,
       ROUND(MEDIAN(ate_20a_s) / 60.0, 1)                       AS mediana_min_ate_20a,
       ROUND(100.0 * count_if(nas_24h = total) / COUNT(*), 1)   AS pct_tudo_nas_24h
FROM u;
