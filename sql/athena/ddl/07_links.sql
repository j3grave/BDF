-- 07_links.sql
-- links em Parquet (zstd). imdbid é texto (mantém os zeros à esquerda, ex.: 0114709).
-- Não existe no dataset 1M (o athena_setup.py salta-a).
--
-- Parâmetros: ${bucket}, ${pasta}
CREATE EXTERNAL TABLE IF NOT EXISTS links (
    movieid     int,
    imdbid      string,
    tmdbid      int
)
STORED AS PARQUET
LOCATION 's3://${bucket}/${pasta}/links/'
