-- 01_ligacao.sql (Athena) - equivalente a sql/imdb/01_ligacao.sql (explicação completa lá).
--
-- Diferença para o DuckDB: percentagens com CAST(... AS double); no Trino, 100.0 * x / y com
-- inteiros ficaria em decimal com poucas casas.
--
-- Parâmetros: ${filmes}
SELECT CASE
           WHEN f.imdbid IS NULL      THEN '1. sem imdbId no links.csv'
           WHEN NOT f.existe_no_imdb  THEN '2. tconst não existe no title.basics'
           WHEN f.nota_imdb IS NULL   THEN '3. sem nota no title.ratings'
           ELSE '4. ligado e com nota'
       END                                                          AS categoria,
       COUNT(*)                                                     AS filmes,
       100 * CAST(COUNT(*) AS double) / SUM(COUNT(*)) OVER ()       AS pct_filmes,
       SUM(f.n_ml)                                                  AS avaliacoes_ml,
       100 * CAST(SUM(f.n_ml) AS double) / SUM(SUM(f.n_ml)) OVER () AS pct_avaliacoes_ml
FROM ${filmes} AS f
GROUP BY 1
ORDER BY 1
