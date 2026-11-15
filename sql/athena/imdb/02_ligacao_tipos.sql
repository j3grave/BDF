-- 02_ligacao_tipos.sql (Athena) - equivalente a sql/imdb/02_ligacao_tipos.sql.
--
-- Diferença para o DuckDB: percentagem com CAST(... AS double).
--
-- Parâmetros: ${filmes}
SELECT f.tipo_imdb,
       COUNT(*)                                                AS filmes,
       100 * CAST(COUNT(*) AS double) / SUM(COUNT(*)) OVER ()  AS pct_filmes,
       count_if(f.nota_imdb IS NOT NULL)                       AS com_nota_imdb,
       SUM(f.n_ml)                                             AS avaliacoes_ml
FROM ${filmes} AS f
WHERE f.existe_no_imdb
GROUP BY f.tipo_imdb
ORDER BY filmes DESC, f.tipo_imdb
