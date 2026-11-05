# Análises · MovieLens 1m

Gerado por `scripts/05_analises.py` em 0.1 s (sessão DuckDB em UTC).

## Fontes

- **ratings** — `parquet: data/1m/parquet/ratings.parquet`
- **movies** — `parquet: data/1m/parquet/movies.parquet`

## Verificações

| Verificação | Valor | OK |
|---|---|---|
| qualidade: linhas com nulos = 0 | 0 | sim |
| qualidade: fora da escala comum = 0 | 0 | sim |
| qualidade: pares (utilizador, filme) repetidos | 0 | sim |
| qualidade (1M): só inteiros de 1 a 5 | 0 / 0 | sim |
| linhas = n_ratings do 04_eda.py | 1000209 / 1000209 | sim |
| utilizadores = n_utilizadores do 04_eda.py | 6040 / 6040 | sim |
| filmes = n_filmes_avaliados do 04_eda.py | 3706 / 3706 | sim |
| média global = rating_media do 04_eda.py | 3.582 / 3.582 | sim |
| soma de anual.num_ratings = linhas | 1000209 / 1000209 | sim |

## Queries

| Query | Linhas | Segundos | CSV |
|---|---:|---:|---|
| anual | 4 | 0.007 | `anual.csv` |
| ponderado | 10 | 0.003 | `ponderado.csv` |
| qualidade | 1 | 0.013 | `qualidade.csv` |
| valores_ano | 20 | 0.005 | `valores_ano.csv` |

## Versões Athena emuladas no DuckDB

Emulação: divisão inteira entre inteiros e macros para `from_unixtime`, `date_format`, `sequence` e `approx_percentile`. Valida a lógica, não a sintaxe do Trino.

| Query | Linhas DuckDB | Linhas Athena (emul.) | Iguais | Nota |
|---|---:|---:|---|---|
| anual | 4 | 4 | sim |  |
| ponderado | 10 | 10 | sim |  |
| qualidade | 1 | 1 | sim |  |
| valores_ano | 20 | 20 | sim |  |
