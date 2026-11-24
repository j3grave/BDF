-- 01_ratings.sql
-- ratings em Parquet (zstd), sem partição: um único ficheiro em ratings/.
--
-- Notas:
-- - EXTERNAL: a tabela só aponta para os ficheiros no S3. Apagar a tabela (DROP TABLE)
--   não apaga os dados.
-- - O catálogo guarda os nomes em minúsculas (userId -> userid). Na leitura de Parquet
--   a correspondência de nomes não distingue maiúsculas, por isso os ficheiros servem tal como estão.
-- - timestamp é palavra reservada: no DDL vai entre backticks, nas queries entre aspas duplas.
-- - Tipos iguais aos dos ficheiros (ver reports/cloud_manifest_<dataset>.md).
--
-- Parâmetros: ${bucket}, ${pasta}
CREATE EXTERNAL TABLE IF NOT EXISTS ratings (
    userid      int,
    movieid     int,
    rating      double,
    `timestamp` bigint
)
STORED AS PARQUET
LOCATION 's3://${bucket}/${pasta}/ratings/'
