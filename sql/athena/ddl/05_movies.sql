-- 05_movies.sql
-- movies em Parquet (zstd). genres guarda vários géneros num só texto ("Action|Comedy").
--
-- Parâmetros: ${bucket}, ${pasta}
CREATE EXTERNAL TABLE IF NOT EXISTS movies (
    movieid     int,
    title       string,
    genres      string
)
STORED AS PARQUET
LOCATION 's3://${bucket}/${pasta}/movies/'
