-- 11_imdb_title_basics_tsv.sql
-- Cópia do title.basics.tsv.gz original, para comparar os bytes lidos em TSV e em Parquet.
-- No TSV, isadult é 0/1 (int) e genres é texto ("Drama,Romance"); as queries fazem split(genres, ',').
-- Mesmas notas do 10_imdb_title_ratings_tsv.sql.
--
-- Parâmetros: ${bucket}
CREATE EXTERNAL TABLE IF NOT EXISTS imdb_title_basics_tsv (
    tconst          string,
    titletype       string,
    primarytitle    string,
    originaltitle   string,
    isadult         int,
    startyear       int,
    endyear         int,
    runtimeminutes  int,
    genres          string
)
ROW FORMAT DELIMITED
    FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION 's3://${bucket}/imdb/title_basics_tsv/'
TBLPROPERTIES ('skip.header.line.count' = '1', 'serialization.null.format' = '\\N')
