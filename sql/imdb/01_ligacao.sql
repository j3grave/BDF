-- 01_ligacao.sql (DuckDB) - quantos filmes do MovieLens ligam ao IMDb, e porque é que os
-- restantes não ligam.
--
-- Como funciona: cada filme avaliado no MovieLens cai numa só categoria, pela ordem:
--   1. sem imdbId no links.csv;
--   2. com imdbId, mas o tconst não existe no title.basics (id removido ou fundido noutro
--      no IMDb; o ficheiro público não diz qual);
--   3. existe no title.basics, mas não tem nota no title.ratings (filme sem votos);
--   4. ligado, com nota e de um tipo incluído (entra nas análises);
--   5. ligado e com nota, mas de um tipo de título excluído (${tipos} no config.yaml:
--      por omissão só 'movie'; ficam de fora séries, episódios, curtas e vídeos).
-- O 02_ligacao_tipos.sql mostra a distribuição por tipo de título.
--
-- Parâmetros: ${filmes}, ${tipos}
SELECT CASE
           WHEN imdbId IS NULL      THEN '1. sem imdbId no links.csv'
           WHEN NOT existe_no_imdb  THEN '2. tconst não existe no title.basics'
           WHEN nota_imdb IS NULL   THEN '3. sem nota no title.ratings'
           WHEN tipo_imdb NOT IN ${tipos} THEN '5. com nota mas tipo de título excluído'
           ELSE '4. ligado e com nota (entra nas análises)'
       END                                       AS categoria,
       COUNT(*)                                  AS filmes,
       100.0 * COUNT(*) / SUM(COUNT(*)) OVER ()  AS pct_filmes,
       SUM(n_ml)                                 AS avaliacoes_ml,
       100.0 * SUM(n_ml) / SUM(SUM(n_ml)) OVER () AS pct_avaliacoes_ml
FROM ${filmes}
GROUP BY 1
ORDER BY 1;
