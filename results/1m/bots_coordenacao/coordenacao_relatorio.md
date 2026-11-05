# Coordenação entre contas · MovieLens 1m

Gerado por `scripts/06_coordenacao.py` (sessão DuckDB em UTC, memory_limit 12GB, fonte Parquet). **A validar com o Luís.**

## Tempos

- Total: 1.6 s (0.0 min).
- Carga dos dados: 0.0 s.
- Permutações: 20, 1.4 s no total, 0.07 s em média (a primeira inclui a verificação: 0.1 s).

## Definição

Rajada: (filme, lado, hora UTC) com >= U utilizadores distintos cuja nota está no lado e a >= D da média do filme. Lados: `1` (rating = 1), `5` (rating = 5). U em {3, 5, 10, 20}, D em {1.5, 2}.

Linha de base: 20 permutações dos timestamps dentro de cada filme (sementes 1..20).

## Verificação da permutação (semente 1)

- Filmes: 3706; com conjunto de timestamps diferente: 0; com avaliações (utilizador, nota) diferentes: 0.
- Avaliações: 1000209; com timestamp diferente do original: 996539 (99.6%); com hora diferente: 995879 (99.6%).

Exemplo (filme 90, 6 avaliações):

| movieId | userId | rating | ts_original | ts_permutado |
|---|---|---|---|---|
| 90 | 5553 | 4.0 | 2000-05-27 19:31:45 | 2000-08-03 20:46:51 |
| 90 | 4168 | 5.0 | 2000-08-03 20:46:51 | 2001-05-10 01:41:49 |
| 90 | 3585 | 4.0 | 2000-08-19 14:43:26 | 2000-08-19 14:43:26 |
| 90 | 3618 | 3.0 | 2000-08-24 11:04:49 | 2000-05-27 19:31:45 |
| 90 | 1069 | 2.0 | 2000-11-23 01:40:49 | 2000-11-23 01:40:49 |
| 90 | 2547 | 4.0 | 2001-05-10 01:41:49 | 2000-08-24 11:04:49 |

## Real vs linha de base

Comparações: 24. Bonferroni: limiar 0.05 / 24 = 0.00208. Menor valor-p empírico possível com 20 permutações: 1 / 21 = 0.04762. **Com este n.º de permutações nenhuma comparação pode passar o limiar corrigido**; seriam precisas pelo menos 480 permutações. O z é dado como informação complementar.

| analise | notas | min_utilizadores | min_desvio | real | media | desvio_padrao | p95 | maximo | razao_real_media | z | valor_p | sinal_bonferroni |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| principal | 1 | 3 | 1.5 | 31 | 27.25 | 5.82 | 37.3 | 43 | 1.14 | 0.64 | 0.2381 | False |
| principal | 1 | 3 | 2.0 | 17 | 14.15 | 3.67 | 19.25 | 24 | 1.2 | 0.78 | 0.1429 | False |
| principal | 1 | 5 | 1.5 | 2 | 0.6 | 0.68 | 2.0 | 2 | 3.33 | 2.06 | 0.1429 | False |
| principal | 1 | 5 | 2.0 | 2 | 0.35 | 0.59 | 1.05 | 2 | 5.71 | 2.81 | 0.0952 | False |
| principal | 1 | 10 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 1 | 10 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 1 | 20 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 1 | 20 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 5 | 3 | 1.5 | 56 | 45.8 | 5.96 | 53.25 | 58 | 1.22 | 1.71 | 0.0952 | False |
| principal | 5 | 3 | 2.0 | 3 | 0.6 | 0.6 | 1.05 | 2 | 5.0 | 4.01 | 0.0476 | False |
| principal | 5 | 5 | 1.5 | 1 | 1.4 | 1.05 | 3.0 | 3 | 0.71 | -0.38 | 0.8095 | False |
| principal | 5 | 5 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 5 | 10 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 5 | 10 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 5 | 20 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 5 | 20 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 1 e 5 | 3 | 1.5 | 87 | 73.05 | 9.6 | 84.4 | 92 | 1.19 | 1.45 | 0.0952 | False |
| principal | 1 e 5 | 3 | 2.0 | 20 | 14.75 | 3.84 | 20.25 | 25 | 1.36 | 1.37 | 0.1429 | False |
| principal | 1 e 5 | 5 | 1.5 | 3 | 2.0 | 1.12 | 3.05 | 4 | 1.5 | 0.89 | 0.4286 | False |
| principal | 1 e 5 | 5 | 2.0 | 2 | 0.35 | 0.59 | 1.05 | 2 | 5.71 | 2.81 | 0.0952 | False |
| principal | 1 e 5 | 10 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 1 e 5 | 10 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 1 e 5 | 20 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 1 e 5 | 20 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |

