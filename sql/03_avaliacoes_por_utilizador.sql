-- 03_avaliacoes_por_utilizador.sql
-- Pergunta 7.3: qual é a distribuição das avaliações por utilizador?
--
-- Como funciona: agrupa os ratings por utilizador e calcula, para cada um, o n.º de
-- avaliações, a média, o desvio-padrão (amostral), o mínimo, a mediana e o máximo.
--
-- Ligação às aulas:
-- - Formato colunar: das 4 colunas de ratings só são lidas userId e rating
--   (projection pushdown); movieId e timestamp nem saem do disco.
-- - Partições: não ajudam. A query usa todos os anos, por isso o DuckDB tem de abrir
--   todas as pastas year=AAAA; com muitos ficheiros pequenos pode até ser mais lenta
--   do que com um ficheiro único. Compare as duas linhas em results/benchmarks.csv.
--
-- Parâmetros: ${ratings}
SELECT userId,
       COUNT(*)                         AS num_ratings,
       ROUND(AVG(rating), 3)            AS mean,
       ROUND(STDDEV_SAMP(rating), 3)    AS std,
       MIN(rating)                      AS min,
       MEDIAN(rating)                   AS median,
       MAX(rating)                      AS max
FROM ${ratings}
GROUP BY userId
ORDER BY userId;
