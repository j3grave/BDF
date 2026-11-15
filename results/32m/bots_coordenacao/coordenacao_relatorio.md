# Coordenação entre contas · MovieLens 32m

Gerado por `scripts/06_coordenacao.py` (sessão DuckDB em UTC, memory_limit 12GB, fonte Parquet). **A validar com o Luís.**

## Tempos

- Total: 596.8 s (9.9 min).
- Carga dos dados: 0.2 s.
- Permutações: 200, 595.4 s no total, 2.98 s em média (a primeira inclui a verificação: 2.3 s).

## Definição

Rajada: (filme, lado, hora UTC) com >= U utilizadores distintos cuja nota está no lado e a >= D da média do filme. Lados: `0.5` (rating = 0.5), `<=1.0` (rating <= 1.0), `5.0` (rating = 5.0). U em {3, 5, 10, 20}, D em {1.5, 2}.

Linha de base: 200 permutações dos timestamps dentro de cada filme (sementes 1..200).

## Verificação da permutação (semente 1)

- Filmes: 84432; com conjunto de timestamps diferente: 0; com avaliações (utilizador, nota) diferentes: 0.
- Avaliações: 32000204; com timestamp diferente do original: 31916118 (99.7%); com hora diferente: 31914823 (99.7%).

Exemplo (filme 604, 6 avaliações):

| movieId | userId | rating | ts_original | ts_permutado |
|---|---|---|---|---|
| 604 | 84603 | 1.0 | 1997-02-03 20:41:19 | 2002-04-07 14:01:01 |
| 604 | 92958 | 1.0 | 1997-05-06 14:53:11 | 1999-12-01 16:31:47 |
| 604 | 186566 | 1.0 | 1999-12-01 16:31:47 | 1997-05-06 14:53:11 |
| 604 | 1474 | 4.0 | 2000-01-31 23:33:34 | 2004-07-30 07:53:32 |
| 604 | 200493 | 4.0 | 2002-04-07 14:01:01 | 2000-01-31 23:33:34 |
| 604 | 27841 | 0.5 | 2004-07-30 07:53:32 | 1997-02-03 20:41:19 |

## Real vs linha de base

Comparações: 40. Bonferroni: limiar 0.05 / 40 = 0.00125. Menor valor-p empírico possível com 200 permutações: 1 / 201 = 0.00498. **Com este n.º de permutações nenhuma comparação pode passar o limiar corrigido**; seriam precisas pelo menos 800 permutações. O z é dado como informação complementar.

