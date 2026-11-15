-- 03_concordancia.sql (DuckDB) - P1: as notas do MovieLens e do IMDb concordam?
--
-- Uma linha com:
-- - gap médio IMDb - MovieLens (escala de 1 a 10) e o intervalo de confiança a 95%:
--   média ± 1,96 × desvio-padrão / raiz(n) (aproximação normal; com centenas de filmes é adequada);
-- - gap absoluto médio (quanto se afastam, seja para que lado for);
-- - correlação de Pearson (relação linear entre as notas) e de Spearman (só a ordem dos filmes).
--
-- Spearman = Pearson calculado sobre as posições (ranks) em vez das notas. Em caso de empate
-- (muito comum: o IMDb só tem uma casa decimal) cada filme fica com a posição média do grupo
-- empatado: rank() + (n.º de empatados - 1) / 2.
--
-- Limiares (config.yaml, secção imdb): só filmes com pelo menos ${min_ml} avaliações no
-- MovieLens e ${min_imdb} votos no IMDb. Com poucas avaliações a média é muito instável.
-- O 07_imdb.py corre esta query também com outros limiares (análise de sensibilidade).
--
-- Parâmetros: ${filmes}, ${min_ml}, ${min_imdb}
WITH f AS (
    SELECT nota_ml_10, nota_imdb, gap
    FROM ${filmes}
    WHERE nota_imdb IS NOT NULL AND n_ml >= ${min_ml} AND votos_imdb >= ${min_imdb}
),
r AS (
    SELECT nota_ml_10, nota_imdb, gap,
           rank() OVER (ORDER BY nota_ml_10) + (COUNT(*) OVER (PARTITION BY nota_ml_10) - 1) / 2.0 AS rank_ml,
           rank() OVER (ORDER BY nota_imdb)  + (COUNT(*) OVER (PARTITION BY nota_imdb) - 1) / 2.0  AS rank_imdb
    FROM f
)
SELECT COUNT(*)                                              AS filmes,
       AVG(nota_ml_10)                                       AS media_ml_10,
       AVG(nota_imdb)                                        AS media_imdb,
       AVG(gap)                                              AS gap_medio,
       STDDEV_SAMP(gap)                                      AS gap_desvio_padrao,
       AVG(gap) - 1.96 * STDDEV_SAMP(gap) / SQRT(COUNT(*))   AS gap_ic95_inf,
       AVG(gap) + 1.96 * STDDEV_SAMP(gap) / SQRT(COUNT(*))   AS gap_ic95_sup,
       AVG(ABS(gap))                                         AS gap_abs_medio,
       100.0 * count_if(gap > 0) / COUNT(*)                  AS pct_imdb_acima,
       CORR(nota_ml_10, nota_imdb)                           AS pearson,
       CORR(rank_ml, rank_imdb)                              AS spearman
FROM r;
