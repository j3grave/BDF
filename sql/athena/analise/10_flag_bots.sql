-- 10_flag_bots.sql (Athena) - equivalente a sql/analise/10_flag_bots.sql
--
-- *** A VALIDAR COM O LUÍS *** - substitui utilizadores_sinalizados (notebook, célula 112).
-- A explicação das regras (eventos, submissão em lote, regras A e B, sinais complementares)
-- está no cabeçalho da versão DuckDB.
--
-- COMO CORRER: o resultado tem uma linha por utilizador (200 948 no 32M), por isso NÃO é
-- devolvido ao cliente. Corre-se como CTAS em Parquet, e as perguntas fazem-se sobre a tabela:
--   CREATE TABLE flag_bots
--   WITH (format = 'PARQUET', external_location = 's3://<bucket-resultados>/ctas/flag_bots/')
--   AS <esta query>
-- Depois: 10_flag_bots_calibracao.sql (uma linha) e eventos.sql leem ${flag_bots} = flag_bots.
--
-- Fuso horário: from_unixtime("timestamp") devolve UTC; os intervalos e as janelas usam o
-- timestamp em segundos, sem conversão.
-- Diferenças para o DuckDB:
-- - MEDIAN e quantile_cont não existem: approx_percentile(CAST(x AS double), p). É uma
--   aproximação; a mediana dos intervalos (inteiros) e os quantis podem diferir ligeiramente,
--   o que só importa para quem está exatamente no limiar;
-- - frações com CAST(... AS double) (no Trino, 100.0 * x / y teria só 1 casa decimal);
-- - approx_percentile(CASE WHEN fase THEN x END, p) em vez de FILTER (os agregados ignoram
--   NULL; é a forma mais portável);
-- - "timestamp" entre aspas; date_format(from_unixtime(...)) em vez de strftime(epoch_ms(...)).
-- A CONFIRMAR NA AWS: a janela RANGE BETWEEN CURRENT ROW AND 599 FOLLOWING (frame RANGE com
-- deslocamento numérico) é suportada pelas versões recentes do Trino; se o Athena a recusar,
-- a alternativa é um self-join dos eventos com e2.ts BETWEEN e1.ts AND e1.ts + 599.
--
-- Parâmetros: ${ratings}
WITH lim AS (SELECT 86400 AS registo_s,
                    100   AS regra_b_min_eventos,
                    2     AS regra_b_max_mediana_s,
                    10    AS lote_min_avaliacoes),
     ev AS (SELECT r.userid, r."timestamp" AS ts, COUNT(*) AS k
            FROM ${ratings} AS r
            GROUP BY r.userid, r."timestamp"),
     fase AS (SELECT ev.userid, ev.ts, ev.k,
                     ev.ts - MIN(ev.ts) OVER (PARTITION BY ev.userid) < l.registo_s AS no_registo
              FROM ev CROSS JOIN lim AS l),
     ritmo AS (SELECT fase.*,
                      ts - LAG(ts) OVER (PARTITION BY userid, no_registo ORDER BY ts) AS intervalo,
                      COUNT(*) OVER (PARTITION BY userid, no_registo ORDER BY ts
                                     RANGE BETWEEN CURRENT ROW AND 599 FOLLOWING)  AS eventos_10min
               FROM fase),
     por_eventos AS (SELECT userid,
                            COUNT(*)                                          AS eventos,
                            MAX(k)                                            AS max_avaliacoes_mesmo_segundo,
                            100 * CAST(count_if(k >= 2) AS double) / COUNT(*) AS pct_eventos_lote,
                            count_if(no_registo)                              AS eventos_registo,
                            approx_percentile(CASE WHEN no_registo THEN CAST(intervalo AS double) END, 0.5) AS mediana_intervalo_registo_s,
                            MAX(eventos_10min) FILTER (WHERE no_registo)      AS max_eventos_10min_registo,
                            count_if(NOT no_registo)                          AS eventos_apos_registo,
                            approx_percentile(CASE WHEN NOT no_registo THEN CAST(intervalo AS double) END, 0.5) AS mediana_intervalo_apos_s,
                            MAX(eventos_10min) FILTER (WHERE NOT no_registo)  AS max_eventos_10min_apos,
                            MIN(ts)                                           AS primeiro_ts,
                            MAX(ts)                                           AS ultimo_ts
                     FROM ritmo
                     GROUP BY userid),
     notas AS (SELECT r.userid, COUNT(*) AS avaliacoes, stddev_samp(r.rating) AS desvio_notas
               FROM ${ratings} AS r GROUP BY r.userid),
     por_nota AS (SELECT r.userid, r.rating, COUNT(*) AS n FROM ${ratings} AS r GROUP BY r.userid, r.rating),
     modal AS (SELECT userid, MAX(n) AS n_nota_modal FROM por_nota GROUP BY userid),
     base AS (SELECT e.*, n.avaliacoes, n.desvio_notas,
                     100 * CAST(m.n_nota_modal AS double) / n.avaliacoes AS pct_nota_modal
              FROM por_eventos AS e
              JOIN notas AS n ON e.userid = n.userid
              JOIN modal AS m ON e.userid = m.userid),
     limiar_a AS (SELECT approx_percentile(CAST(max_eventos_10min_apos AS double), 0.999) AS limiar_regra_a   -- QUANTIL DA REGRA A
                  FROM base WHERE eventos_apos_registo > 0),
     limiares_c AS (SELECT approx_percentile(desvio_notas, 0.01)     AS limiar_desvio_baixo,
                           approx_percentile(pct_nota_modal, 0.99)   AS limiar_modal_alto,
                           approx_percentile(pct_eventos_lote, 0.99) AS limiar_lote_alto
                    FROM base),
     f AS (SELECT b.*, a.limiar_regra_a,
                  COALESCE(b.eventos_apos_registo > 0 AND b.max_eventos_10min_apos >= a.limiar_regra_a, false) AS regra_a,
                  COALESCE(b.eventos_registo >= l.regra_b_min_eventos
                           AND b.mediana_intervalo_registo_s <= l.regra_b_max_mediana_s, false)               AS regra_b,
                  b.max_avaliacoes_mesmo_segundo >= l.lote_min_avaliacoes                                     AS submissao_lote,
                  IF(b.desvio_notas <= c.limiar_desvio_baixo, 1, 0)
                    + IF(b.pct_nota_modal >= c.limiar_modal_alto, 1, 0)
                    + IF(b.pct_eventos_lote >= c.limiar_lote_alto, 1, 0)                                     AS sinais_complementares
           FROM base AS b CROSS JOIN limiar_a AS a CROSS JOIN limiares_c AS c CROSS JOIN lim AS l)
SELECT userid, avaliacoes, eventos,
       date_format(from_unixtime(primeiro_ts), '%Y-%m-%d') AS primeiro_dia,
       date_format(from_unixtime(ultimo_ts), '%Y-%m-%d')   AS ultimo_dia,
       eventos_registo, mediana_intervalo_registo_s, max_eventos_10min_registo,
       eventos_apos_registo, mediana_intervalo_apos_s, max_eventos_10min_apos, limiar_regra_a,
       max_avaliacoes_mesmo_segundo, pct_eventos_lote, desvio_notas, pct_nota_modal,
       regra_a, regra_b, submissao_lote, sinais_complementares,
       CASE WHEN regra_a AND regra_b THEN 'suspeito (regras A e B)'
            WHEN regra_a THEN 'suspeito (regra A)'
            WHEN regra_b THEN 'suspeito (regra B)'
            WHEN submissao_lote THEN 'submissão em lote'
            ELSE 'sem sinais' END AS classificacao
FROM f
ORDER BY userid
