-- 08_segmentos.sql (DuckDB) - P2: que diferenças há entre os tipos de utilizadores?
--
-- LIMITAÇÃO: o IMDb só publica agregados por filme (nota média e n.º de votos), não tem
-- dados por utilizador. Por isso não se comparam utilizadores do IMDb com utilizadores do
-- MovieLens: segmentam-se os utilizadores do MovieLens e vê-se quanto cada segmento concorda
-- com a nota (agregada) do IMDb.
--
-- Segmentos (três tipos, cada utilizador está num segmento de cada tipo):
-- - atividade: n.º total de avaliações do utilizador, nas faixas do grupos_atividade.sql
--   (20–49, 50–99, 100–249, 250–999, 1000 ou mais);
-- - era: data da primeira avaliação (aproximação da data de registo), antes ou a partir de
--   18/02/2003, quando o MovieLens passou a ter meias estrelas (${corte_era} = esse instante
--   em segundos desde 1970, UTC);
-- - bots: sinalizados ou não pelo sql/analise/10_flag_bots.sql (regras A e B).
--   *** PROVISÓRIO: as regras ainda estão a ser validadas pelo Luís. ***
--
-- Como funciona:
-- 1. por_filme: nota média de cada segmento em cada filme (só avaliações desse segmento).
-- 2. elegiveis: pares (segmento, filme) com pelo menos ${min_seg} avaliações do segmento e
--    com nota no IMDb (pelo menos ${min_imdb} votos).
-- 3. comuns: para cada tipo, os filmes elegíveis em TODOS os segmentos desse tipo. Assim os
--    segmentos comparam-se sobre o mesmo conjunto de filmes; senão, um segmento podia parecer
--    mais "de acordo" só por avaliar filmes diferentes.
-- 4. Por segmento: gap médio (IMDb - segmento) com IC 95%, Pearson e Spearman.
--
-- Parâmetros: ${ratings}, ${filmes}, ${flag_bots}, ${min_seg}, ${min_imdb}, ${corte_era}
WITH u AS (
    SELECT userId, COUNT(*) AS total, MIN(timestamp) AS primeiro_ts
    FROM ${ratings}
    GROUP BY userId
),
seg AS (
    SELECT userId, 'atividade' AS tipo,
           CASE WHEN total < 50 THEN '20–49' WHEN total < 100 THEN '50–99' WHEN total < 250 THEN '100–249'
                WHEN total < 1000 THEN '250–999' ELSE '1000 ou mais' END AS segmento,
           CASE WHEN total < 50 THEN 1 WHEN total < 100 THEN 2 WHEN total < 250 THEN 3
                WHEN total < 1000 THEN 4 ELSE 5 END AS ordem
    FROM u
    UNION ALL
    SELECT userId, 'era',
           CASE WHEN primeiro_ts < ${corte_era} THEN 'antes de 18/02/2003' ELSE 'a partir de 18/02/2003' END,
           CASE WHEN primeiro_ts < ${corte_era} THEN 1 ELSE 2 END
    FROM u
    UNION ALL
    SELECT userId, 'bots (PROVISÓRIO)',
           CASE WHEN classificacao LIKE 'suspeito%' THEN 'sinalizados' ELSE 'não sinalizados' END,
           CASE WHEN classificacao LIKE 'suspeito%' THEN 2 ELSE 1 END
    FROM ${flag_bots}
),
utilizadores AS (
    SELECT tipo, segmento, ordem, COUNT(*) AS utilizadores
    FROM seg
    GROUP BY tipo, segmento, ordem
),
n_segmentos AS (
    SELECT tipo, COUNT(*) AS n FROM utilizadores GROUP BY tipo
),
por_filme AS (
    SELECT s.tipo, s.segmento, r.movieId, COUNT(*) AS n, AVG(r.rating) * 2 AS nota_seg_10
    FROM ${ratings} r
    JOIN seg s ON s.userId = r.userId
    GROUP BY s.tipo, s.segmento, r.movieId
),
elegiveis AS (
    SELECT p.tipo, p.segmento, p.movieId, p.n, p.nota_seg_10, f.nota_imdb,
           f.nota_imdb - p.nota_seg_10 AS gap
    FROM por_filme p
    JOIN ${filmes} f ON f.movieId = p.movieId
    WHERE p.n >= ${min_seg} AND f.nota_imdb IS NOT NULL AND f.votos_imdb >= ${min_imdb}
),
comuns AS (
    -- um filme é comum se for elegível em tantos segmentos quantos os do tipo
    SELECT e.tipo, e.movieId
    FROM elegiveis e
    JOIN n_segmentos s ON s.tipo = e.tipo
    GROUP BY e.tipo, e.movieId
    HAVING COUNT(*) = MAX(s.n)
),
r AS (
    SELECT e.tipo, e.segmento, e.n, e.nota_seg_10, e.nota_imdb, e.gap,
           rank() OVER (PARTITION BY e.tipo, e.segmento ORDER BY e.nota_seg_10)
             + (COUNT(*) OVER (PARTITION BY e.tipo, e.segmento, e.nota_seg_10) - 1) / 2.0 AS rank_seg,
           rank() OVER (PARTITION BY e.tipo, e.segmento ORDER BY e.nota_imdb)
             + (COUNT(*) OVER (PARTITION BY e.tipo, e.segmento, e.nota_imdb) - 1) / 2.0   AS rank_imdb
    FROM elegiveis e
    JOIN comuns c ON c.tipo = e.tipo AND c.movieId = e.movieId
),
metricas AS (
    SELECT tipo, segmento,
           COUNT(*)                                              AS filmes_comuns,
           SUM(n)                                                AS avaliacoes,
           AVG(nota_seg_10)                                      AS media_segmento_10,
           AVG(nota_imdb)                                        AS media_imdb,
           AVG(gap)                                              AS gap_medio,
           AVG(gap) - 1.96 * STDDEV_SAMP(gap) / SQRT(COUNT(*))   AS gap_ic95_inf,
           AVG(gap) + 1.96 * STDDEV_SAMP(gap) / SQRT(COUNT(*))   AS gap_ic95_sup,
           AVG(ABS(gap))                                         AS gap_abs_medio,
           CORR(nota_seg_10, nota_imdb)                          AS pearson,
           CORR(rank_seg, rank_imdb)                             AS spearman
    FROM r
    GROUP BY tipo, segmento
)
-- LEFT JOIN: um segmento sem filmes comuns aparece na mesma, com as métricas vazias
SELECT u.tipo, u.segmento, u.ordem, u.utilizadores,
       COALESCE(m.filmes_comuns, 0) AS filmes_comuns, m.avaliacoes,
       m.media_segmento_10, m.media_imdb, m.gap_medio, m.gap_ic95_inf, m.gap_ic95_sup,
       m.gap_abs_medio, m.pearson, m.spearman
FROM utilizadores u
LEFT JOIN metricas m ON m.tipo = u.tipo AND m.segmento = u.segmento
ORDER BY u.tipo, u.ordem;
