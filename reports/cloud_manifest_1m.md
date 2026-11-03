# Manifesto para a cloud: ml-1m

- Dataset: `1m`
- Gerado em: 2026-11-03T21:16:26 (DuckDB 1.5.6, 0.1 s)
- Pasta local: `data/cloud/ml-1m/` (origem: `data/1m/parquet/` e `data/1m/csv/ratings.csv`)
- Upload (fase seguinte, não executado): `aws s3 sync data/cloud/ml-1m/ s3://<bucket-dados>/ml-1m/`
- Verificações: contagens iguais à origem, soma das partições igual a `ratings`, contagens por ano iguais ao `ratings_by_year` da fase 1, tipos iguais à origem, `year` só no nome das pastas, compressão zstd e só ficheiros da tabela em cada pasta. Todas passaram.

> **Nota:** o benchmark DuckDB vs Athena deve ler os ficheiros de `data/cloud/`, que são exatamente os mesmos que vão para o S3 (zstd), e não os Parquet da fase 1 (snappy). Assim os dois motores leem os mesmos bytes.

## Tabelas

| Tabela | Caminho | Ficheiros | Tamanho (MB) | Linhas | Compressão |
|---|---|---:|---:|---:|---|
| ratings | `ratings/` | 1 | 4.02 | 1 000 209 | ZSTD |
| ratings_part | `ratings_part/year=AAAA/` | 4 | 4.04 | 1 000 209 | ZSTD |
| ratings_csv | `ratings_csv/` | 1 | 23.59 | 1 000 209 | nenhuma (CSV) |
| movies | `movies/` | 1 | 0.06 | 3 883 | ZSTD |

## Compressão: fase 1 vs cloud

| Tabela | Origem (fase 1) | Compressão origem | MB origem | MB cloud (zstd) | Variação |
|---|---|---|---:|---:|---:|
| ratings | `data/1m/parquet/ratings.parquet` | SNAPPY | 5.21 | 4.02 | -22.8 % |
| ratings_part | `data/1m/parquet/ratings_by_year/` | SNAPPY | 5.25 | 4.04 | -23.0 % |
| movies | `data/1m/parquet/movies.parquet` | SNAPPY | 0.09 | 0.06 | -32.5 % |

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
| 2000 | 904 757 | 3.58 | 1 |
| 2001 | 68 058 | 0.32 | 1 |
| 2002 | 24 046 | 0.12 | 1 |
| 2003 | 3 348 | 0.02 | 1 |
| **Total (4 anos)** | **1 000 209** | **4.04** | **4** |

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
