-- 02_ligacao_tipos.sql (DuckDB) - tipo de título no IMDb (titleType) dos filmes que ligam.
--
-- Serve para decidir se vale a pena filtrar por tipo: o MovieLens também tem séries
-- (tvSeries, tvMiniSeries), filmes para TV (tvMovie), curtas (short) e vídeos (video).
-- As análises NÃO filtram por tipo; esta tabela só mostra quantos há de cada.
--
-- Parâmetros: ${filmes}
SELECT tipo_imdb,
       COUNT(*)                                  AS filmes,
       100.0 * COUNT(*) / SUM(COUNT(*)) OVER ()  AS pct_filmes,
       count_if(nota_imdb IS NOT NULL)           AS com_nota_imdb,
       SUM(n_ml)                                 AS avaliacoes_ml
FROM ${filmes}
WHERE existe_no_imdb
GROUP BY tipo_imdb
ORDER BY filmes DESC, tipo_imdb;
