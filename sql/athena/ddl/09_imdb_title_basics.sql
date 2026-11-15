-- 09_imdb_title_basics.sql
-- IMDb title.basics em Parquet (zstd): tipo, títulos, anos, duração e géneros de cada título.
-- isadult é booleano e genres é uma lista (array<string>), tal como o 07_imdb.py os escreve.
--
-- Parâmetros: ${bucket}
CREATE EXTERNAL TABLE IF NOT EXISTS imdb_title_basics (
    tconst          string,
    titletype       string,
    primarytitle    string,
    originaltitle   string,
    isadult         boolean,
    startyear       int,
    endyear         int,
    runtimeminutes  int,
    genres          array<string>
)
STORED AS PARQUET
LOCATION 's3://${bucket}/imdb/title_basics/'
