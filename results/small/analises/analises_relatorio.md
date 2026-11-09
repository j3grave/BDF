# Análises · MovieLens small

Gerado por `scripts/05_analises.py` em 0.3 s (sessão DuckDB em UTC).

## Fontes

- **ratings** — `parquet: data/small/parquet/ratings.parquet`
- **movies** — `parquet: data/small/parquet/movies.parquet`

## Verificações

| Verificação | Valor | OK |
|---|---|---|
| qualidade: linhas com nulos = 0 | 0 | sim |
| qualidade: fora da escala comum = 0 | 0 | sim |
| qualidade: pares (utilizador, filme) repetidos | 0 | sim |
| integridade: ids de filmes repetidos = 0 | 0 | sim |
| integridade: avaliações sem filme = 0 | 0 | sim |
| linhas = n_ratings do 04_eda.py | 100836 / 100836 | sim |
| utilizadores = n_utilizadores do 04_eda.py | 610 / 610 | sim |
| filmes = n_filmes_avaliados do 04_eda.py | 9724 / 9724 | sim |
| média global = rating_media do 04_eda.py | 3.502 / 3.502 | sim |
| soma de anual.num_ratings = linhas | 100836 / 100836 | sim |
| bots: utilizador 257 = sem sinais | sem sinais | sim |
| bots: utilizador 7 = sem sinais | sem sinais | sim |
| bots: utilizador 89 = suspeito (regra B) | suspeito (regra B) | sim |
| bots: utilizador 610 = suspeito (regra A) | suspeito (regra A) | sim |
| bots: utilizador 534 = submissão em lote | submissão em lote | sim |

## Queries

| Query | Linhas | Segundos | CSV |
|---|---:|---:|---|
| 10_flag_bots | 610 | 0.077 | `10_flag_bots.csv` |
| 10_flag_bots_calibracao | 1 | 0.011 | `10_flag_bots_calibracao.csv` |
| anual | 23 | 0.013 | `anual.csv` |
| distribuicao | 10 | 0.011 | `distribuicao.csv` |
| eventos | 0 | 0.036 | `eventos.csv` |
| evolucao_filmes | 366 | 0.013 | `evolucao_filmes.csv` |
| filmes_ano | 39 | 0.022 | `filmes_ano.csv` |
| filtros_eventos | 1 | 0.030 | `filtros_eventos.csv` |
| grupos_atividade | 108 | 0.015 | `grupos_atividade.csv` |
| integridade | 1 | 0.016 | `integridade.csv` |
| mensal | 267 | 0.015 | `mensal.csv` |
| perfis_ativos | 28 | 0.010 | `perfis_ativos.csv` |
| perfis_cumulativos | 39 | 0.011 | `perfis_cumulativos.csv` |
| ponderado | 10 | 0.011 | `ponderado.csv` |
| qualidade | 1 | 0.013 | `qualidade.csv` |
| valores_ano | 195 | 0.012 | `valores_ano.csv` |

## Deteção de bots (10_flag_bots, a validar com o Luís)

- Utilizadores: 610; suspeitos: 2 (0.33%) = regra A 1 + regra B 1 (sem repetir quem tem as duas).
- Submissão em lote (reportada à parte, não é bot): 13 utilizadores, dos quais 13 sem outra classificação.
- Ritmo sustentado depois do registo (máx. de eventos em 10 min), 248 utilizadores: p50 18.0, p90 52.3, p99 90.8, p99,5 100.6, p99,9 114.8, máximo 119.
- Sinalizados pela regra A com o limiar no p99 / p99,5 / p99,9: 3 / 2 / 1 (a query usa o p99,9).

Submissão em lote por década do primeiro rating: 1990s: 9, 2000s: 3, 2010s: 1.

| userId | Classificação | Justificação |
|---|---|---|
| 89 | suspeito (regra B) | regra B: 481 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 610 | suspeito (regra A) | regra A: 119 eventos em 10 min depois do registo (limiar p99,9 = 114.8), mediana de 4 s entre eventos; sinais complementares: 0/3 |

### Utilizadores de referência

| userId | Caso | Esperado | Obtido | OK | Justificação |
|---|---|---|---|---|---|
| 257 | 20 avaliações em 11 min no registo: não pode ser sinalizado | sem sinais | sem sinais | sim | depois do registo: máx. - eventos em 10 min (limiar 114.8); registo: 19 eventos, mediana de 4 s (a regra B exige >= 100 eventos e <= 2 s); máx. 2 avaliações no mesmo segundo; sinais complementares: 0/3 |
| 7 | uso normal: não pode ser sinalizado | sem sinais | sem sinais | sim | depois do registo: máx. 4 eventos em 10 min (limiar 114.8); registo: 102 eventos, mediana de 5 s (a regra B exige >= 100 eventos e <= 2 s); máx. 1 avaliações no mesmo segundo; sinais complementares: 0/3 |
| 89 | 518 avaliações em 23 min no registo, ~2 s cada: candidato | suspeito (regra B) | suspeito (regra B) | sim | regra B: 481 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 610 | 566 avaliações numa hora, ~4 s cada, ~6 meses depois do registo | suspeito (regra A) | suspeito (regra A) | sim | regra A: 119 eventos em 10 min depois do registo (limiar p99,9 = 114.8), mediana de 4 s entre eventos; sinais complementares: 0/3 |
| 534 | muitas avaliações no mesmo segundo (2016): não é bot | submissão em lote | submissão em lote | sim | submissão em lote: até 128 avaliações no mesmo segundo (4% dos eventos com 2 ou mais), primeiro dia 2016-04-04; sinais complementares: 0/3 |
