-- 00_filmes.sql (DuckDB) - tabela base: um filme do MovieLens por linha, ligado ao IMDb.
--
-- Pergunta: para cada filme avaliado no MovieLens, qual é a nota média no MovieLens e
-- qual é a nota no IMDb?
--
-- Como funciona:
-- 1. ml: n.º de avaliações e nota média de cada filme no MovieLens.
-- 2. lk: o imdbId do links.csv passa a tconst, o identificador do IMDb ("tt" + 7 algarismos).
--    O links.csv guarda o número sem o "tt" e, no 32M, alguns ids têm 8 algarismos.
--    ATENÇÃO: lpad(x, 7, '0') também CORTA os textos com mais de 7 caracteres
--    (lpad('12345678', 7, '0') = '1234567'). Por isso o lpad só se aplica aos ids
--    com menos de 7 algarismos; os de 7 e 8 ficam como estão.
-- 3. LEFT JOIN com o title.basics e o title.ratings do IMDb: os filmes que não ligam ficam
--    na tabela (com as colunas do IMDb vazias), para o 01_ligacao.sql contar porquê.
--
-- Escalas: o MovieLens vai de 0,5 a 5 e o IMDb de 1 a 10. nota_ml_10 = nota_ml * 2 põe o
-- MovieLens de 1 a 10 (0,5 -> 1 e 5 -> 10), os mesmos extremos do IMDb. É uma conversão linear,
-- por isso não muda a ordem dos filmes nem as correlações. O gap é IMDb - MovieLens (em pontos
-- da escala de 1 a 10): positivo quando o IMDb dá nota mais alta.
--
-- O resultado é guardado numa tabela temporária (${filmes}) que as outras queries leem.
--
-- Parâmetros: ${ratings}, ${movies}, ${links}, ${imdb_basics}, ${imdb_ratings}
WITH ml AS (
    SELECT movieId, COUNT(*) AS n_ml, AVG(rating) AS media_ml
    FROM ${ratings}
    GROUP BY movieId
),
lk AS (
    SELECT movieId,
           imdbId,
           'tt' || CASE WHEN length(imdbId) < 7 THEN lpad(imdbId, 7, '0') ELSE imdbId END AS tconst
    FROM ${links}
    WHERE imdbId IS NOT NULL
)
SELECT ml.movieId,
       m.title,
       string_split(m.genres, '|')          AS generos_ml,
       ml.n_ml,
       ml.media_ml,
       ml.media_ml * 2                      AS nota_ml_10,
       lk.imdbId,
       lk.tconst,
       b.tconst IS NOT NULL                 AS existe_no_imdb,
       b.titleType                          AS tipo_imdb,
       b.startYear                          AS ano_estreia,
       b.genres                             AS generos_imdb,
       i.averageRating                      AS nota_imdb,
       i.numVotes                           AS votos_imdb,
       i.averageRating - ml.media_ml * 2    AS gap
FROM ml
JOIN ${movies} m ON m.movieId = ml.movieId
LEFT JOIN lk ON lk.movieId = ml.movieId
LEFT JOIN ${imdb_basics} b ON b.tconst = lk.tconst
LEFT JOIN ${imdb_ratings} i ON i.tconst = lk.tconst;
