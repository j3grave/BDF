-- eventos.sql (Athena) - equivalente a sql/analise/eventos.sql
-- Origem: notebook do Luís, célula 112 ("novo-advanced"): dias_filme, view "eventos" e participantes.
--
-- A tabela filme x dia (14,7 M linhas no 32M) só existe como CTE. Se for precisa para outras
-- análises, cria-se com CTAS em Parquet; nunca é devolvida ao cliente.
-- ${flag_bots} é a tabela flag_bots criada por CTAS a partir de 10_flag_bots.sql.
-- LIMIT (posicao <= 100) justificado: os 100 eventos com mais suspeitos, para inspeção; o total
-- vem na coluna total_eventos e no funil (filtros_eventos.sql).
-- Dia: "timestamp" / 86400 (divisão inteira no Trino = dia UTC); a data sai com
-- CAST(from_unixtime(dia * 86400) AS date), em UTC.
-- Frações com CAST(... AS double) (no Trino, x * 1.0 / y teria só 1 casa decimal).
-- Limites do capítulo 9 (P7), a decidir com o Luís.
--
-- Parâmetros: ${ratings}, ${movies}, ${flag_bots}
WITH lim AS (SELECT 5 AS min_anterior, 5 AS min_utilizadores, 2.0 AS nota_baixa, 4.0 AS nota_alta,
                    0.51 AS min_frac_extremas, 0.5 AS min_variacao),
     d AS (SELECT r.movieid, r."timestamp" / 86400 AS dia, COUNT(*) AS n,
                  COUNT(DISTINCT r.userid) AS utilizadores, SUM(r.rating) AS soma, AVG(r.rating) AS media,
                  CAST(count_if(r.rating <= l.nota_baixa) AS double) / COUNT(*) AS frac_baixas,
                  CAST(count_if(r.rating >= l.nota_alta)  AS double) / COUNT(*) AS frac_altas
           FROM ${ratings} AS r CROSS JOIN lim AS l
           GROUP BY r.movieid, r."timestamp" / 86400),
     h AS (SELECT d.*,
                  SUM(n)    OVER (PARTITION BY movieid ORDER BY dia ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - n    AS n_anterior,
                  SUM(soma) OVER (PARTITION BY movieid ORDER BY dia ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - soma AS soma_anterior
           FROM d),
     v AS (SELECT h.*, soma_anterior / NULLIF(n_anterior, 0) AS media_anterior,
                  media - soma_anterior / NULLIF(n_anterior, 0) AS variacao
           FROM h),
     ev AS (SELECT v.movieid, v.dia, v.utilizadores, v.n_anterior, v.media_anterior, v.media, v.variacao,
                   CASE WHEN v.frac_baixas >= l.min_frac_extremas AND v.variacao <= -l.min_variacao THEN 'Avaliações baixas'
                        WHEN v.frac_altas  >= l.min_frac_extremas AND v.variacao >=  l.min_variacao THEN 'Avaliações altas'
                   END AS tipo
            FROM v CROSS JOIN lim AS l
            WHERE v.n_anterior >= l.min_anterior AND v.utilizadores >= l.min_utilizadores),
     e AS (SELECT * FROM ev WHERE tipo IS NOT NULL),
     p AS (SELECT r.movieid, r."timestamp" / 86400 AS dia,
                  COUNT(DISTINCT r.userid)                                           AS participantes,
                  COUNT(DISTINCT CASE WHEN f.regra_a OR f.regra_b THEN r.userid END) AS suspeitos,
                  COUNT(DISTINCT CASE WHEN f.submissao_lote THEN r.userid END)       AS em_lote
           FROM ${ratings} AS r
           JOIN e ON r.movieid = e.movieid AND r."timestamp" / 86400 = e.dia
           LEFT JOIN ${flag_bots} AS f ON r.userid = f.userid
           GROUP BY r.movieid, r."timestamp" / 86400),
     x AS (SELECT e.*, p.participantes, p.suspeitos, p.em_lote,
                  100 * CAST(p.suspeitos AS double) / p.participantes AS pct_suspeitos,
                  ROW_NUMBER() OVER (ORDER BY p.suspeitos DESC, e.utilizadores DESC, e.movieid, e.dia) AS posicao,
                  COUNT(*) OVER () AS total_eventos
           FROM e JOIN p ON e.movieid = p.movieid AND e.dia = p.dia)
SELECT x.posicao, x.movieid, m.title, CAST(from_unixtime(x.dia * 86400) AS date) AS dia, x.tipo,
       x.utilizadores, x.n_anterior, x.media_anterior, x.media, x.variacao,
       x.suspeitos, x.em_lote, x.pct_suspeitos, x.total_eventos
FROM x JOIN ${movies} AS m ON x.movieid = m.movieid
WHERE x.posicao <= 100
ORDER BY x.posicao
