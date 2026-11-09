-- eventos.sql (DuckDB) - dias em que um filme recebeu uma concentração de notas extremas que
-- mudou a sua média, cruzados com os utilizadores suspeitos
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 112 (id "novo-advanced"): SQL_AVANCADO["dias_filme"], a view "eventos" e a
--         consulta dos participantes (gravada em eventos_filme.parquet). Autor: Luís Pousada (e51d050).
--
-- Pergunta: em que (filme, dia) houve muitas notas extremas no mesmo sentido, com a média do dia
-- afastada do histórico anterior do filme? Quantos dos utilizadores desse dia são suspeitos?
--
-- Alterações face ao original:
-- - dias_filme e a view eventos só existem como CTEs (d, h, v, ev): a tabela filme x dia
--   (14,7 M linhas no 32M) nunca é devolvida (relatório, P6);
-- - o cruzamento passa a usar a nova deteção (10_flag_bots.sql, tabela ${flag_bots}):
--   suspeitos = regra A ou regra B; em_lote = submissão em lote (conta-se à parte, não é bot).
--   O original usava num_sinais > 0 da regra antiga, que sinalizava 34% dos utilizadores;
-- - LIMIT 100 (justificado): devolve os 100 eventos com mais suspeitos, para inspeção manual.
--   O total de eventos está na coluna total_eventos e no funil (filtros_eventos.sql); no 32M,
--   com estes limites, o notebook registou 90 108 eventos;
-- - limites na CTE lim, os do capítulo 9 (P7), iguais aos de filtros_eventos.sql, a decidir
--   com o Luís; COUNT(DISTINCT CASE ...) em vez de FILTER, como na versão Athena;
-- - dia como data (UTC): timestamp // 86400 é o n.º do dia desde 1970-01-01 em UTC.
--
-- Parâmetros: ${ratings}, ${movies}, ${flag_bots}
WITH lim AS (SELECT 5 AS min_anterior, 5 AS min_utilizadores, 2.0 AS nota_baixa, 4.0 AS nota_alta,
                    0.51 AS min_frac_extremas, 0.5 AS min_variacao),
     d AS (SELECT r.movieId, r.timestamp // 86400 AS dia, COUNT(*) AS n,
                  COUNT(DISTINCT r.userId) AS utilizadores, SUM(r.rating) AS soma, AVG(r.rating) AS media,
                  count_if(r.rating <= l.nota_baixa) * 1.0 / COUNT(*) AS frac_baixas,
                  count_if(r.rating >= l.nota_alta)  * 1.0 / COUNT(*) AS frac_altas
           FROM ${ratings} r CROSS JOIN lim l
           GROUP BY r.movieId, r.timestamp // 86400),
     h AS (SELECT d.*,
                  SUM(n)    OVER (PARTITION BY movieId ORDER BY dia ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - n    AS n_anterior,
                  SUM(soma) OVER (PARTITION BY movieId ORDER BY dia ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - soma AS soma_anterior
           FROM d),
     v AS (SELECT h.*, soma_anterior / NULLIF(n_anterior, 0) AS media_anterior,
                  media - soma_anterior / NULLIF(n_anterior, 0) AS variacao
           FROM h),
     ev AS (SELECT v.movieId, v.dia, v.utilizadores, v.n_anterior, v.media_anterior, v.media, v.variacao,
                   CASE WHEN v.frac_baixas >= l.min_frac_extremas AND v.variacao <= -l.min_variacao THEN 'Avaliações baixas'
                        WHEN v.frac_altas  >= l.min_frac_extremas AND v.variacao >=  l.min_variacao THEN 'Avaliações altas'
                   END AS tipo
            FROM v CROSS JOIN lim l
            WHERE v.n_anterior >= l.min_anterior AND v.utilizadores >= l.min_utilizadores),
     e AS (SELECT * FROM ev WHERE tipo IS NOT NULL),
     p AS (SELECT r.movieId, r.timestamp // 86400 AS dia,
                  COUNT(DISTINCT r.userId)                                                  AS participantes,
                  COUNT(DISTINCT CASE WHEN f.regra_a OR f.regra_b THEN r.userId END)        AS suspeitos,
                  COUNT(DISTINCT CASE WHEN f.submissao_lote THEN r.userId END)              AS em_lote
           FROM ${ratings} r
           JOIN e ON r.movieId = e.movieId AND r.timestamp // 86400 = e.dia
           LEFT JOIN ${flag_bots} f ON r.userId = f.userId
           GROUP BY r.movieId, r.timestamp // 86400),
     x AS (SELECT e.*, p.participantes, p.suspeitos, p.em_lote,
                  100.0 * p.suspeitos / p.participantes AS pct_suspeitos,
                  ROW_NUMBER() OVER (ORDER BY p.suspeitos DESC, e.utilizadores DESC, e.movieId, e.dia) AS posicao,
                  COUNT(*) OVER () AS total_eventos
           FROM e JOIN p ON e.movieId = p.movieId AND e.dia = p.dia)
SELECT x.posicao, x.movieId, m.title, CAST(epoch_ms(x.dia * 86400 * 1000) AS DATE) AS dia, x.tipo,
       x.utilizadores, x.n_anterior, x.media_anterior, x.media, x.variacao,
       x.suspeitos, x.em_lote, x.pct_suspeitos, x.total_eventos
FROM x JOIN ${movies} m ON x.movieId = m.movieId
WHERE x.posicao <= 100
ORDER BY x.posicao;
