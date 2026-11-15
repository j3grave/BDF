-- filtros_eventos.sql (DuckDB) - funil dos filtros dos "eventos" (concentrações de notas
-- extremas num filme, num dia)
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 112 (id "novo-advanced"): SQL_AVANCADO["dias_filme"] (tabela filme x dia),
--         a view "eventos" e a consulta "filtros". Autor: Luís Pousada (e51d050).
--
-- Pergunta: quantos pares (filme, dia) passam cada filtro, por ordem: histórico anterior ->
-- n.º de utilizadores no dia -> proporção de notas extremas -> variação da média face ao
-- histórico no mesmo sentido?
--
-- Alterações face ao original:
-- - dias_filme (uma linha por filme x dia: 99 538 no small, 14,7 M no 32M) deixa de ser um
--   resultado: só existe como CTE (d, h, v) e a query devolve uma linha (relatório, P6);
-- - os limites estão numa CTE (lim) e são devolvidos com o resultado. São os do capítulo 9
--   do notebook (os das queries SQL), não os do capítulo 8 (P7): escolher um só conjunto é
--   uma decisão a tomar com o Luís;
-- - count_if em vez de COUNT(*) FILTER e AVG((cond)::INTEGER); janela por extenso.
-- O dia é timestamp // 86400 (dia UTC, sem conversão de fuso).
--
-- Parâmetros: ${ratings}
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
FROM v CROSS JOIN lim l
GROUP BY l.min_anterior, l.min_utilizadores, l.nota_baixa, l.nota_alta, l.min_frac_extremas, l.min_variacao;
