# Análises · MovieLens 1m

Gerado por `scripts/05_analises.py` em 0.7 s (sessão DuckDB em UTC).

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
| integridade: ids de filmes repetidos = 0 | 0 | sim |
| integridade: avaliações sem filme = 0 | 0 | sim |
| linhas = n_ratings do 04_eda.py | 1000209 / 1000209 | sim |
| utilizadores = n_utilizadores do 04_eda.py | 6040 / 6040 | sim |
| filmes = n_filmes_avaliados do 04_eda.py | 3706 / 3706 | sim |
| média global = rating_media do 04_eda.py | 3.582 / 3.582 | sim |
| soma de anual.num_ratings = linhas | 1000209 / 1000209 | sim |

## Queries

| Query | Linhas | Segundos | CSV |
|---|---:|---:|---|
| 10_flag_bots | 6040 | 0.053 | `10_flag_bots.csv` |
| 10_flag_bots_calibracao | 1 | 0.002 | `10_flag_bots_calibracao.csv` |
| anual | 4 | 0.008 | `anual.csv` |
| distribuicao | 5 | 0.006 | `distribuicao.csv` |
| eventos | 100 | 0.082 | `eventos.csv` |
| evolucao_filmes | 0 | 0.013 | `evolucao_filmes.csv` |
| filmes_ano | 0 | 0.015 | `filmes_ano.csv` |
| filtros_eventos | 1 | 0.085 | `filtros_eventos.csv` |
| grupos_atividade | 20 | 0.009 | `grupos_atividade.csv` |
| integridade | 1 | 0.004 | `integridade.csv` |
| mensal | 35 | 0.013 | `mensal.csv` |
| perfis_ativos | 4 | 0.009 | `perfis_ativos.csv` |
| perfis_cumulativos | 4 | 0.014 | `perfis_cumulativos.csv` |
| ponderado | 10 | 0.004 | `ponderado.csv` |
| qualidade | 1 | 0.017 | `qualidade.csv` |
| valores_ano | 20 | 0.005 | `valores_ano.csv` |

## Deteção de bots (10_flag_bots, a validar com o Luís)

- Utilizadores: 6040; suspeitos: 6 (0.10%) = regra A 6 + regra B 0 (sem repetir quem tem as duas).
- Submissão em lote (reportada à parte, não é bot): 339 utilizadores, dos quais 339 sem outra classificação.
- Ritmo sustentado depois do registo (máx. de eventos em 10 min), 2239 utilizadores: p50 14.0, p90 26.0, p99 35.0, p99,5 38.0, p99,9 40.0, máximo 45.
- Sinalizados pela regra A com o limiar no p99 / p99,5 / p99,9: 25 / 13 / 6 (a query usa o p99,9).

Submissão em lote por década do primeiro rating: 2000s: 339.

| userId | Classificação | Justificação |
|---|---|---|
| 1077 | suspeito (regra A) | regra A: 40 eventos em 10 min depois do registo (limiar p99,9 = 40.0), mediana de 14 s entre eventos; sinais complementares: 0/3 |
| 1117 | suspeito (regra A) | regra A: 40 eventos em 10 min depois do registo (limiar p99,9 = 40.0), mediana de 17 s entre eventos; sinais complementares: 0/3 |
| 1875 | suspeito (regra A) | regra A: 42 eventos em 10 min depois do registo (limiar p99,9 = 40.0), mediana de 15 s entre eventos; sinais complementares: 0/3 |
| 2880 | suspeito (regra A) | regra A: 45 eventos em 10 min depois do registo (limiar p99,9 = 40.0), mediana de 16 s entre eventos; sinais complementares: 0/3 |
| 5522 | suspeito (regra A) | regra A: 40 eventos em 10 min depois do registo (limiar p99,9 = 40.0), mediana de 18 s entre eventos; sinais complementares: 0/3 |
| 5536 | suspeito (regra A) | regra A: 40 eventos em 10 min depois do registo (limiar p99,9 = 40.0), mediana de 19 s entre eventos; sinais complementares: 0/3 |

## Versões Athena emuladas no DuckDB

Emulação: divisão inteira entre inteiros e macros para `from_unixtime`, `date_format`, `sequence` e `approx_percentile`. Valida a lógica, não a sintaxe do Trino.

| Query | Linhas DuckDB | Linhas Athena (emul.) | Iguais | Nota |
|---|---:|---:|---|---|
| 10_flag_bots | 6040 | 6040 | sim |  |
| 10_flag_bots_calibracao | 1 | 1 | sim |  |
| anual | 4 | 4 | sim |  |
| distribuicao | 5 | 5 | sim |  |
| eventos | 100 | 100 | sim |  |
| evolucao_filmes | 0 | 0 | sim |  |
| filmes_ano | 0 | 0 | sim |  |
| filtros_eventos | 1 | 1 | sim |  |
| grupos_atividade | 20 | 20 | sim |  |
| integridade | 1 | 1 | sim |  |
| mensal | 35 | 35 | sim |  |
| perfis_ativos | 4 | 4 | sim |  |
| perfis_cumulativos | 4 | 4 | sim |  |
| ponderado | 10 | 10 | sim |  |
| qualidade | 1 | 1 | sim |  |
| valores_ano | 20 | 20 | sim |  |
