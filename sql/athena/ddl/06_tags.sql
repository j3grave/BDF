-- 06_tags.sql
-- tags em Parquet (zstd). Não existe no dataset 1M (o athena_setup.py salta-a).
--
-- Parâmetros: ${bucket}, ${pasta}
CREATE EXTERNAL TABLE IF NOT EXISTS tags (
    userid      int,
    movieid     int,
    tag         string,
    `timestamp` bigint
)
STORED AS PARQUET
LOCATION 's3://${bucket}/${pasta}/tags/'