| analise | notas | min_utilizadores | min_desvio | real | media | desvio_padrao | p95 | maximo | razao_real_media | z | valor_p | sinal_bonferroni |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| principal | 0.5 | 3 | 1.5 | 73 | 27.07 | 5.51 | 36.05 | 42 | 2.7 | 8.34 | 0.005 | False |
| principal | 0.5 | 3 | 2.0 | 71 | 23.76 | 5.21 | 33.0 | 39 | 2.99 | 9.07 | 0.005 | False |
| principal | 0.5 | 5 | 1.5 | 15 | 0.68 | 0.84 | 2.0 | 4 | 22.06 | 17.1 | 0.005 | False |
| principal | 0.5 | 5 | 2.0 | 15 | 0.66 | 0.82 | 2.0 | 4 | 22.9 | 17.53 | 0.005 | False |
| principal | 0.5 | 10 | 1.5 | 1 | 0.0 | 0.0 | 0.0 | 0 |  |  | 0.005 | False |
| principal | 0.5 | 10 | 2.0 | 1 | 0.0 | 0.0 | 0.0 | 0 |  |  | 0.005 | False |
| principal | 0.5 | 20 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 0.5 | 20 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 5.0 | 3 | 1.5 | 2127 | 904.0 | 26.16 | 947.1 | 980 | 2.35 | 46.76 | 0.005 | False |
| principal | 5.0 | 3 | 2.0 | 97 | 42.42 | 5.95 | 52.0 | 61 | 2.29 | 9.17 | 0.005 | False |
| principal | 5.0 | 5 | 1.5 | 118 | 40.2 | 5.34 | 49.0 | 53 | 2.94 | 14.58 | 0.005 | False |
| principal | 5.0 | 5 | 2.0 | 4 | 2.22 | 1.19 | 4.0 | 5 | 1.81 | 1.51 | 0.1294 | False |
| principal | 5.0 | 10 | 1.5 | 2 | 1.03 | 1.01 | 3.0 | 4 | 1.94 | 0.96 | 0.2935 | False |
| principal | 5.0 | 10 | 2.0 | 0 | 0.0 | 0.07 | 0.0 | 1 | 0.0 | -0.07 | 1.0 | False |
| principal | 5.0 | 20 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 5.0 | 20 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 0.5 e 5.0 | 3 | 1.5 | 2200 | 931.06 | 26.78 | 977.05 | 1007 | 2.36 | 47.38 | 0.005 | False |
| principal | 0.5 e 5.0 | 3 | 2.0 | 168 | 66.18 | 7.58 | 79.0 | 91 | 2.54 | 13.43 | 0.005 | False |
| principal | 0.5 e 5.0 | 5 | 1.5 | 133 | 40.88 | 5.42 | 49.0 | 53 | 3.25 | 16.99 | 0.005 | False |
| principal | 0.5 e 5.0 | 5 | 2.0 | 19 | 2.87 | 1.38 | 5.0 | 7 | 6.62 | 11.69 | 0.005 | False |
| principal | 0.5 e 5.0 | 10 | 1.5 | 3 | 1.03 | 1.01 | 3.0 | 4 | 2.91 | 1.96 | 0.0896 | False |
| principal | 0.5 e 5.0 | 10 | 2.0 | 1 | 0.0 | 0.07 | 0.0 | 1 | 200.0 | 14.07 | 0.01 | False |
| principal | 0.5 e 5.0 | 20 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 0.5 e 5.0 | 20 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| sensibilidade | <=1.0 | 3 | 1.5 | 841 | 593.7 | 23.32 | 635.05 | 665 | 1.42 | 10.61 | 0.005 | False |
| sensibilidade | <=1.0 | 3 | 2.0 | 487 | 281.59 | 15.89 | 306.0 | 322 | 1.73 | 12.93 | 0.005 | False |
| sensibilidade | <=1.0 | 5 | 1.5 | 73 | 31.64 | 4.61 | 39.05 | 46 | 2.31 | 8.98 | 0.005 | False |
| sensibilidade | <=1.0 | 5 | 2.0 | 46 | 14.2 | 2.89 | 19.0 | 22 | 3.24 | 11.01 | 0.005 | False |
| sensibilidade | <=1.0 | 10 | 1.5 | 9 | 1.94 | 1.26 | 4.0 | 6 | 4.65 | 5.59 | 0.005 | False |
| sensibilidade | <=1.0 | 10 | 2.0 | 4 | 0.86 | 0.82 | 2.0 | 4 | 4.62 | 3.83 | 0.01 | False |
| sensibilidade | <=1.0 | 20 | 1.5 | 1 | 0.0 | 0.0 | 0.0 | 0 |  |  | 0.005 | False |
| sensibilidade | <=1.0 | 20 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| sensibilidade | <=1.0 e 5.0 | 3 | 1.5 | 2968 | 1497.7 | 35.8 | 1556.1 | 1604 | 1.98 | 41.07 | 0.005 | False |
| sensibilidade | <=1.0 e 5.0 | 3 | 2.0 | 584 | 324.02 | 15.98 | 347.0 | 360 | 1.8 | 16.27 | 0.005 | False |
| sensibilidade | <=1.0 e 5.0 | 5 | 1.5 | 191 | 71.83 | 6.93 | 83.0 | 92 | 2.66 | 17.19 | 0.005 | False |
| sensibilidade | <=1.0 e 5.0 | 5 | 2.0 | 50 | 16.41 | 2.99 | 22.0 | 23 | 3.05 | 11.23 | 0.005 | False |
| sensibilidade | <=1.0 e 5.0 | 10 | 1.5 | 11 | 2.96 | 1.65 | 6.0 | 7 | 3.71 | 4.86 | 0.005 | False |
| sensibilidade | <=1.0 e 5.0 | 10 | 2.0 | 4 | 0.87 | 0.82 | 2.0 | 4 | 4.6 | 3.83 | 0.01 | False |
| sensibilidade | <=1.0 e 5.0 | 20 | 1.5 | 1 | 0.0 | 0.0 | 0.0 | 0 |  |  | 0.005 | False |
| sensibilidade | <=1.0 e 5.0 | 20 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |

## Rajadas por ano (análise principal, U >= 3, D >= 1,5)

