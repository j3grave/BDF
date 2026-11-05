# Coordenação entre contas · MovieLens 1m

Gerado por `scripts/06_coordenacao.py` em 1.5 s (sessão DuckDB em UTC). **A validar com o Luís.**

## Definição

Rajada: (filme, nota extrema, hora UTC) com >= U utilizadores distintos e |nota - média do filme| >= D. Notas extremas: 1 e 5. U em {3, 5, 10}, D em {1.5, 2}.

Linha de base: 20 permutações dos timestamps dentro de cada filme (sementes 1..20). Valor-p empírico = (1 + n.º de permutações >= real) / (1 + R); com R = 20 o menor valor possível é 0.048.

## Real vs linha de base

| nota | min_utilizadores | min_desvio | real | media | p95 | maximo | razao_real_media | valor_p |
|---|---|---|---|---|---|---|---|---|
| 1.0 | 3 | 1.5 | 31 | 27.25 | 37.3 | 43 | 1.14 | 0.238 |
| 1.0 | 3 | 2.0 | 17 | 14.15 | 19.25 | 24 | 1.2 | 0.143 |
| 1.0 | 5 | 1.5 | 2 | 0.6 | 2.0 | 2 | 3.33 | 0.143 |
| 1.0 | 5 | 2.0 | 2 | 0.35 | 1.05 | 2 | 5.71 | 0.095 |
| 1.0 | 10 | 1.5 | 0 | 0.0 | 0.0 | 0 |  | 1.0 |
| 1.0 | 10 | 2.0 | 0 | 0.0 | 0.0 | 0 |  | 1.0 |
| 5.0 | 3 | 1.5 | 56 | 45.8 | 53.25 | 58 | 1.22 | 0.095 |
| 5.0 | 3 | 2.0 | 3 | 0.6 | 1.05 | 2 | 5.0 | 0.048 |
| 5.0 | 5 | 1.5 | 1 | 1.4 | 3.0 | 3 | 0.71 | 0.81 |
| 5.0 | 5 | 2.0 | 0 | 0.0 | 0.0 | 0 |  | 1.0 |
| 5.0 | 10 | 1.5 | 0 | 0.0 | 0.0 | 0 |  | 1.0 |
| 5.0 | 10 | 2.0 | 0 | 0.0 | 0.0 | 0 |  | 1.0 |
| ambas | 3 | 1.5 | 87 | 73.05 | 84.4 | 92 | 1.19 | 0.095 |
| ambas | 3 | 2.0 | 20 | 14.75 | 20.25 | 25 | 1.36 | 0.143 |
| ambas | 5 | 1.5 | 3 | 2.0 | 3.05 | 4 | 1.5 | 0.429 |
| ambas | 5 | 2.0 | 2 | 0.35 | 1.05 | 2 | 5.71 | 0.095 |
| ambas | 10 | 1.5 | 0 | 0.0 | 0.0 | 0 |  | 1.0 |
| ambas | 10 | 2.0 | 0 | 0.0 | 0.0 | 0 |  | 1.0 |

## As 10 rajadas reais mais fortes

| rajada | title | nota | inicio_hora_utc | utilizadores | avaliacoes_filme_hora | pct_da_hora | desvio | dias_desde_estreia_dataset | antiguidade_mediana_dias | pct_no_registo | avaliacoes_conta_mediana | pct_voltaram_24h | jaccard_medio | jaccard_max | suspeitos_bloco5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Rocky Horror Picture Show, The (1975) | 5.0 | 2000-11-20 08:00 | 7 | 8 | 87.5 | 1.709 | 208.11 | 0.01 | 100.0 | 565.0 | 42.9 | 0.13 | 0.246 | 0 |
| 2 | Lost World: Jurassic Park, The (1997) | 1.0 | 2000-11-21 01:00 | 5 | 15 | 33.3 | 2.037 | 209.0 | 0.01 | 100.0 | 404.0 | 80.0 | 0.196 | 0.283 | 0 |
| 3 | Blair Witch Project, The (1999) | 1.0 | 2000-11-20 06:00 | 5 | 11 | 45.5 | 2.032 | 208.22 | 0.05 | 100.0 | 317.0 | 40.0 | 0.114 | 0.208 | 0 |
| 4 | Rocky Horror Picture Show, The (1975) | 1.0 | 2000-11-20 05:00 | 4 | 12 | 33.3 | 2.291 | 207.99 | 0.01 | 100.0 | 218.0 | 75.0 | 0.106 | 0.22 | 0 |
| 5 | From Dusk Till Dawn (1996) | 1.0 | 2000-11-20 08:00 | 4 | 14 | 28.6 | 2.156 | 208.06 | 0.075 | 100.0 | 389.0 | 50.0 | 0.134 | 0.222 | 0 |
| 6 | From Dusk Till Dawn (1996) | 5.0 | 2000-11-20 08:00 | 4 | 14 | 28.6 | 1.844 | 208.06 | 0.025 | 100.0 | 481.5 | 50.0 | 0.162 | 0.325 | 0 |
| 7 | Running Man, The (1987) | 5.0 | 2000-11-20 07:00 | 4 | 7 | 57.1 | 1.801 | 181.23 | 0.03 | 100.0 | 499.0 | 50.0 | 0.235 | 0.384 | 0 |
| 8 | Little Shop of Horrors (1986) | 5.0 | 2000-11-20 09:00 | 4 | 7 | 57.1 | 1.668 | 208.39 | 0.06 | 100.0 | 395.5 | 25.0 | 0.086 | 0.143 | 0 |
| 9 | Godfather: Part III, The (1990) | 5.0 | 2000-11-21 01:00 | 4 | 4 | 100.0 | 1.655 | 208.2 | 0.6 | 75.0 | 231.5 | 25.0 | 0.081 | 0.181 | 0 |
| 10 | Hairspray (1988) | 5.0 | 2000-11-20 09:00 | 4 | 7 | 57.1 | 1.649 | 208.31 | 0.05 | 100.0 | 515.5 | 50.0 | 0.105 | 0.231 | 0 |

Jaccard de referência entre pares de contas quaisquer (1000 contas ao acaso): média 0.056, p95 0.156.
