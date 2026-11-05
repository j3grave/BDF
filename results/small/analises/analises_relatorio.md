# Análises · MovieLens small

Gerado por `scripts/05_analises.py` em 0.0 s (sessão DuckDB em UTC).

## Fontes

- **ratings** — `parquet: data/small/parquet/ratings.parquet`
- **movies** — `parquet: data/small/parquet/movies.parquet`

## Verificações

| Verificação | Valor | OK |
|---|---|---|
| qualidade: linhas com nulos = 0 | 0 | sim |
| qualidade: fora da escala comum = 0 | 0 | sim |
| qualidade: pares (utilizador, filme) repetidos | 0 | sim |
| linhas = n_ratings do 04_eda.py | 100836 / 100836 | sim |
| utilizadores = n_utilizadores do 04_eda.py | 610 / 610 | sim |
| filmes = n_filmes_avaliados do 04_eda.py | 9724 / 9724 | sim |
| média global = rating_media do 04_eda.py | 3.502 / 3.502 | sim |
| soma de anual.num_ratings = linhas | 100836 / 100836 | sim |

## Queries

| Query | Linhas | Segundos | CSV |
|---|---:|---:|---|
| anual | 23 | 0.004 | `anual.csv` |
| ponderado | 10 | 0.003 | `ponderado.csv` |
| qualidade | 1 | 0.005 | `qualidade.csv` |
| valores_ano | 195 | 0.003 | `valores_ano.csv` |

## Versões Athena emuladas no DuckDB

Emulação: divisão inteira entre inteiros e macros para `from_unixtime`, `date_format`, `sequence` e `approx_percentile`. Valida a lógica, não a sintaxe do Trino.

| Query | Linhas DuckDB | Linhas Athena (emul.) | Iguais | Nota |
|---|---:|---:|---|---|
| anual | 23 | 23 | sim |  |
| ponderado | 10 | 10 | sim |  |
| qualidade | 1 | 1 | sim |  |
| valores_ano | 195 | 195 | sim |  |