| ano | rajadas_reais | media_permutacoes | p95_permutacoes | contas_novas |
|---|---|---|---|---|
| 1995.0 | 0.0 | 0.0 | 0.0 | 2.0 |
| 1996.0 | 1253.0 | 527.36 | 562.05 | 25304.0 |
| 1997.0 | 139.0 | 39.26 | 50.0 | 9092.0 |
| 1998.0 | 35.0 | 7.12 | 11.0 | 2574.0 |
| 1999.0 | 315.0 | 85.84 | 99.05 | 8813.0 |
| 2000.0 | 238.0 | 65.18 | 79.0 | 11843.0 |
| 2001.0 | 25.0 | 3.36 | 7.0 | 6871.0 |
| 2002.0 | 11.0 | 0.66 | 2.0 | 4487.0 |
| 2003.0 | 11.0 | 2.24 | 5.0 | 5092.0 |
| 2004.0 | 3.0 | 2.88 | 5.05 | 4955.0 |
| 2005.0 | 92.0 | 146.54 | 163.0 | 8649.0 |
| 2006.0 | 1.0 | 1.94 | 5.0 | 5931.0 |
| 2007.0 | 0.0 | 3.18 | 6.0 | 5197.0 |
| 2008.0 | 16.0 | 23.94 | 32.0 | 6582.0 |
| 2009.0 | 3.0 | 0.66 | 2.0 | 5415.0 |
| 2010.0 | 0.0 | 0.88 | 2.05 | 5447.0 |
| 2011.0 | 1.0 | 0.23 | 1.0 | 4998.0 |
| 2012.0 | 11.0 | 4.2 | 8.0 | 4606.0 |
| 2013.0 | 4.0 | 0.92 | 3.0 | 4238.0 |
| 2014.0 | 4.0 | 0.49 | 2.0 | 3760.0 |
| 2015.0 | 18.0 | 5.12 | 9.0 | 12157.0 |
| 2016.0 | 4.0 | 2.38 | 5.0 | 10491.0 |
| 2017.0 | 6.0 | 1.52 | 4.0 | 9163.0 |
| 2018.0 | 0.0 | 2.7 | 6.0 | 6902.0 |
| 2019.0 | 3.0 | 0.92 | 3.0 | 6850.0 |
| 2020.0 | 1.0 | 0.77 | 2.0 | 8531.0 |
| 2021.0 | 5.0 | 0.36 | 2.0 | 5668.0 |
| 2022.0 | 1.0 | 0.16 | 1.0 | 3911.0 |
| 2023.0 | 0.0 | 0.22 | 1.0 | 3419.0 |

## As 10 rajadas reais mais fortes (análise principal)

| rajada | title | lado | inicio_hora_utc | u_15 | avaliacoes_filme_hora | pct_da_hora | desvio_max | dias_desde_estreia_dataset | antiguidade_mediana_dias | pct_no_registo | avaliacoes_conta_mediana | pct_voltaram_24h | jaccard_medio | jaccard_max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Honey, I Shrunk the Kids (1989) | 0.5 | 2005-03-22 06:00 | 14 | 63 | 22.2 | 2.236 | 2442.43 | 0.0 | 100.0 | 77.0 | 42.9 | 0.069 | 0.253 |
| 2 | Mrs. Doubtfire (1993) | 5.0 | 1996-11-26 05:00 | 11 | 25 | 44.0 | 1.608 | 270.21 | 0.0 | 100.0 | 42.0 | 27.3 | 0.305 | 0.593 |
| 3 | Independence Day (a.k.a. ID4) (1996) | 5.0 | 1997-05-11 11:00 | 10 | 25 | 40.0 | 1.619 | 318.64 | 0.0 | 100.0 | 37.0 | 10.0 | 0.306 | 0.675 |
| 4 | Blair Witch Project, The (1999) | 5.0 | 1999-12-11 16:00 | 9 | 23 | 39.1 | 2.084 | 153.1 | 0.01 | 100.0 | 126.0 | 66.7 | 0.091 | 0.223 |
| 5 | Star Wars: Episode I - The Phantom Menace (1999) | 5.0 | 1999-12-11 08:00 | 9 | 24 | 37.5 | 1.937 | 214.71 | 0.01 | 100.0 | 166.0 | 55.6 | 0.091 | 0.229 |
| 6 | Body Snatchers (1993) | 5.0 | 1998-05-22 12:00 | 9 | 103 | 8.7 | 1.891 | 812.5 | 353.68 | 0.0 | 121.0 | 0.0 | 0.164 | 0.373 |
| 7 | Money Talks (1997) | 5.0 | 1998-05-22 14:00 | 8 | 74 | 10.8 | 2.066 | 248.94 | 157.44 | 0.0 | 38.0 | 25.0 | 0.114 | 0.301 |
| 8 | Mrs. Doubtfire (1993) | 5.0 | 1996-11-26 06:00 | 8 | 19 | 42.1 | 1.608 | 270.25 | 0.0 | 100.0 | 60.0 | 12.5 | 0.264 | 0.63 |
| 9 | Pretty Woman (1990) | 5.0 | 1996-11-26 06:00 | 8 | 21 | 38.1 | 1.565 | 270.25 | 0.0 | 100.0 | 46.5 | 12.5 | 0.204 | 0.525 |
| 10 | True Lies (1994) | 5.0 | 1996-11-26 05:00 | 8 | 23 | 34.8 | 1.504 | 270.21 | 0.0 | 100.0 | 46.5 | 12.5 | 0.35 | 0.606 |

Jaccard de referência entre pares de contas quaisquer (1000 contas ao acaso): média 0.043, p95 0.130.
