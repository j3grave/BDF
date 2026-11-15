-- 08_imdb_title_ratings.sql
-- IMDb title.ratings em Parquet (zstd): nota média e n.º de votos de cada título.
-- Fica em s3://<bucket>/imdb/, a mesma pasta para os três datasets do MovieLens.
-- Só é criada se existir data/cloud/imdb/ (passo imdb e prepare_cloud_imdb.py).
--
-- Parâmetros: ${bucket}
CREATE EXTERNAL TABLE IF NOT EXISTS imdb_title_ratings (
    tconst          string,
    averagerating   double,
    numvotes        int
)
STORED AS PARQUET
LOCATION 's3://${bucket}/imdb/title_ratings/'
