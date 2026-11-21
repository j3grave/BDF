# Manifesto para a cloud: ml-latest-small

- Dataset: `small`
- Gerado em: 2026-11-21T16:58:12 (DuckDB 1.5.6, 0.1 s)
- Pasta local: `data/cloud/ml-latest-small/` (origem: `data/small/parquet/` e `data/small/csv/ratings.csv`)
- Upload: `python run_pipeline.py --dataset small --steps cloud` (envia para `s3://<bucket-dados>/ml-latest-small/`)
- Verificações: contagens iguais à origem, soma das partições igual a `ratings`, contagens por ano iguais ao `ratings_by_year` da fase 1, tipos iguais à origem, `year` só no nome das pastas, compressão zstd e só ficheiros da tabela em cada pasta. Todas passaram.

> **Nota:** o benchmark DuckDB vs Athena deve ler os ficheiros de `data/cloud/`, que são exatamente os mesmos que vão para o S3 (zstd), e não os Parquet da fase 1 (snappy). Assim os dois motores leem os mesmos bytes.

## Tabelas

| Tabela | Caminho | Ficheiros | Tamanho (MB) | Linhas | Compressão |
|---|---|---:|---:|---:|---|
| ratings | `ratings/` | 1 | 0.50 | 100 836 | ZSTD |
| ratings_part | `ratings_part/year=AAAA/` | 23 | 0.50 | 100 836 | ZSTD |
| ratings_csv | `ratings_csv/` | 1 | 2.48 | 100 836 | nenhuma (CSV) |
| movies | `movies/` | 1 | 0.16 | 9 742 | ZSTD |

## Compressão: fase 1 vs cloud

| Tabela | Origem (fase 1) | Compressão origem | MB origem | MB cloud (zstd) | Variação |
|---|---|---|---:|---:|---:|
| ratings | `data/small/parquet/ratings.parquet` | SNAPPY | 0.69 | 0.50 | -26.9 % |
| ratings_part | `data/small/parquet/ratings_by_year/` | SNAPPY | 0.77 | 0.50 | -35.1 % |
| movies | `data/small/parquet/movies.parquet` | SNAPPY | 0.25 | 0.16 | -33.4 % |

O `ratings_csv` é uma cópia byte a byte do CSV, sem compressão.

## Schemas

### ratings

| Coluna | Tipo (DuckDB) |
|---|---|
| userId | INTEGER |
| movieId | INTEGER |
| rating | DOUBLE |
| timestamp | BIGINT |

### ratings_part

| Coluna | Tipo (DuckDB) |
|---|---|
| userId | INTEGER |
| movieId | INTEGER |
| rating | DOUBLE |
| timestamp | BIGINT |
| year *(partição: só no nome da pasta)* | BIGINT |

### ratings_csv

| Coluna | Tipo (DuckDB) |
|---|---|
| userId | INTEGER |
| movieId | INTEGER |
| rating | DOUBLE |
| timestamp | BIGINT |

Tipos fixados pelo `SCHEMAS` do `common.py` ao ler o CSV (com cabeçalho, separador `,`).

### movies

| Coluna | Tipo (DuckDB) |
|---|---|
| movieId | INTEGER |
| title | VARCHAR |
| genres | VARCHAR |

## ratings_part: partições

| Ano | Linhas | Tamanho (MB) | Ficheiros |
|---|---:|---:|---:|
| 1996 | 6 040 | 0.02 | 1 |
| 1997 | 1 916 | 0.01 | 1 |
| 1998 | 507 | 0.00 | 1 |
| 1999 | 2 439 | 0.01 | 1 |
| 2000 | 10 061 | 0.04 | 1 |
| 2001 | 3 922 | 0.02 | 1 |
| 2002 | 3 478 | 0.02 | 1 |
| 2003 | 4 014 | 0.02 | 1 |
| 2004 | 3 279 | 0.02 | 1 |
| 2005 | 5 813 | 0.03 | 1 |
| 2006 | 4 059 | 0.02 | 1 |
| 2007 | 7 114 | 0.04 | 1 |
| 2008 | 4 351 | 0.02 | 1 |
| 2009 | 4 158 | 0.02 | 1 |
| 2010 | 2 301 | 0.01 | 1 |
| 2011 | 1 690 | 0.01 | 1 |
| 2012 | 4 656 | 0.02 | 1 |
| 2013 | 1 664 | 0.01 | 1 |
| 2014 | 1 439 | 0.01 | 1 |
| 2015 | 6 616 | 0.03 | 1 |
| 2016 | 6 703 | 0.03 | 1 |
| 2017 | 8 198 | 0.04 | 1 |
| 2018 | 6 418 | 0.03 | 1 |
| **Total (23 anos)** | **100 836** | **0.50** | **23** |

Ano calculado com `year(to_timestamp("timestamp"))` em UTC.

## Tipos para o DDL do Athena

O Athena (catálogo Glue/Hive) guarda os nomes das colunas em minúsculas: `userId` passa a `userid`. Na leitura de Parquet a correspondência de nomes não distingue maiúsculas, por isso os ficheiros não precisam de ser alterados.

`timestamp` é uma palavra reservada no Athena: no DDL escreve-se `` `timestamp` `` (entre backticks) e nas queries `"timestamp"` (entre aspas duplas).

| DuckDB | Athena |
|---|---|
| INTEGER | int |
| BIGINT | bigint |
| DOUBLE | double |
| VARCHAR | string |

### ratings

| Coluna no Athena | Tipo no Athena |
|---|---|
| userid | int |
| movieid | int |
| rating | double |
| timestamp | bigint |

### ratings_part

| Coluna no Athena | Tipo no Athena |
|---|---|
| userid | int |
| movieid | int |
| rating | double |
| timestamp | bigint |

Partição: `PARTITIONED BY (year int)`. Depois de criar a tabela, carregar as partições com `MSCK REPAIR TABLE` ou com um crawler do Glue (ou usar partition projection).

### ratings_csv

| Coluna no Athena | Tipo no Athena |
|---|---|
| userid | int |
| movieid | int |
| rating | double |
| timestamp | bigint |

CSV com cabeçalho: `ROW FORMAT DELIMITED FIELDS TERMINATED BY ','` e `TBLPROPERTIES ('skip.header.line.count'='1')`.

### movies

| Coluna no Athena | Tipo no Athena |
|---|---|
| movieid | int |
| title | string |
| genres | string |
