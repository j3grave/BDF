# Manifesto para a cloud: ml-32m

- Dataset: `32m`
- Gerado em: 2026-11-08T15:31:17 (DuckDB 2.0.0, 2.2 s)
- Pasta local: `data/cloud/ml-32m/` (origem: `data/32m/parquet/` e `data/32m/csv/ratings.csv`)
- Upload (fase seguinte, não executado): `aws s3 sync data/cloud/ml-32m/ s3://<bucket-dados>/ml-32m/`
- Verificações: contagens iguais à origem, soma das partições igual a `ratings`, contagens por ano iguais ao `ratings_by_year` da fase 1, tipos iguais à origem, `year` só no nome das pastas, compressão zstd e só ficheiros da tabela em cada pasta. Todas passaram.

> **Nota:** o benchmark DuckDB vs Athena deve ler os ficheiros de `data/cloud/`, que são exatamente os mesmos que vão para o S3 (zstd), e não os Parquet da fase 1 (snappy). Assim os dois motores leem os mesmos bytes.

## Tabelas

| Tabela | Caminho | Ficheiros | Tamanho (MB) | Linhas | Compressão |
|---|---|---:|---:|---:|---|
| ratings | `ratings/` | 1 | 158.90 | 32 000 204 | ZSTD |
| ratings_part | `ratings_part/year=AAAA/` | 29 | 151.01 | 32 000 204 | ZSTD |
| ratings_csv | `ratings_csv/` | 1 | 877.08 | 32 000 204 | nenhuma (CSV) |
| movies | `movies/` | 1 | 1.40 | 87 585 | ZSTD |
| tags | `tags/` | 1 | 13.23 | 2 000 072 | ZSTD |
| links | `links/` | 1 | 0.86 | 87 585 | ZSTD |

## Compressão: fase 1 vs cloud

| Tabela | Origem (fase 1) | Compressão origem | MB origem | MB cloud (zstd) | Variação |
|---|---|---|---:|---:|---:|
| ratings | `data/32m/parquet/ratings.parquet` | SNAPPY | 217.75 | 158.90 | -27.0 % |
| ratings_part | `data/32m/parquet/ratings_by_year/` | SNAPPY | 214.05 | 151.01 | -29.4 % |
| movies | `data/32m/parquet/movies.parquet` | SNAPPY | 2.19 | 1.40 | -35.9 % |
| tags | `data/32m/parquet/tags.parquet` | SNAPPY | 20.93 | 13.23 | -36.8 % |
| links | `data/32m/parquet/links.parquet` | SNAPPY | 1.25 | 0.86 | -31.6 % |

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

### tags

| Coluna | Tipo (DuckDB) |
|---|---|
| userId | INTEGER |
| movieId | INTEGER |
| tag | VARCHAR |
| timestamp | BIGINT |

### links

| Coluna | Tipo (DuckDB) |
|---|---|
| movieId | INTEGER |
| imdbId | VARCHAR |
| tmdbId | INTEGER |

## ratings_part: partições

| Ano | Linhas | Tamanho (MB) | Ficheiros |
|---|---:|---:|---:|
| 1995 | 4 | 0.00 | 1 |
| 1996 | 1 571 368 | 5.41 | 1 |
| 1997 | 685 388 | 2.52 | 1 |
| 1998 | 301 691 | 1.15 | 1 |
| 1999 | 1 174 629 | 4.56 | 1 |
| 2000 | 1 912 322 | 7.73 | 1 |
| 2001 | 1 160 098 | 5.07 | 1 |
| 2002 | 849 762 | 3.85 | 1 |
| 2003 | 1 011 000 | 4.83 | 1 |
| 2004 | 1 139 068 | 5.37 | 1 |
| 2005 | 1 752 573 | 8.22 | 1 |
| 2006 | 1 141 704 | 5.47 | 1 |
| 2007 | 1 023 813 | 5.08 | 1 |
| 2008 | 1 117 071 | 5.36 | 1 |
| 2009 | 890 696 | 4.45 | 1 |
| 2010 | 860 073 | 4.41 | 1 |
| 2011 | 729 301 | 3.81 | 1 |
| 2012 | 695 493 | 3.49 | 1 |
| 2013 | 563 301 | 2.86 | 1 |
| 2014 | 518 537 | 2.63 | 1 |
| 2015 | 1 743 866 | 8.56 | 1 |
| 2016 | 1 918 739 | 9.42 | 1 |
| 2017 | 1 827 953 | 8.92 | 1 |
| 2018 | 1 391 057 | 6.96 | 1 |
| 2019 | 1 385 467 | 6.97 | 1 |
| 2020 | 1 688 159 | 8.48 | 1 |
| 2021 | 1 239 912 | 6.42 | 1 |
| 2022 | 913 105 | 4.84 | 1 |
| 2023 | 794 054 | 4.18 | 1 |
| **Total (29 anos)** | **32 000 204** | **151.01** | **29** |

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

### tags

| Coluna no Athena | Tipo no Athena |
|---|---|
| userid | int |
| movieid | int |
| tag | string |
| timestamp | bigint |

### links

| Coluna no Athena | Tipo no Athena |
|---|---|
| movieid | int |
| imdbid | string |
| tmdbid | int |
