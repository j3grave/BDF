-- 10_flag_bots_calibracao.sql (DuckDB) - distribuição do ritmo sustentado e n.º de sinalizados
-- por limiar, para calibrar a regra A de 10_flag_bots.sql
--
-- *** A VALIDAR COM O LUÍS *** (faz parte da deteção que substitui a regra do notebook)
--
-- Pergunta: como se distribui o máximo de eventos numa janela de 10 min, depois das primeiras
-- 24 h, e quantos utilizadores ficariam sinalizados com o limiar no p99, no p99,5 e no p99,9?
-- Inclui também os totais de cada regra e categoria, e a taxa de sinalizados.
--
-- Lê a tabela por utilizador de 10_flag_bots.sql (${flag_bots}); o 05_analises.py corre-a
-- antes. Resultado agregado: uma linha.
--
-- Parâmetros: ${flag_bots}
WITH a AS (SELECT max_eventos_10min_apos AS x, mediana_intervalo_apos_s AS mediana
           FROM ${flag_bots} WHERE eventos_apos_registo > 0),
     q AS (SELECT COUNT(*)               AS utilizadores_com_atividade_apos_registo,
                  quantile_cont(x, 0.5)   AS p50,
                  quantile_cont(x, 0.9)   AS p90,
                  quantile_cont(x, 0.95)  AS p95,
                  quantile_cont(x, 0.99)  AS p99,
                  quantile_cont(x, 0.995) AS p99_5,
                  quantile_cont(x, 0.999) AS p99_9,
                  MAX(x)                  AS maximo
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
                  100.0 * count_if(regra_a OR regra_b) / COUNT(*) AS pct_suspeitos
           FROM ${flag_bots})
SELECT s.*, t.* FROM s CROSS JOIN t;
