-- 04_ratings_csv.sql
-- Cópia do ratings.csv original, para comparar os bytes lidos pelo Athena em CSV e em Parquet.
--
-- Notas:
-- - LazySimpleSerDe (ROW FORMAT DELIMITED): serve porque o ratings.csv só tem números,
--   sem aspas nem vírgulas dentro dos campos.
-- - skip.header.line.count salta a linha de cabeçalho (userId,movieId,rating,timestamp).
--
-- Parâmetros: ${bucket}, ${pasta}
CREATE EXTERNAL TABLE IF NOT EXISTS ratings_csv (
    userid      int,
    movieid     int,
    rating      double,
    `timestamp` bigint
)
ROW FORMAT DELIMITED
    FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://${bucket}/${pasta}/ratings_csv/'
TBLPROPERTIES ('skip.header.line.count' = '1')
