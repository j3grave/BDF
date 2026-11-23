-- 10_flag_bots_calibracao.sql (DuckDB) - distribuição do ritmo sustentado e n.º de sinalizados
-- com vários limiares, para justificar o limiar fixo da regra A de 10_flag_bots.sql (100)
--
-- Pergunta: como se distribui o máximo de eventos numa janela de 10 min, depois das primeiras
-- 24 h, e quantos utilizadores ficariam sinalizados com 50, 60 e 100 eventos em 10 min?
-- Inclui também os totais de cada categoria e a taxa de sinalizados.
--
-- Lê a tabela por utilizador de 10_flag_bots.sql (${flag_bots}); o 04_analise.py corre-a
-- antes. Resultado agregado: uma linha.
--
-- Parâmetros: ${flag_bots}
WITH a AS (SELECT max_eventos_10min_apos AS x
           FROM ${flag_bots} WHERE eventos_apos_registo > 0),
     s AS (SELECT COUNT(*)                AS utilizadores_com_atividade_apos_registo,
                  quantile_cont(x, 0.5)   AS p50,
                  quantile_cont(x, 0.9)   AS p90,
                  quantile_cont(x, 0.99)  AS p99,
                  quantile_cont(x, 0.999) AS p99_9,
                  MAX(x)                  AS maximo,
                  count_if(x >= 50)       AS sinalizados_50,
                  count_if(x >= 60)       AS sinalizados_60,
                  count_if(x >= 100)      AS sinalizados_100
           FROM a),
     t AS (SELECT COUNT(*)                                       AS utilizadores,
                  count_if(regra_a)                              AS suspeitos,
                  count_if(submissao_lote)                       AS submissao_lote,
                  count_if(submissao_lote AND NOT regra_a)       AS so_submissao_lote,
                  100.0 * count_if(regra_a) / COUNT(*)           AS pct_suspeitos
           FROM ${flag_bots})
SELECT s.*, t.* FROM s CROSS JOIN t;
