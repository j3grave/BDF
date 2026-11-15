# Manifesto para a cloud: imdb

- Gerado em: 2026-11-15T16:09:45 (DuckDB 2.0.0, 2.9 s)
- Pasta local: `data/cloud/imdb/` -> `s3://<bucket-dados>/imdb/` (a mesma para os três datasets)
- Verificações: o mesmo n.º de linhas na origem, no Parquet zstd e no TSV.gz. Todas passaram.

| Tabela | Parquet (zstd) | MB | TSV comprimido (gzip) | MB | Linhas |
|---|---|---:|---|---:|---:|
| title_ratings | `imdb/title_ratings/` | 8.7 | `imdb/title_ratings_tsv/` | 8.8 | 1 732 558 |
| title_basics | `imdb/title_basics/` | 284.9 | `imdb/title_basics_tsv/` | 230.4 | 12 965 577 |

No Athena, as tabelas `imdb_title_ratings_tsv` e `imdb_title_basics_tsv` leem o TSV.gz (`\N` = nulo, `skip.header.line.count` = 1) e as tabelas sem `_tsv` leem o Parquet.
