# Análises · MovieLens 32m

Gerado por `scripts/04_analise.py` em 10.7 s (sessão DuckDB em UTC).

## Fontes

- **ratings** — `parquet: data/32m/parquet/ratings.parquet`
- **movies** — `parquet: data/32m/parquet/movies.parquet`

## Verificações

| Verificação | Valor | OK |
|---|---|---|
| qualidade: linhas com nulos = 0 | 0 | sim |
| qualidade: fora da escala comum = 0 | 0 | sim |
| qualidade: pares (utilizador, filme) repetidos | 0 | sim |
| integridade: ids de filmes repetidos = 0 | 0 | sim |
| integridade: avaliações sem filme = 0 | 0 | sim |
| linhas = n_ratings da EDA | 32000204 / 32000204 | sim |
| utilizadores = n_utilizadores da EDA | 200948 / 200948 | sim |
| filmes = n_filmes_avaliados da EDA | 84432 / 84432 | sim |
| média global = rating_media da EDA | 3.540 / 3.540 | sim |
| soma de anual.num_ratings = linhas | 32000204 / 32000204 | sim |

## Queries

| Query | Linhas | Segundos | CSV |
|---|---:|---:|---|
| 10_flag_bots | 200948 | 1.750 | `10_flag_bots.csv` |
| 10_flag_bots_calibracao | 1 | 0.007 | `10_flag_bots_calibracao.csv` |
| anual | 29 | 0.116 | `anual.csv` |
| distribuicao | 10 | 0.087 | `distribuicao.csv` |
| eventos | 100 | 3.813 | `eventos.csv` |
| evolucao_filmes | 14758 | 0.187 | `evolucao_filmes.csv` |
| filmes_ano | 22 | 0.214 | `filmes_ano.csv` |
| filtros_eventos | 1 | 2.572 | `filtros_eventos.csv` |
| grupos_atividade | 142 | 0.134 | `grupos_atividade.csv` |
| integridade | 1 | 0.040 | `integridade.csv` |
| mensal | 334 | 0.245 | `mensal.csv` |
| perfis_ativos | 67 | 0.140 | `perfis_ativos.csv` |
| perfis_cumulativos | 70 | 0.665 | `perfis_cumulativos.csv` |
| ponderado | 10 | 0.051 | `ponderado.csv` |
| qualidade | 1 | 0.349 | `qualidade.csv` |
| valores_ano | 248 | 0.100 | `valores_ano.csv` |

## Deteção de bots (10_flag_bots)

- Utilizadores: 200948; suspeitos: 460 (0.23%) = regra A 83 + regra B 382 (sem repetir quem tem as duas).
- Submissão em lote (reportada à parte, não é bot): 6165 utilizadores, dos quais 6138 sem outra classificação.
- Ritmo sustentado depois do registo (máx. de eventos em 10 min), 82819 utilizadores: p50 16.0, p90 53.0, p99 107.0, p99,5 124.0, p99,9 169.2, máximo 516.
- Sinalizados pela regra A com o limiar no p99 / p99,5 / p99,9: 836 / 418 / 83 (a query usa o p99,9).

Submissão em lote por década do primeiro rating: 1990s: 2962, 2000s: 1380, 2010s: 1071, 2020s: 752.