## Rajadas por ano (análise principal, U >= 3, D >= 1,5)

| ano | rajadas_reais | media_permutacoes | p95_permutacoes | contas_novas |
|---|---|---|---|---|
| 2000.0 | 87.0 | 73.05 | 84.4 | 6034.0 |
| 2001.0 | 0.0 | 0.0 | 0.0 | 4.0 |
| 2002.0 | 0.0 | 0.0 | 0.0 | 2.0 |

## As 10 rajadas reais mais fortes (análise principal)

| rajada | title | lado | inicio_hora_utc | u_15 | avaliacoes_filme_hora | pct_da_hora | desvio_max | dias_desde_estreia_dataset | antiguidade_mediana_dias | pct_no_registo | avaliacoes_conta_mediana | pct_voltaram_24h | jaccard_medio | jaccard_max | suspeitos_bloco5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Rocky Horror Picture Show, The (1975) | 5 | 2000-11-20 08:00 | 7 | 8 | 87.5 | 1.709 | 208.11 | 0.01 | 100.0 | 565.0 | 42.9 | 0.13 | 0.246 | 0 |
| 2 | Lost World: Jurassic Park, The (1997) | 1 | 2000-11-21 01:00 | 5 | 15 | 33.3 | 2.037 | 209.0 | 0.01 | 100.0 | 404.0 | 80.0 | 0.196 | 0.283 | 0 |
| 3 | Blair Witch Project, The (1999) | 1 | 2000-11-20 06:00 | 5 | 11 | 45.5 | 2.032 | 208.22 | 0.05 | 100.0 | 317.0 | 40.0 | 0.114 | 0.208 | 0 |
| 4 | Rocky Horror Picture Show, The (1975) | 1 | 2000-11-20 05:00 | 4 | 12 | 33.3 | 2.291 | 207.99 | 0.01 | 100.0 | 218.0 | 75.0 | 0.106 | 0.22 | 0 |
| 5 | From Dusk Till Dawn (1996) | 1 | 2000-11-20 08:00 | 4 | 14 | 28.6 | 2.156 | 208.06 | 0.075 | 100.0 | 389.0 | 50.0 | 0.134 | 0.222 | 0 |
| 6 | From Dusk Till Dawn (1996) | 5 | 2000-11-20 08:00 | 4 | 14 | 28.6 | 1.844 | 208.06 | 0.025 | 100.0 | 481.5 | 50.0 | 0.162 | 0.325 | 0 |
| 7 | Running Man, The (1987) | 5 | 2000-11-20 07:00 | 4 | 7 | 57.1 | 1.801 | 181.23 | 0.03 | 100.0 | 499.0 | 50.0 | 0.235 | 0.384 | 0 |
| 8 | Little Shop of Horrors (1986) | 5 | 2000-11-20 09:00 | 4 | 7 | 57.1 | 1.668 | 208.39 | 0.06 | 100.0 | 395.5 | 25.0 | 0.086 | 0.143 | 0 |
| 9 | Godfather: Part III, The (1990) | 5 | 2000-11-21 01:00 | 4 | 4 | 100.0 | 1.655 | 208.2 | 0.6 | 75.0 | 231.5 | 25.0 | 0.081 | 0.181 | 0 |
| 10 | Hairspray (1988) | 5 | 2000-11-20 09:00 | 4 | 7 | 57.1 | 1.649 | 208.31 | 0.05 | 100.0 | 515.5 | 50.0 | 0.105 | 0.231 | 0 |

Jaccard de referência entre pares de contas quaisquer (1000 contas ao acaso): média 0.056, p95 0.156.
