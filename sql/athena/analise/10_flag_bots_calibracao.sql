-- 10_flag_bots_calibracao.sql (Athena) - equivalente a sql/analise/10_flag_bots_calibracao.sql
--
-- *** A VALIDAR COM O LUÍS ***
-- Lê a tabela flag_bots criada por CTAS a partir de sql/athena/analise/10_flag_bots.sql
-- (${flag_bots} = flag_bots). Resultado agregado: uma linha.
-- Quantis com approx_percentile (aproximados; no DuckDB são exatos, quantile_cont).
-- Frações com CAST(... AS double). Não converte o timestamp (sem questões de fuso).
--
-- Parâmetros: ${flag_bots}
WITH a AS (SELECT CAST(max_eventos_10min_apos AS double) AS x
           FROM ${flag_bots} WHERE eventos_apos_registo > 0),
     q AS (SELECT COUNT(*)                     AS utilizadores_com_atividade_apos_registo,
                  approx_percentile(x, 0.5)    AS p50,
                  approx_percentile(x, 0.9)    AS p90,
                  approx_percentile(x, 0.95)   AS p95,
                  approx_percentile(x, 0.99)   AS p99,
                  approx_percentile(x, 0.995)  AS p99_5,
                  approx_percentile(x, 0.999)  AS p99_9,
                  MAX(x)                       AS maximo
           FROM a),
     s AS (SELECT q.utilizadores_com_atividade_apos_registo, q.p50, q.p90, q.p95, q.p99, q.p99_5, q.p99_9, q.maximo,
                  count_if(a.x >= q.p99)   AS sinalizados_a_p99,
                  count_if(a.x >= q.p99_5) AS sinalizados_a_p99_5,
                  count_if(a.x >= q.p99_9) AS sinalizados_a_p99_9
           FROM a CROSS JOIN q
           GROUP BY q.utilizadores_com_atividade_apos_registo, q.p50, q.p90, q.p95, q.p99, q.p99_5, q.p99_9, q.maximo),
     t AS (SELECT COUNT(*)                                     AS utilizadores,
                  count_if(regra_a)                            AS regra_a,
                  count_if(regra_b)                            AS regra_b,
                  count_if(regra_a OR regra_b)                 AS suspeitos,
                  count_if(submissao_lote)                     AS submissao_lote,
                  count_if(submissao_lote AND NOT (regra_a OR regra_b)) AS so_submissao_lote,
                  100 * CAST(count_if(regra_a OR regra_b) AS double) / COUNT(*) AS pct_suspeitos
           FROM ${flag_bots})
SELECT s.*, t.* FROM s CROSS JOIN t
