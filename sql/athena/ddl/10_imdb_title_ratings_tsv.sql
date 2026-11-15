-- 10_imdb_title_ratings_tsv.sql
-- Cópia do title.ratings.tsv.gz original, para comparar os bytes lidos em TSV e em Parquet.
--
-- Notas:
-- - O Athena lê ficheiros .gz diretamente (descomprime pela extensão).
-- - FIELDS TERMINATED BY '\t': separador tabulação. O IMDb não usa aspas.
-- - serialization.null.format: o IMDb escreve \N quando não há valor; passa a nulo.
-- - skip.header.line.count salta a linha de cabeçalho.
--
-- Parâmetros: ${bucket}
CREATE EXTERNAL TABLE IF NOT EXISTS imdb_title_ratings_tsv (
    tconst          string,
    averagerating   double,
    numvotes        int
)
ROW FORMAT DELIMITED
    FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION 's3://${bucket}/imdb/title_ratings_tsv/'
TBLPROPERTIES ('skip.header.line.count' = '1', 'serialization.null.format' = '\\N')
