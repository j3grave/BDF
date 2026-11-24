# Coordenação entre contas · MovieLens small

Gerado por `scripts/04_analise.py` (sessão DuckDB em UTC, memory_limit 12GB, fonte Parquet).

## Tempos

- Total: 0.4 s (0.0 min).
- Carga dos dados: 0.0 s.
- Permutações: 20, 0.3 s no total, 0.02 s em média (a primeira inclui a verificação: 0.0 s).

## Definição

Rajada: (filme, lado, hora UTC) com >= U utilizadores distintos cuja nota está no lado e a >= D da média do filme. Lados: `0.5` (rating = 0.5), `<=1.0` (rating <= 1.0), `5.0` (rating = 5.0). U em {3, 5, 10, 20}, D em {1.5, 2}.

Linha de base: 20 permutações dos timestamps dentro de cada filme (sementes 1..20).

## Verificação da permutação (semente 1)

- Filmes: 9724; com conjunto de timestamps diferente: 0; com avaliações (utilizador, nota) diferentes: 0.
- Avaliações: 100836; com timestamp diferente do original: 91101 (90.3%); com hora diferente: 91098 (90.3%).

Exemplo (filme 61, 6 avaliações):

| movieId | userId | rating | ts_original | ts_permutado |
|---|---|---|---|---|
| 61 | 501 | 3.0 | 1996-10-10 18:59:40 | 1996-12-03 07:34:13 |
| 61 | 181 | 4.0 | 1996-10-16 13:21:55 | 1996-10-10 18:59:40 |
| 61 | 6 | 4.0 | 1996-10-17 12:30:54 | 1996-10-17 12:30:54 |
| 61 | 402 | 5.0 | 1996-12-03 07:34:13 | 2018-02-22 19:30:17 |
| 61 | 492 | 4.0 | 1997-05-18 17:27:27 | 1996-10-16 13:21:55 |
| 61 | 599 | 2.5 | 2018-02-22 19:30:17 | 1997-05-18 17:27:27 |

## Real vs linha de base

Comparações: 40. Bonferroni: limiar 0.05 / 40 = 0.00125. Menor valor-p empírico possível com 20 permutações: 1 / 21 = 0.04762. **Com este n.º de permutações nenhuma comparação pode passar o limiar corrigido**; seriam precisas pelo menos 800 permutações. O z é dado como informação complementar.

| analise | notas | min_utilizadores | min_desvio | real | media | desvio_padrao | p95 | maximo | razao_real_media | z | valor_p | sinal_bonferroni |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| principal | 0.5 | 3 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 0.5 | 3 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 0.5 | 5 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 0.5 | 5 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 0.5 | 10 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 0.5 | 10 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 0.5 | 20 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 0.5 | 20 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 5.0 | 3 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 5.0 | 3 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 5.0 | 5 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 5.0 | 5 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 5.0 | 10 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 5.0 | 10 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 5.0 | 20 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 5.0 | 20 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 0.5 e 5.0 | 3 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 0.5 e 5.0 | 3 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 0.5 e 5.0 | 5 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 0.5 e 5.0 | 5 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 0.5 e 5.0 | 10 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 0.5 e 5.0 | 10 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 0.5 e 5.0 | 20 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| principal | 0.5 e 5.0 | 20 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| sensibilidade | <=1.0 | 3 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| sensibilidade | <=1.0 | 3 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| sensibilidade | <=1.0 | 5 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| sensibilidade | <=1.0 | 5 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| sensibilidade | <=1.0 | 10 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| sensibilidade | <=1.0 | 10 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| sensibilidade | <=1.0 | 20 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| sensibilidade | <=1.0 | 20 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| sensibilidade | <=1.0 e 5.0 | 3 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| sensibilidade | <=1.0 e 5.0 | 3 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| sensibilidade | <=1.0 e 5.0 | 5 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| sensibilidade | <=1.0 e 5.0 | 5 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| sensibilidade | <=1.0 e 5.0 | 10 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| sensibilidade | <=1.0 e 5.0 | 10 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| sensibilidade | <=1.0 e 5.0 | 20 | 1.5 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |
| sensibilidade | <=1.0 e 5.0 | 20 | 2.0 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  | 1.0 | False |

## Rajadas por ano (análise principal, U >= 3, D >= 1,5)

| ano | rajadas_reais | media_permutacoes | p95_permutacoes | contas_novas |
|---|---|---|---|---|
| 1996.0 | 0.0 | 0.0 | 0.0 | 97.0 |
| 1997.0 | 0.0 | 0.0 | 0.0 | 27.0 |
| 1998.0 | 0.0 | 0.0 | 0.0 | 9.0 |
| 1999.0 | 0.0 | 0.0 | 0.0 | 26.0 |
| 2000.0 | 0.0 | 0.0 | 0.0 | 48.0 |
| 2001.0 | 0.0 | 0.0 | 0.0 | 20.0 |
| 2002.0 | 0.0 | 0.0 | 0.0 | 14.0 |
| 2003.0 | 0.0 | 0.0 | 0.0 | 20.0 |
| 2004.0 | 0.0 | 0.0 | 0.0 | 11.0 |
| 2005.0 | 0.0 | 0.0 | 0.0 | 24.0 |
| 2006.0 | 0.0 | 0.0 | 0.0 | 23.0 |
| 2007.0 | 0.0 | 0.0 | 0.0 | 22.0 |
| 2008.0 | 0.0 | 0.0 | 0.0 | 22.0 |
| 2009.0 | 0.0 | 0.0 | 0.0 | 21.0 |
| 2010.0 | 0.0 | 0.0 | 0.0 | 15.0 |
| 2011.0 | 0.0 | 0.0 | 0.0 | 22.0 |
| 2012.0 | 0.0 | 0.0 | 0.0 | 25.0 |
| 2013.0 | 0.0 | 0.0 | 0.0 | 13.0 |
| 2014.0 | 0.0 | 0.0 | 0.0 | 8.0 |
| 2015.0 | 0.0 | 0.0 | 0.0 | 47.0 |
| 2016.0 | 0.0 | 0.0 | 0.0 | 32.0 |
| 2017.0 | 0.0 | 0.0 | 0.0 | 35.0 |
| 2018.0 | 0.0 | 0.0 | 0.0 | 29.0 |

## As 10 rajadas reais mais fortes (análise principal)

| rajada | title | lado | inicio_hora_utc | u_15 | avaliacoes_filme_hora | pct_da_hora | desvio_max | dias_desde_estreia_dataset | antiguidade_mediana_dias | pct_no_registo | avaliacoes_conta_mediana | pct_voltaram_24h | jaccard_medio | jaccard_max | contas_suspeitas |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Jaccard de referência entre pares de contas quaisquer (1000 contas ao acaso): média 0.045, p95 0.141.