| userId | Classificação | Justificação |
|---|---|---|
| 316 | suspeito (regra B) | regra B: 113 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 556 | suspeito (regra B) | regra B: 371 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 716 | suspeito (regra B) | regra B: 109 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 2164 | suspeito (regra B) | regra B: 403 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 2353 | suspeito (regra B) | regra B: 129 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 2864 | suspeito (regra B) | regra B: 160 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 3339 | suspeito (regra B) | regra B: 218 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); submissão em lote: até 80 avaliações no mesmo segundo (4% dos eventos com 2 ou mais), primeiro dia 2018-10-23; sinais complementares: 0/3 |
| 4554 | suspeito (regra B) | regra B: 114 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 4572 | suspeito (regra B) | regra B: 244 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 4675 | suspeito (regra B) | regra B: 251 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 5277 | suspeito (regra B) | regra B: 224 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 5723 | suspeito (regra B) | regra B: 527 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 6076 | suspeito (regra B) | regra B: 351 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 6166 | suspeito (regra B) | regra B: 157 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 6273 | suspeito (regra B) | regra B: 108 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 6613 | suspeito (regra B) | regra B: 107 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 6883 | suspeito (regra B) | regra B: 116 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 7476 | suspeito (regra B) | regra B: 332 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 7575 | suspeito (regra B) | regra B: 224 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 8009 | suspeito (regra B) | regra B: 235 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 8023 | suspeito (regra B) | regra B: 441 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 8120 | suspeito (regra A) | regra A: 241 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 2 s entre eventos; sinais complementares: 1/3 |
| 8514 | suspeito (regra B) | regra B: 146 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 9085 | suspeito (regra B) | regra B: 104 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); submissão em lote: até 95 avaliações no mesmo segundo (76% dos eventos com 2 ou mais), primeiro dia 2022-02-05; sinais complementares: 0/3 |
| 9238 | suspeito (regra B) | regra B: 1109 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 9339 | suspeito (regra B) | regra B: 103 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 9453 | suspeito (regra B) | regra B: 218 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 9569 | suspeito (regra B) | regra B: 234 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 10170 | suspeito (regra B) | regra B: 108 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 10534 | suspeito (regra B) | regra B: 153 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 10723 | suspeito (regra B) | regra B: 554 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 11250 | suspeito (regra B) | regra B: 170 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 11511 | suspeito (regra A) | regra A: 452 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 1 s entre eventos; submissão em lote: até 10 avaliações no mesmo segundo (27% dos eventos com 2 ou mais), primeiro dia 2014-06-14; sinais complementares: 0/3 |
| 11617 | suspeito (regra B) | regra B: 101 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 12125 | suspeito (regra B) | regra B: 116 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 12779 | suspeito (regra B) | regra B: 352 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 12933 | suspeito (regra B) | regra B: 222 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 13076 | suspeito (regra B) | regra B: 162 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 13241 | suspeito (regra A) | regra A: 251 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 13450 | suspeito (regra A) | regra A: 188 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 1 s entre eventos; submissão em lote: até 23 avaliações no mesmo segundo (95% dos eventos com 2 ou mais), primeiro dia 2015-04-28; sinais complementares: 0/3 |
| 13750 | suspeito (regra B) | regra B: 135 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 14383 | suspeito (regra B) | regra B: 264 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 15114 | suspeito (regra B) | regra B: 207 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 15968 | suspeito (regra A) | regra A: 214 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 11 s entre eventos; sinais complementares: 0/3 |
| 16050 | suspeito (regra B) | regra B: 176 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 17035 | suspeito (regra A) | regra A: 267 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 18404 s entre eventos; submissão em lote: até 30 avaliações no mesmo segundo (8% dos eventos com 2 ou mais), primeiro dia 2012-12-13; sinais complementares: 0/3 |
| 17146 | suspeito (regra B) | regra B: 511 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 17311 | suspeito (regra B) | regra B: 143 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 17521 | suspeito (regra B) | regra B: 109 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 17897 | suspeito (regra A) | regra A: 183 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 18149 | suspeito (regra B) | regra B: 297 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 18933 | suspeito (regra B) | regra B: 476 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 20865 | suspeito (regra B) | regra B: 109 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 21011 | suspeito (regra B) | regra B: 188 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); submissão em lote: até 132 avaliações no mesmo segundo (25% dos eventos com 2 ou mais), primeiro dia 2016-10-18; sinais complementares: 0/3 |
| 21316 | suspeito (regra B) | regra B: 118 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 21427 | suspeito (regra B) | regra B: 113 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 21622 | suspeito (regra B) | regra B: 220 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 21748 | suspeito (regra B) | regra B: 101 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 22096 | suspeito (regra A) | regra A: 171 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 5 s entre eventos; sinais complementares: 0/3 |
| 22110 | suspeito (regra B) | regra B: 114 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 22470 | suspeito (regra B) | regra B: 217 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 23290 | suspeito (regra B) | regra B: 149 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 24001 | suspeito (regra B) | regra B: 241 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 24613 | suspeito (regra B) | regra B: 144 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); submissão em lote: até 24 avaliações no mesmo segundo (98% dos eventos com 2 ou mais), primeiro dia 2015-11-04; sinais complementares: 0/3 |
| 24682 | suspeito (regra B) | regra B: 117 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 25012 | suspeito (regra B) | regra B: 138 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 25346 | suspeito (regra B) | regra B: 192 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 25861 | suspeito (regra B) | regra B: 140 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 25926 | suspeito (regra A) | regra A: 175 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 2 s entre eventos; sinais complementares: 0/3 |
| 26402 | suspeito (regra B) | regra B: 159 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 26450 | suspeito (regra A) | regra A: 182 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 26862 | suspeito (regra B) | regra B: 613 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 27232 | suspeito (regra B) | regra B: 197 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 27628 | suspeito (regra B) | regra B: 130 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 27655 | suspeito (regra B) | regra B: 330 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 27756 | suspeito (regra B) | regra B: 105 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 28039 | suspeito (regra A) | regra A: 177 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 4 s entre eventos; sinais complementares: 0/3 |
| 28084 | suspeito (regra B) | regra B: 131 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 28229 | suspeito (regra B) | regra B: 188 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 28409 | suspeito (regra B) | regra B: 174 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 1/3 |
| 28869 | suspeito (regra B) | regra B: 150 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 29241 | suspeito (regra B) | regra B: 184 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 29304 | suspeito (regra B) | regra B: 297 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 29743 | suspeito (regra A) | regra A: 516 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 1 s entre eventos; sinais complementares: 0/3 |
| 30030 | suspeito (regra B) | regra B: 137 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 30317 | suspeito (regra B) | regra B: 115 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 30497 | suspeito (regra B) | regra B: 247 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 30887 | suspeito (regra B) | regra B: 225 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 30910 | suspeito (regra A) | regra A: 320 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 2 s entre eventos; sinais complementares: 0/3 |
| 31891 | suspeito (regra A) | regra A: 240 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 2 s entre eventos; sinais complementares: 0/3 |
| 31935 | suspeito (regra B) | regra B: 435 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 32190 | suspeito (regra B) | regra B: 137 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 32235 | suspeito (regra A) | regra A: 186 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 14 s entre eventos; sinais complementares: 0/3 |
| 32526 | suspeito (regra A) | regra A: 188 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 2 s entre eventos; sinais complementares: 0/3 |
| 32614 | suspeito (regra A) | regra A: 172 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 4 s entre eventos; sinais complementares: 0/3 |
| 33212 | suspeito (regra B) | regra B: 127 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 33461 | suspeito (regra B) | regra B: 378 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 33856 | suspeito (regra B) | regra B: 185 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 33997 | suspeito (regra B) | regra B: 213 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 34370 | suspeito (regra B) | regra B: 217 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 34533 | suspeito (regra B) | regra B: 149 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 34864 | suspeito (regra B) | regra B: 178 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); submissão em lote: até 26 avaliações no mesmo segundo (32% dos eventos com 2 ou mais), primeiro dia 2015-11-19; sinais complementares: 0/3 |
| 34901 | suspeito (regra B) | regra B: 107 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 34972 | suspeito (regra B) | regra B: 259 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 35874 | suspeito (regra B) | regra B: 198 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 36091 | suspeito (regra B) | regra B: 367 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 36194 | suspeito (regra B) | regra B: 612 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 36303 | suspeito (regra B) | regra B: 138 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 36910 | suspeito (regra A) | regra A: 208 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 37286 | suspeito (regra B) | regra B: 116 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 37493 | suspeito (regra B) | regra B: 225 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 39020 | suspeito (regra A) | regra A: 183 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 39130 | suspeito (regra B) | regra B: 846 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 39140 | suspeito (regra B) | regra B: 223 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 39855 | suspeito (regra B) | regra B: 130 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 39940 | suspeito (regra A) | regra A: 225 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 6 s entre eventos; sinais complementares: 0/3 |
| 40038 | suspeito (regra B) | regra B: 171 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 40335 | suspeito (regra B) | regra B: 257 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 40344 | suspeito (regra B) | regra B: 101 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 1/3 |
| 40698 | suspeito (regra A) | regra A: 194 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 7 s entre eventos; sinais complementares: 0/3 |
| 41277 | suspeito (regra B) | regra B: 106 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 42043 | suspeito (regra B) | regra B: 346 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 43001 | suspeito (regra B) | regra B: 102 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 43154 | suspeito (regra B) | regra B: 116 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 43703 | suspeito (regra B) | regra B: 109 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); submissão em lote: até 99 avaliações no mesmo segundo (87% dos eventos com 2 ou mais), primeiro dia 2022-09-30; sinais complementares: 0/3 |
| 43986 | suspeito (regra B) | regra B: 107 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 44021 | suspeito (regra A) | regra A: 344 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 1 s entre eventos; submissão em lote: até 18 avaliações no mesmo segundo (20% dos eventos com 2 ou mais), primeiro dia 2008-09-09; sinais complementares: 0/3 |
| 45342 | suspeito (regra B) | regra B: 139 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 45423 | suspeito (regra B) | regra B: 495 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 45498 | suspeito (regra B) | regra B: 230 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 45651 | suspeito (regra B) | regra B: 488 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 46947 | suspeito (regra B) | regra B: 178 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 47090 | suspeito (regra A) | regra A: 179 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 22 s entre eventos; sinais complementares: 0/3 |
| 47956 | suspeito (regra B) | regra B: 132 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 48764 | suspeito (regra B) | regra B: 198 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 48916 | suspeito (regra B) | regra B: 237 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 49079 | suspeito (regra B) | regra B: 174 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 49852 | suspeito (regra B) | regra B: 136 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 50704 | suspeito (regra B) | regra B: 163 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 51342 | suspeito (regra B) | regra B: 224 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 51669 | suspeito (regra B) | regra B: 155 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 53215 | suspeito (regra B) | regra B: 117 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 53664 | suspeito (regra B) | regra B: 192 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 54315 | suspeito (regra A) | regra A: 175 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 13 s entre eventos; sinais complementares: 0/3 |
| 55863 | suspeito (regra B) | regra B: 335 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 56136 | suspeito (regra B) | regra B: 110 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 56883 | suspeito (regra A) | regra A: 177 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 4 s entre eventos; submissão em lote: até 10 avaliações no mesmo segundo (10% dos eventos com 2 ou mais), primeiro dia 2002-08-06; sinais complementares: 0/3 |
| 57602 | suspeito (regra B) | regra B: 129 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 57832 | suspeito (regra B) | regra B: 143 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 57859 | suspeito (regra B) | regra B: 136 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 59036 | suspeito (regra B) | regra B: 101 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 59581 | suspeito (regra B) | regra B: 106 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 1/3 |
| 59767 | suspeito (regra B) | regra B: 117 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 60397 | suspeito (regra A) | regra A: 254 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 2 s entre eventos; sinais complementares: 0/3 |
| 60433 | suspeito (regra B) | regra B: 296 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 61278 | suspeito (regra B) | regra B: 116 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 61488 | suspeito (regra B) | regra B: 153 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 61543 | suspeito (regra A) | regra A: 265 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 12 s entre eventos; sinais complementares: 0/3 |
| 61686 | suspeito (regra B) | regra B: 223 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 61771 | suspeito (regra B) | regra B: 228 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 63076 | suspeito (regra B) | regra B: 105 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 63114 | suspeito (regra B) | regra B: 388 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 64830 | suspeito (regra B) | regra B: 765 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 64972 | suspeito (regra B) | regra B: 646 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 65452 | suspeito (regra B) | regra B: 104 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 65458 | suspeito (regra A) | regra A: 172 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 66317 | suspeito (regra A) | regra A: 170 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 16 s entre eventos; sinais complementares: 0/3 |
| 67307 | suspeito (regra B) | regra B: 104 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 68821 | suspeito (regra A) | regra A: 208 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 9320 s entre eventos; sinais complementares: 0/3 |
| 70483 | suspeito (regra A) | regra A: 247 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 34926 s entre eventos; sinais complementares: 0/3 |
| 70903 | suspeito (regra B) | regra B: 109 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 71323 | suspeito (regra A) | regra A: 210 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 2 s entre eventos; sinais complementares: 0/3 |
| 71523 | suspeito (regra A) | regra A: 246 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 2 s entre eventos; sinais complementares: 0/3 |
| 73107 | suspeito (regra A) | regra A: 194 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 11 s entre eventos; sinais complementares: 0/3 |
| 74268 | suspeito (regra B) | regra B: 121 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 74956 | suspeito (regra B) | regra B: 142 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 2/3 |
| 75243 | suspeito (regra A) | regra A: 197 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 75488 | suspeito (regra B) | regra B: 161 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 76060 | suspeito (regra B) | regra B: 137 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); sinais complementares: 2/3 |
| 76471 | suspeito (regra B) | regra B: 125 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 76629 | suspeito (regra B) | regra B: 791 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 76718 | suspeito (regra B) | regra B: 199 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 76766 | suspeito (regra B) | regra B: 389 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 76809 | suspeito (regra B) | regra B: 172 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 76832 | suspeito (regra B) | regra B: 449 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 77018 | suspeito (regra B) | regra B: 124 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 77161 | suspeito (regra B) | regra B: 103 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 77579 | suspeito (regra B) | regra B: 220 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 78015 | suspeito (regra B) | regra B: 139 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 78026 | suspeito (regra B) | regra B: 561 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 78051 | suspeito (regra A) | regra A: 222 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 1 s entre eventos; sinais complementares: 0/3 |
| 78140 | suspeito (regra B) | regra B: 132 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 78195 | suspeito (regra A) | regra A: 247 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 2 s entre eventos; sinais complementares: 0/3 |
| 79145 | suspeito (regra B) | regra B: 128 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 79352 | suspeito (regra B) | regra B: 124 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 79732 | suspeito (regra B) | regra B: 349 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 79967 | suspeito (regra B) | regra B: 112 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 2/3 |
| 80445 | suspeito (regra B) | regra B: 101 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 80501 | suspeito (regra B) | regra B: 899 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 80618 | suspeito (regra A) | regra A: 201 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 82599 | suspeito (regras A e B) | regra A: 179 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 2 s entre eventos; regra B: 1187 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 83156 | suspeito (regra B) | regra B: 179 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 84285 | suspeito (regra A) | regra A: 178 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 4 s entre eventos; sinais complementares: 0/3 |
| 84379 | suspeito (regra B) | regra B: 225 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 84409 | suspeito (regra A) | regra A: 277 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 4 s entre eventos; sinais complementares: 0/3 |
| 84423 | suspeito (regra B) | regra B: 111 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 84793 | suspeito (regra B) | regra B: 131 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 84941 | suspeito (regra B) | regra B: 115 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 84991 | suspeito (regra B) | regra B: 145 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); submissão em lote: até 14 avaliações no mesmo segundo (39% dos eventos com 2 ou mais), primeiro dia 2016-01-03; sinais complementares: 0/3 |
| 85243 | suspeito (regra B) | regra B: 112 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 85312 | suspeito (regra B) | regra B: 2754 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 85888 | suspeito (regra B) | regra B: 166 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 86167 | suspeito (regra A) | regra A: 352 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 2 s entre eventos; sinais complementares: 0/3 |
| 86450 | suspeito (regra B) | regra B: 189 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 87185 | suspeito (regra B) | regra B: 119 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 87391 | suspeito (regra B) | regra B: 633 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 88831 | suspeito (regra B) | regra B: 109 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 89087 | suspeito (regra B) | regra B: 147 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 89913 | suspeito (regra B) | regra B: 164 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 91287 | suspeito (regra B) | regra B: 232 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 91402 | suspeito (regra B) | regra B: 184 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 92675 | suspeito (regra B) | regra B: 100 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 92876 | suspeito (regra B) | regra B: 191 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 94119 | suspeito (regra B) | regra B: 130 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); submissão em lote: até 26 avaliações no mesmo segundo (76% dos eventos com 2 ou mais), primeiro dia 2015-06-21; sinais complementares: 0/3 |
| 94220 | suspeito (regra A) | regra A: 179 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 4 s entre eventos; sinais complementares: 0/3 |
| 95229 | suspeito (regra B) | regra B: 120 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 95246 | suspeito (regra B) | regra B: 153 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 96145 | suspeito (regra B) | regra B: 430 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 96758 | suspeito (regra B) | regra B: 180 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 97085 | suspeito (regra B) | regra B: 446 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 99244 | suspeito (regra B) | regra B: 137 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 99489 | suspeito (regra B) | regra B: 130 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 99792 | suspeito (regra B) | regra B: 215 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 100407 | suspeito (regra B) | regra B: 180 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 101370 | suspeito (regra A) | regra A: 226 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 2 s entre eventos; sinais complementares: 0/3 |
| 101752 | suspeito (regra B) | regra B: 140 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 103468 | suspeito (regra B) | regra B: 137 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 103965 | suspeito (regra A) | regra A: 172 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 104016 | suspeito (regra B) | regra B: 456 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 104080 | suspeito (regra A) | regra A: 172 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 104645 | suspeito (regra A) | regra A: 173 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 4 s entre eventos; sinais complementares: 0/3 |
| 104746 | suspeito (regra B) | regra B: 293 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 104859 | suspeito (regra A) | regra A: 176 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 105646 | suspeito (regra B) | regra B: 160 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 105883 | suspeito (regra B) | regra B: 1061 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 106086 | suspeito (regra B) | regra B: 529 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 106322 | suspeito (regra A) | regra A: 189 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 41 s entre eventos; sinais complementares: 0/3 |
| 107226 | suspeito (regra B) | regra B: 321 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 107263 | suspeito (regra B) | regra B: 363 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 108381 | suspeito (regra A) | regra A: 266 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 2 s entre eventos; sinais complementares: 0/3 |
| 109704 | suspeito (regras A e B) | regra A: 170 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 2 s entre eventos; regra B: 496 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 110423 | suspeito (regra A) | regra A: 175 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 110554 | suspeito (regra B) | regra B: 324 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 110935 | suspeito (regra B) | regra B: 130 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 111225 | suspeito (regra B) | regra B: 104 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); submissão em lote: até 26 avaliações no mesmo segundo (79% dos eventos com 2 ou mais), primeiro dia 2016-01-06; sinais complementares: 0/3 |
| 112185 | suspeito (regra B) | regra B: 299 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 112311 | suspeito (regra B) | regra B: 375 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 112991 | suspeito (regra B) | regra B: 107 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 113453 | suspeito (regra B) | regra B: 150 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 113616 | suspeito (regra B) | regra B: 177 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 114038 | suspeito (regra B) | regra B: 226 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 114117 | suspeito (regra B) | regra B: 179 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 114478 | suspeito (regra B) | regra B: 433 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 114503 | suspeito (regra B) | regra B: 216 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 114977 | suspeito (regra B) | regra B: 130 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 115209 | suspeito (regra B) | regra B: 416 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 115580 | suspeito (regra A) | regra A: 209 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 115761 | suspeito (regra B) | regra B: 194 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 116047 | suspeito (regra B) | regra B: 158 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 116927 | suspeito (regra A) | regra A: 194 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 5 s entre eventos; sinais complementares: 0/3 |
| 117249 | suspeito (regra B) | regra B: 290 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 117318 | suspeito (regra B) | regra B: 305 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 118142 | suspeito (regra A) | regra A: 170 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 7 s entre eventos; sinais complementares: 0/3 |
| 120531 | suspeito (regra B) | regra B: 253 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 122253 | suspeito (regra B) | regra B: 127 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 123047 | suspeito (regra B) | regra B: 180 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 123054 | suspeito (regra B) | regra B: 176 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 123249 | suspeito (regra B) | regra B: 429 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 123464 | suspeito (regra B) | regra B: 572 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 125323 | suspeito (regra B) | regra B: 556 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 125470 | suspeito (regra B) | regra B: 316 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 125507 | suspeito (regra B) | regra B: 189 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); submissão em lote: até 93 avaliações no mesmo segundo (43% dos eventos com 2 ou mais), primeiro dia 2017-02-02; sinais complementares: 0/3 |
| 125720 | suspeito (regra B) | regra B: 102 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 126075 | suspeito (regras A e B) | regra A: 194 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 2 s entre eventos; regra B: 402 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 127124 | suspeito (regra B) | regra B: 100 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 127171 | suspeito (regra B) | regra B: 2988 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 1/3 |
| 127335 | suspeito (regra B) | regra B: 468 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); submissão em lote: até 68 avaliações no mesmo segundo (95% dos eventos com 2 ou mais), primeiro dia 2016-01-30; sinais complementares: 0/3 |
| 128818 | suspeito (regra B) | regra B: 102 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 129705 | suspeito (regra B) | regra B: 122 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); submissão em lote: até 64 avaliações no mesmo segundo (59% dos eventos com 2 ou mais), primeiro dia 2016-12-20; sinais complementares: 0/3 |
| 130742 | suspeito (regra B) | regra B: 572 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 130837 | suspeito (regra B) | regra B: 184 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 131613 | suspeito (regra B) | regra B: 120 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); submissão em lote: até 24 avaliações no mesmo segundo (65% dos eventos com 2 ou mais), primeiro dia 2015-07-28; sinais complementares: 0/3 |
| 131675 | suspeito (regra A) | regra A: 301 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 2 s entre eventos; sinais complementares: 0/3 |
| 131729 | suspeito (regra A) | regra A: 181 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 5 s entre eventos; sinais complementares: 0/3 |
| 132696 | suspeito (regra A) | regra A: 182 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 132839 | suspeito (regra B) | regra B: 1339 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 134087 | suspeito (regra B) | regra B: 228 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 136970 | suspeito (regra B) | regra B: 480 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 137524 | suspeito (regra B) | regra B: 242 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 137947 | suspeito (regra B) | regra B: 326 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 138449 | suspeito (regra B) | regra B: 126 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 138464 | suspeito (regra B) | regra B: 109 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 138718 | suspeito (regra B) | regra B: 169 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 138940 | suspeito (regra B) | regra B: 112 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 139011 | suspeito (regra B) | regra B: 115 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 139071 | suspeito (regra B) | regra B: 142 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 139252 | suspeito (regra B) | regra B: 338 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 139576 | suspeito (regra B) | regra B: 283 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 139843 | suspeito (regra B) | regra B: 116 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 140462 | suspeito (regra B) | regra B: 467 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 1/3 |
| 140924 | suspeito (regra B) | regra B: 868 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 141868 | suspeito (regra B) | regra B: 177 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 142672 | suspeito (regra A) | regra A: 178 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 4 s entre eventos; sinais complementares: 0/3 |
| 142801 | suspeito (regra B) | regra B: 192 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 143325 | suspeito (regra A) | regra A: 174 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 144108 | suspeito (regra A) | regra A: 172 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 144194 | suspeito (regra B) | regra B: 107 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 144257 | suspeito (regra B) | regra B: 1043 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 145010 | suspeito (regra B) | regra B: 185 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 145553 | suspeito (regra B) | regra B: 119 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 146447 | suspeito (regra B) | regra B: 280 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 146576 | suspeito (regra B) | regra B: 120 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 146593 | suspeito (regra B) | regra B: 138 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 146845 | suspeito (regra B) | regra B: 554 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 147502 | suspeito (regra B) | regra B: 154 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 148507 | suspeito (regra A) | regra A: 186 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 148508 | suspeito (regra B) | regra B: 113 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 148704 | suspeito (regra B) | regra B: 121 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 148732 | suspeito (regra B) | regra B: 884 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 149152 | suspeito (regra B) | regra B: 1002 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 150536 | suspeito (regra B) | regra B: 289 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 151030 | suspeito (regra B) | regra B: 142 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 152015 | suspeito (regra B) | regra B: 139 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 152048 | suspeito (regra B) | regra B: 182 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 152357 | suspeito (regra A) | regra A: 196 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; submissão em lote: até 40 avaliações no mesmo segundo (4% dos eventos com 2 ou mais), primeiro dia 2021-11-17; sinais complementares: 0/3 |
| 152510 | suspeito (regra B) | regra B: 209 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); submissão em lote: até 12 avaliações no mesmo segundo (63% dos eventos com 2 ou mais), primeiro dia 2002-11-11; sinais complementares: 0/3 |
| 153385 | suspeito (regra B) | regra B: 104 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 153669 | suspeito (regra B) | regra B: 110 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 154550 | suspeito (regra B) | regra B: 184 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 155162 | suspeito (regra B) | regra B: 117 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 155227 | suspeito (regra B) | regra B: 164 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 156129 | suspeito (regra B) | regra B: 169 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 156523 | suspeito (regra B) | regra B: 783 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 156627 | suspeito (regra B) | regra B: 105 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 156864 | suspeito (regra B) | regra B: 131 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 157788 | suspeito (regras A e B) | regra A: 173 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 2 s entre eventos; regra B: 511 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 158657 | suspeito (regra B) | regra B: 368 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 158752 | suspeito (regra B) | regra B: 199 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 159300 | suspeito (regra B) | regra B: 178 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); submissão em lote: até 21 avaliações no mesmo segundo (6% dos eventos com 2 ou mais), primeiro dia 2015-06-20; sinais complementares: 0/3 |
| 159555 | suspeito (regra A) | regra A: 292 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; submissão em lote: até 11 avaliações no mesmo segundo (7% dos eventos com 2 ou mais), primeiro dia 2016-01-12; sinais complementares: 0/3 |
| 160198 | suspeito (regra B) | regra B: 204 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 160412 | suspeito (regra B) | regra B: 143 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 160461 | suspeito (regra B) | regra B: 103 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 161169 | suspeito (regra A) | regra A: 184 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 9298 s entre eventos; sinais complementares: 0/3 |
| 161410 | suspeito (regra B) | regra B: 104 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); sinais complementares: 2/3 |
| 161412 | suspeito (regra B) | regra B: 127 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 161874 | suspeito (regra B) | regra B: 234 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 162281 | suspeito (regra B) | regra B: 136 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 162491 | suspeito (regra B) | regra B: 217 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 163262 | suspeito (regra A) | regra A: 184 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 164244 | suspeito (regra B) | regra B: 169 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 164886 | suspeito (regra B) | regra B: 162 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 164925 | suspeito (regra B) | regra B: 176 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 165239 | suspeito (regra B) | regra B: 126 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 165310 | suspeito (regra B) | regra B: 216 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 165423 | suspeito (regra B) | regra B: 109 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 165448 | suspeito (regra B) | regra B: 247 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 165516 | suspeito (regra B) | regra B: 155 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 165651 | suspeito (regra B) | regra B: 210 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 166007 | suspeito (regra B) | regra B: 1470 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 166074 | suspeito (regra B) | regra B: 116 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 166229 | suspeito (regra B) | regra B: 193 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 166698 | suspeito (regra B) | regra B: 172 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 1/3 |
| 166707 | suspeito (regra B) | regra B: 182 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 167104 | suspeito (regra B) | regra B: 170 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 167280 | suspeito (regra B) | regra B: 101 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 168190 | suspeito (regra B) | regra B: 324 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 168309 | suspeito (regra B) | regra B: 104 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 168354 | suspeito (regra B) | regra B: 1024 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 168653 | suspeito (regra B) | regra B: 370 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 169594 | suspeito (regra A) | regra A: 197 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 5 s entre eventos; sinais complementares: 0/3 |
| 170219 | suspeito (regra B) | regra B: 158 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 170323 | suspeito (regra B) | regra B: 164 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 171063 | suspeito (regra B) | regra B: 103 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); submissão em lote: até 37 avaliações no mesmo segundo (34% dos eventos com 2 ou mais), primeiro dia 2016-03-12; sinais complementares: 0/3 |
| 171166 | suspeito (regra B) | regra B: 216 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 171276 | suspeito (regra A) | regra A: 175 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 2 s entre eventos; sinais complementares: 0/3 |
| 171882 | suspeito (regra B) | regra B: 157 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); submissão em lote: até 96 avaliações no mesmo segundo (96% dos eventos com 2 ou mais), primeiro dia 2019-09-19; sinais complementares: 0/3 |
| 173340 | suspeito (regra B) | regra B: 154 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 173639 | suspeito (regra B) | regra B: 238 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 173924 | suspeito (regra B) | regra B: 215 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 174046 | suspeito (regra B) | regra B: 370 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); submissão em lote: até 110 avaliações no mesmo segundo (1% dos eventos com 2 ou mais), primeiro dia 2017-10-23; sinais complementares: 0/3 |
| 175325 | suspeito (regra B) | regra B: 598 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); submissão em lote: até 148 avaliações no mesmo segundo (94% dos eventos com 2 ou mais), primeiro dia 2015-12-15; sinais complementares: 0/3 |
| 175396 | suspeito (regra B) | regra B: 125 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 175701 | suspeito (regra B) | regra B: 242 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 176445 | suspeito (regra B) | regra B: 246 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 176816 | suspeito (regra B) | regra B: 326 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 177381 | suspeito (regra B) | regra B: 172 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 177414 | suspeito (regra B) | regra B: 182 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 177641 | suspeito (regra B) | regra B: 137 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 177776 | suspeito (regra B) | regra B: 967 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 177777 | suspeito (regra A) | regra A: 193 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 5 s entre eventos; sinais complementares: 0/3 |
| 177857 | suspeito (regra B) | regra B: 416 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 178422 | suspeito (regra B) | regra B: 100 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 178532 | suspeito (regra B) | regra B: 113 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 178578 | suspeito (regra A) | regra A: 269 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 2 s entre eventos; sinais complementares: 0/3 |
| 179513 | suspeito (regra B) | regra B: 129 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 179712 | suspeito (regras A e B) | regra A: 208 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 2 s entre eventos; regra B: 640 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 1/3 |
| 180087 | suspeito (regra B) | regra B: 106 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 180443 | suspeito (regra B) | regra B: 122 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 181059 | suspeito (regra A) | regra A: 225 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 19601 s entre eventos; sinais complementares: 0/3 |
| 181185 | suspeito (regra B) | regra B: 147 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 181547 | suspeito (regra B) | regra B: 348 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 181612 | suspeito (regra B) | regra B: 339 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 182187 | suspeito (regra A) | regra A: 191 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 183009 | suspeito (regra B) | regra B: 451 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 184364 | suspeito (regra B) | regra B: 339 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 184372 | suspeito (regra B) | regra B: 129 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 184655 | suspeito (regra B) | regra B: 121 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 185207 | suspeito (regra B) | regra B: 136 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 185357 | suspeito (regra B) | regra B: 316 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 185598 | suspeito (regra B) | regra B: 125 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 186159 | suspeito (regra B) | regra B: 200 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 186842 | suspeito (regra B) | regra B: 226 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 187243 | suspeito (regra B) | regra B: 107 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 187799 | suspeito (regra B) | regra B: 189 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 188037 | suspeito (regra B) | regra B: 110 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 1/3 |
| 188121 | suspeito (regra A) | regra A: 196 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 10 s entre eventos; sinais complementares: 0/3 |
| 188126 | suspeito (regra B) | regra B: 114 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 188486 | suspeito (regra B) | regra B: 302 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 188594 | suspeito (regra B) | regra B: 236 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 189112 | suspeito (regra A) | regra A: 213 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 189645 | suspeito (regra B) | regra B: 187 eventos nas primeiras 24 h, mediana de 1 s entre eventos (>= 100 e <= 2 s); submissão em lote: até 22 avaliações no mesmo segundo (97% dos eventos com 2 ou mais), primeiro dia 2015-06-09; sinais complementares: 0/3 |
| 190857 | suspeito (regra B) | regra B: 165 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 191015 | suspeito (regra B) | regra B: 220 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 191243 | suspeito (regra B) | regra B: 146 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 191269 | suspeito (regra B) | regra B: 251 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 191696 | suspeito (regra B) | regra B: 209 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 192914 | suspeito (regra A) | regra A: 188 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 4 s entre eventos; sinais complementares: 0/3 |
| 193171 | suspeito (regra B) | regra B: 514 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 193416 | suspeito (regra B) | regra B: 168 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 193981 | suspeito (regra B) | regra B: 364 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 194729 | suspeito (regra B) | regra B: 115 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 2/3 |
| 194919 | suspeito (regra A) | regra A: 183 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 195236 | suspeito (regra B) | regra B: 163 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 195359 | suspeito (regra B) | regra B: 116 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 195448 | suspeito (regra A) | regra A: 182 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 9 s entre eventos; sinais complementares: 0/3 |
| 195588 | suspeito (regra B) | regra B: 240 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 196538 | suspeito (regra B) | regra B: 107 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 197309 | suspeito (regra B) | regra B: 432 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 197455 | suspeito (regra B) | regra B: 134 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 197853 | suspeito (regra B) | regra B: 207 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 197860 | suspeito (regra B) | regra B: 270 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 198295 | suspeito (regra B) | regra B: 208 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 199811 | suspeito (regra A) | regra A: 182 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 200106 | suspeito (regra B) | regra B: 143 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 200283 | suspeito (regra A) | regra A: 211 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 3 s entre eventos; sinais complementares: 0/3 |
| 200409 | suspeito (regra B) | regra B: 111 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 200576 | suspeito (regra B) | regra B: 174 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 200578 | suspeito (regra A) | regra A: 200 eventos em 10 min depois do registo (limiar p99,9 = 169.2), mediana de 5 s entre eventos; sinais complementares: 0/3 |
| 200843 | suspeito (regra B) | regra B: 293 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
