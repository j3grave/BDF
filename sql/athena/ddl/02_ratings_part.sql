-- 02_ratings_part.sql
-- ratings em Parquet (zstd), particionado por ano: ratings_part/year=AAAA/*.parquet.
--
-- Notas:
-- - year não está dentro dos ficheiros: vem do nome da pasta, por isso aparece só em
--   PARTITIONED BY e não na lista de colunas.
-- - Depois de criar a tabela, o catálogo ainda não conhece as pastas year=AAAA.
--   O ficheiro seguinte (03_ratings_part_particoes.sql) carrega-as.
--
-- Parâmetros: ${bucket}, ${pasta}
CREATE EXTERNAL TABLE IF NOT EXISTS ratings_part (
    userid      int,
    movieid     int,
    rating      double,
    `timestamp` bigint
)
PARTITIONED BY (year int)
STORED AS PARQUET
LOCATION 's3://${bucket}/${pasta}/ratings_part/'
