-- filtros_eventos.sql (Athena) - equivalente a sql/analise/filtros_eventos.sql
-- Origem: notebook do Luís, célula 112 ("novo-advanced"): dias_filme, view "eventos" e "filtros".
--
-- A tabela filme x dia (14,7 M linhas no 32M) só existe como CTE: o resultado devolvido é
-- uma linha. Se for precisa para outras análises, cria-se com CTAS em Parquet
-- (CREATE TABLE dias_filme WITH (format = 'PARQUET') AS SELECT ... das CTEs d/h/v),
-- nunca como resultado devolvido ao cliente.
-- Dia: "timestamp" / 86400 (no Trino, bigint / bigint é divisão inteira = dia UTC); não há
-- conversão de fuso.
-- Limites do capítulo 9 do notebook (P7), na CTE lim, a decidir com o Luís.
-- Frações com CAST(... AS double): no Trino, count_if(...) * 1.0 / COUNT(*) ficaria com a
-- escala do literal 1.0 (1 casa decimal) e 0.51 seria comparado com 0.5.
--
-- Parâmetros: ${ratings}
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
     v AS (SELECT h.*, media - soma_anterior / NULLIF(n_anterior, 0) AS variacao FROM h)
SELECT COUNT(*) AS todos_filme_dia,
       count_if(n_anterior >= l.min_anterior) AS com_historico,
       count_if(n_anterior >= l.min_anterior AND utilizadores >= l.min_utilizadores) AS com_utilizadores,
       count_if(n_anterior >= l.min_anterior AND utilizadores >= l.min_utilizadores
                AND (frac_baixas >= l.min_frac_extremas OR frac_altas >= l.min_frac_extremas)) AS com_extremos,
       count_if(n_anterior >= l.min_anterior AND utilizadores >= l.min_utilizadores
                AND ((frac_baixas >= l.min_frac_extremas AND variacao <= -l.min_variacao)
                  OR (frac_altas  >= l.min_frac_extremas AND variacao >=  l.min_variacao))) AS eventos,
       l.min_anterior, l.min_utilizadores, l.nota_baixa, l.nota_alta, l.min_frac_extremas, l.min_variacao
FROM v CROSS JOIN lim AS l
GROUP BY l.min_anterior, l.min_utilizadores, l.nota_baixa, l.nota_alta, l.min_frac_extremas, l.min_variacao
