# Validação das queries do colega e proposta de integração

Secções 0–12 e anexos: Fase 1 (só leitura e análise), de 4 de novembro de 2026. Nessa fase nenhum
ficheiro existente foi alterado.
Secção 13: Fase 2 (implementação), de 5 de novembro de 2026, no branch `integracao-queries-luis`. Tem
a tabela final por query (13.7) e os pendentes (13.9).

## Resumo

- **O que chegou:** o colega (Luis Pousada, `lpousadajr`) adicionou um único commit ao `origin/main`,
  o `e51d050` ("Notebook inicial com novas questões e análises"). Tem dois notebooks e nenhum ficheiro
  `.sql` ou script.
  - As queries novas estão dentro dos notebooks. São **22 queries SQL em dialeto DuckDB** (células
    108, 109 e 112), mais versões Polars das mesmas análises.
  - Os dois notebooks (`…_v1_3.ipynb` e `…_v2.ipynb`) têm o mesmo código. Diferem apenas nas flags da
    célula de configuração: o `v2` liga os 5 datasets, sem limites.
- **Execução:** as 22 queries correm no DuckDB sobre o small, em CSV e em Parquet.
  - Os números batem com o `04_eda.py` (100 836 avaliações, 610 utilizadores, 9 724 filmes avaliados,
    média 3,502).
  - Batem também com as queries 02, 04 e 05 de `sql/`. A query 03 só difere no arredondamento de 3
    utilizadores.
- **Problemas a corrigir antes de integrar:**
  1. **Fuso horário.** Seis queries usam `to_timestamp`, que depende do fuso da sessão. Duas delas
     (`mensal` e `grupos_atividade`) dão resultados diferentes fora de UTC.
  2. **Deteção de bots.** A regra de "atividade concentrada" sinaliza sobretudo o registo de
     utilizadores novos. Sinaliza 34% dos utilizadores no small e 38% no 32M; ignorando as primeiras
     24 h, o small desce para 3,4%.
  3. **`evolucao_filmes`.** Usa um último ano incompleto como "período recente".
  4. **`grupos_atividade`.** Tem faixas que ficam vazias, porque o dataset só inclui utilizadores com
     pelo menos 20 avaliações.
  5. **`dias_filme`.** Devolve 14,7 milhões de linhas no 32M.
- **Athena:** nenhuma query corre tal como está, exceto, provavelmente, `distribuicao` e `ponderado`.
  As traduções são mecânicas e estão na secção 7. As versões propostas foram emuladas no DuckDB e
  reproduzem os resultados originais. Não foram executadas no Athena, porque ainda não há conta.
- **Sobreposições:** 5 queries duplicam o que já existe em `sql/01–05` ou no `04_eda.py`.
  - Proposta: integrar 15 queries num novo `scripts/05_analises.py`, com as queries em `sql/analise/`
    para não alterar o benchmark da fase 1.
  - A deteção de bots vai para `sql/10_flag_bots.sql`, que é o esqueleto já atribuído ao Luís.

**Fase 2 (secção 13):**
- **Estado das 22 queries:** 4 integradas, 10 corrigidas, 7 fora e 1 substituída (a deteção de
  bots).
- **Ficheiros:** `sql/analise/` e `sql/athena/analise/`, corridos pelo novo
  `scripts/05_analises.py`.
- **Validação:**
  - feita no small e no 1M;
  - totais iguais aos do `04_eda.py`;
  - resultados iguais em três fusos horários;
  - versões Athena emuladas iguais às versões DuckDB.
- **Deteção de bots** (a validar com o Luís):
  - suspeitos: 0,33% no small e 0,10% no 1M, contra 34,4% e 46,8% com a regra original;
  - submissões em lote reportadas à parte.
- **Coordenação entre contas** (bloco 6, 1M e 32M):
  - 1M: sem sinal acima da linha de base; as rajadas mais fortes são contas novas no pico de
    registos de 20–21/11/2000;
  - 32M: mais rajadas do que na linha de base, mas o excesso está todo antes da escala de meias
    estrelas (fevereiro de 2003) e explica-se pela mudança de escala, não por coordenação;
    nenhuma comparação passa Bonferroni (com 200 permutações não é possível).
- **Ainda não feito:** no 32M só correu o bloco 6; nada no Athena.

## 0. O que foi analisado e como

| Item | Valor |
|---|---|
| Commit | `e51d050` em `origin/main`, autor `lpousadajr`, 2026-11-04 19:34 UTC |
| Ficheiros | `Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb` (21 366 linhas) e `…_v2.ipynb` (45 028 linhas, com saídas) |
| Base do commit | `34e4e75` (antes da fase 1). O `origin/main` não tem a fase 1 nem a fase 2. |
| Diferença v1_3 → v2 | Só a célula 4: todos os datasets ligados, sem limites de download nem de linhas, `MEMORIA_DUCKDB="8GB"` e `CRIAR_ZIP=True` |
| Execução registada no v2 | 63/63 células executadas pelo colega com small, 100k, 1m, 10m e 32m |

Método:

- **Extração:** as queries foram extraídas do notebook com `ast` (só strings SQL). Nenhuma célula do
  notebook foi executada.
- **Execução:**
  - Foi feita com DuckDB 1.5.6 sobre `data/small/` (fase 1), com 3 corridas e a mediana do tempo.
  - **CSV:** `read_csv_auto`, como no `04_eda.py --fonte csv`. **Parquet:**
    `data/small/parquet/*.parquet`.
  - A sessão ficou em `TimeZone='UTC'`, como na função `ligar()` do notebook.
- **Athena:** análise estática, mais uma emulação no DuckDB (macros para `from_unixtime`,
  `date_format` e `sequence`). A emulação valida a lógica e os resultados, **não** a sintaxe do Trino.
- **32M:** não corri nada sobre o 32M. Os números do 32M citados aqui vêm das saídas gravadas no
  notebook do colega e do manifesto `reports/cloud_manifest_32m.md`.

## 1. Estrutura do repositório e confirmação da descrição

| Descrição dada | O que existe (branch `fase2-cloud-prep`) |
|---|---|
| Scripts numerados em `scripts/` | Correto: `01_ingest.py`, `02_to_parquet.py`, `03_benchmark.py` e `04_eda.py`, orquestrados por `run_pipeline.py` (`--steps ingest parquet benchmark eda`). Os scripts da fase 2 (`prepare_cloud.py`, `athena_*.py`) não têm número. |
| Correm com `--dataset {small,1m,32m}` | Correto em todos (`common.parse_args`). |
| … e `--fonte {csv,parquet}` | **Só o `04_eda.py`** (`--fonte auto/parquet/csv`). O `03_benchmark.py` lê sempre os dois Parquet (sem partição e por ano); 01 e 02 não leem Parquet. |
| Ligação ao DuckDB | Não há uma função comum. Cada script faz `duckdb.connect()`; o `04_eda.py` tem `ligar(base, dataset, fonte)`, que cria as views `ratings`, `movies`, `tags` e `links`. As queries de `sql/` usam os marcadores `${ratings}`/`${movies}`, substituídos pelo `03_benchmark.py`, e `${ratings}` já inclui a coluna `year` (UTC, `epoch_ms`). |
| Agregações no DuckDB, só agregados para Python | Correto no `04_eda.py` (está no cabeçalho e no código). |
| Saídas em `results/<dataset>/...` | Parcialmente: o EDA escreve em `results/<dataset>/eda/`. `sizes.csv`, `benchmarks.csv`, `pipeline_runs.csv` e `cloud_benchmarks.csv` são **globais** em `results/`, com uma coluna `dataset`. Os manifestos estão em `reports/`. |
| Cloud: S3 → **Glue Crawler** → Athena | **Não está no repositório.** O que existe é DDL escrito à mão (`sql/athena/ddl/`, executado por `scripts/athena_setup.py`), sem crawler, e ainda não foi corrido na AWS. |
| Tabelas `smallmoviesparquet`, `smallratingsparquet` | **Não existem no repositório.** O DDL cria a base `movielens_<dataset>` com as tabelas `ratings`, `ratings_part`, `ratings_csv`, `movies`, `tags` e `links`. As queries Athena estão em `sql/athena/queries/`, com `${ratings}`/`${movies}`. |
| Colunas em minúsculas no Athena | Correto (`userid`, `movieid`; `timestamp` é palavra reservada e vai entre aspas). |

**A confirmar:** se o crawler e as tabelas `small…parquet` existem na conta do Learner Lab, foram
criados fora do repositório. As propostas da secção 10 usam `${ratings}`/`${movies}`, por isso servem
para os dois esquemas de nomes.

O notebook do colega é um **terceiro fluxo, independente dos outros dois**:
- descarrega e prepara os seus próprios dados em `dados/preparados/<dataset>/*.parquet` (ids `BIGINT`,
  zstd);
- escreve em `output/`;
- cobre 5 datasets, incluindo o 100K e o 10M, que o pipeline não tem;
- compara cada query SQL com uma versão Polars.

Git:
- O `origin/main` (com os notebooks) e o `fase2-cloud-prep` divergem desde o `34e4e75`.
- `git merge-tree` indica que o merge é **limpo**, porque os notebooks são ficheiros novos.
- `dados/`, a pasta de dados do notebook, **não está no `.gitignore`**, nem no `main` nem nos nossos
  branches.

## 2. Inventário das queries

Todas em **dialeto DuckDB**. Leem as views `ratings(userId, movieId, rating, timestamp)` e
`movies(movieId, title, genres)`, sem leitura direta de ficheiros, o que facilita a integração.

| ID | Célula | Query | Pergunta analítica | Tabelas e colunas |
|---|---|---|---|---|
| Q01 | 108 | `generos` | Que géneros existem? | movies.genres |
| Q02 | 108 | `filmes_genero` | Quantos filmes por género (e %)? | movies.movieId, genres |
| Q03 | 108 | `utilizadores` | Estatísticas de rating por utilizador (n, média, dp, min, mediana, max) | ratings.userId, rating |
| Q04 | 108 | `distribuicao` | Quantas vezes cada utilizador deu cada valor | ratings.userId, rating |
| Q05 | 108 | `top10` | 10 melhores médias com ≥100 avaliações | ratings.movieId, rating; movies.title |
| Q06 | 108 | `ponderado` | Top 10 por média bayesiana (peso 100, média global) | ratings.movieId, rating; movies.title |
| Q07 | 108 | `anual` | Avaliações, média e utilizadores ativos por ano | ratings.timestamp, rating, userId |
| Q08 | 108 | `valores_ano` | Distribuição dos valores de rating por ano (meios pontos) | ratings.timestamp, rating |
| Q09 | 108 | `qualidade` | Nulos, domínio da escala, pares (user, filme) repetidos | ratings (todas) |
| Q10 | 109 | `cobertura` | Primeira e última avaliação, totais | ratings (todas) |
| Q11 | 109 | `mensal` | Avaliações e média por mês | ratings.timestamp, rating |
| Q12 | 109 | `integridade` | Ids de filmes repetidos, ratings sem filme, filmes com nulos | ratings.movieId; movies |
| Q13 | 109 | `perfis_ativos` | Por ano, utilizadores ativos com histórico só de inteiros, só de meios pontos ou misto | ratings.userId, timestamp, rating |
| Q14 | 109 | `perfis_cumulativos` | Idem, mas com a população acumulada (inclui anos sem atividade) | ratings.userId, timestamp, rating |
| Q15 | 109 | `grupos_atividade` | Média anual por faixa de atividade total do utilizador | ratings.userId, timestamp, rating |
| Q16 | 112 | `utilizadores_sinalizados` | Sinais de comportamento invulgar por utilizador (5 regras) | ratings (todas) |
| Q17 | 112 | `dias_filme` | Estatísticas por (filme, dia) e histórico anterior (intermédia) | ratings (todas) |
| Q18 | 112 | `evolucao_filmes` | Variação da média de cada filme entre os 5 anos anteriores e os 5 recentes | ratings.movieId, timestamp, rating; movies.title |
| Q19 | 112 | `eventos` (view) | Dias com concentração de avaliações extremas e mudança face ao histórico | Q17 |
| Q20 | 112 | `eventos` (participantes) | Q19 cruzada com utilizadores sinalizados (Q16) | ratings, Q16, Q19, movies |
| Q21 | 112 | `filtros` | Quantos pares (filme, dia) passam cada filtro dos eventos | Q17 |
| Q22 | 112 | `filmes_ano` | Série anual do filme que mais sobe e do que mais desce (para gráfico) | ratings, Q18, movies |

Outras partes do notebook ficaram fora do inventário, por serem didáticas ou já existirem:
- **Células 14, 17, 24, 30–50, 69–79 e 90:** queries da demonstração original. Leem ficheiros
  diretamente (`FROM '{RATINGS}'`), o que não é portável para o Athena, e repetem as perguntas 7.1–7.4.
- **Análises só em Polars:**
  - as células 55, 60, 63, 83, 93, 100 e 104 têm equivalente SQL entre Q07–Q22;
  - a **célula 58** (perfil global por utilizador) e a **célula 95** (eventos com os limites do
    capítulo 8) não têm versão SQL.

## 3. Tabela-resumo

Legenda:
- **DuckDB:** resultado no small (CSV/Parquet).
- **Athena:** corre tal como está.
- **Prioridade:** A = entra já; B = entra depois de corrigida; F = fica de fora.

| Query | Objetivo | Corre em DuckDB? | Corre em Athena? | Problemas | Destino local | Destino cloud | Prioridade |
|---|---|---|---|---|---|---|---|
| Q01 `generos` | Géneros distintos | Sim | Não (`unnest` no SELECT) | Duplica `sql/01` | já existe `sql/01_generos.sql` | já existe `sql/athena/queries/01` | F (duplicada) |
| Q02 `filmes_genero` | Filmes por género | Sim | Não (`unnest`) | Duplica `sql/02` | já existe | já existe | F (duplicada) |
| Q03 `utilizadores` | Estatísticas por utilizador | Sim | Não (`MEDIAN`) | Duplica `sql/03` (difere só no arredondamento) | já existe | já existe | F (duplicada) |
| Q04 `distribuicao` | Contagem por (utilizador, valor) | Sim | Sim (provável) | 3 976 linhas no small, ~1–2 M no 32M; só serve o heatmap do notebook | — | — | F (por agora) |
| Q05 `top10` | Top 10 com ≥100 avaliações | Sim | Não confirmado (`USING` + coluna qualificada) | Duplica `sql/04`, mas desempata por `movieId` (o `sql/04` não desempata) | já existe; propor desempate em `sql/04` | já existe | F (duplicada) |
| Q06 `ponderado` | Média bayesiana | Sim | Sim (provável) | A versão da célula 90 faria divisão inteira no Athena; a da célula 108 está correta | `sql/analise/ponderado.sql` → `05_analises.py` → `results/<ds>/analises/ponderado.csv` | `sql/athena/analise/ponderado.sql` | **A** |
| Q07 `anual` | Volume, média e utilizadores por ano | Sim | Não (`to_timestamp`, alias no GROUP BY, `::`) | Fuso; quase duplica `sql/05` (acrescenta utilizadores) | `sql/analise/anual.sql` | `sql/athena/analise/anual.sql` | **A** (com `${ratings}.year`) |
| Q08 `valores_ano` | Valores de rating por ano | Sim | Não (idem) | Fuso | `sql/analise/valores_ano.sql` + figura | `sql/athena/analise/valores_ano.sql` | **A** (com `${ratings}.year`) |
| Q09 `qualidade` | Nulos, domínio, repetidos | Sim | Não (`COUNT(DISTINCT (a,b))`, `timestamp` sem aspas) | Lê ratings duas vezes no Athena (aceitável) | `sql/analise/qualidade.sql` + verificação no script | `sql/athena/analise/qualidade.sql` | **A** |
| Q10 `cobertura` | Primeira e última avaliação | Sim | Não (`timestamp` sem aspas) | Duplica `eda_indicadores` (anos, totais) | — | — | F (duplicada) |
| Q11 `mensal` | Série mensal | Sim | Não (`strftime`, `to_timestamp`) | **Fuso: 6 meses diferentes** em UTC e em Europe/Lisbon | `sql/analise/mensal.sql` | `sql/athena/analise/mensal.sql` | B |
| Q12 `integridade` | Chaves e relações | Sim | Não (`ANTI JOIN`) | `filmes_sem_metadados` conta linhas de ratings, não filmes | `sql/analise/integridade.sql` + verificação | `sql/athena/analise/integridade.sql` | B |
| Q13 `perfis_ativos` | Perfis de uso da escala (ativos) | Sim | Não (`::BIGINT`, `WINDOW`, alias) | Fuso; rótulo "Só meios pontos" (célula 60) vs "Só não inteiros" | `sql/analise/perfis_ativos.sql` + figura | `sql/athena/analise/perfis_ativos.sql` | B |
| Q14 `perfis_cumulativos` | Perfis (população acumulada) | Sim | Não (`range`, `::`, `WINDOW`) | Fuso; grelha utilizadores × anos (5,8 M linhas no 32M, intencional) | `sql/analise/perfis_cumulativos.sql` | `sql/athena/analise/perfis_cumulativos.sql` | B |
| Q15 `grupos_atividade` | Média por faixa de atividade | Sim | Não (`ANY_VALUE`, `to_timestamp`) | Faixas "Até 5" vazia e "6–20" só com utilizadores de 20 avaliações; fuso | `sql/analise/grupos_atividade.sql` + figura | `sql/athena/analise/grupos_atividade.sql` | B |
| Q16 `utilizadores_sinalizados` | Sinais de bots | Sim | Não (`//`, `::INTEGER`, `timestamp`) | **Apanha o registo (onboarding): 34% sinalizados no small, 38% no 32M** | `sql/10_flag_bots.sql` (esqueleto do Luís) + resumo em `results/<ds>/analises/` | `sql/athena/analise/sinais_resumo.sql` | B |
| Q17 `dias_filme` | Tabela intermédia filme × dia | Sim | Não (`//`, `::`, `WINDOW`) | **14,7 M linhas no 32M**; não deve ser um resultado final | absorvida em Q21 | absorvida em Q21 | F (como saída) |
| Q18 `evolucao_filmes` | Filmes que sobem e descem | Sim | Não (`to_timestamp`, `FILTER` + alias) | Último ano incompleto; fuso; `year()` calculado 4 vezes por linha | `sql/analise/evolucao_filmes.sql` | `sql/athena/analise/evolucao_filmes.sql` | B |
| Q19 `eventos` (view) | Eventos de concentração | Sim (0 no small) | Não | Limites diferentes do capítulo 8; 0 eventos no small | em Q20 | em Q20 | B |
| Q20 `eventos` (participantes) | Eventos × utilizadores sinalizados | Sim (0 no small) | Não | Depende de Q16 (por corrigir) | `sql/analise/eventos.sql` | `sql/athena/analise/eventos.sql` | B |
| Q21 `filtros` | Funil dos filtros dos eventos | Sim | Não | — | `sql/analise/filtros_eventos.sql` (inclui Q17) | `sql/athena/analise/filtros_eventos.sql` | B |
| Q22 `filmes_ano` | Série para gráfico | Sim | Não (`UNION` de subqueries com `LIMIT`, `to_timestamp`) | Depende de Q18 | dentro do `05_analises.py` (figura) | — | B |

## 4. Resultados da execução no small

DuckDB 1.5.6, mediana de 3 corridas, sessão em UTC. Todas correram sem erros.

| Query | CSV (ms) | Parquet (ms) | Linhas |
|---|---:|---:|---:|
| Q01 generos | 11,7 | 1,0 | 20 |
| Q02 filmes_genero | 21,7 | 1,3 | 20 |
| Q03 utilizadores | 25,3 | 4,3 | 610 |
| Q04 distribuicao | 23,5 | 2,6 | 3 976 |
| Q05 top10 | 37,7 | 4,7 | 10 |
| Q06 ponderado | 49,5 | 2,7 | 10 |
| Q07 anual | 32,2 | 10,3 | 23 |
| Q08 valores_ano | 31,1 | 8,9 | 195 |
| Q09 qualidade | 29,3 | 5,3 | 1 |
| Q10 cobertura | 25,4 | 2,0 | 1 |
| Q11 mensal | 34,6 | 13,2 | 267 |
| Q12 integridade | 51,9 | 1,7 | 1 |
| Q13 perfis_ativos | 35,7 | 11,7 | 28 |
| Q14 perfis_cumulativos | 67,8 | 13,7 | 39 |
| Q15 grupos_atividade | 54,6 | 10,8 | 79 |
| Q16 utilizadores_sinalizados | 59,6 | 5,4 | 610 |
| Q17 dias_filme | 97,1 | 75,6 | 99 538 |
| Q18 evolucao_filmes | 71,5 | 18,2 | 300 |
| Q19 eventos (view) | 0,3 | 0,2 | 0 |
| Q20 eventos (participantes) | 28,9 | 2,4 | 0 |
| Q21 filtros | 2,5 | 2,5 | 1 |
| Q22 filmes_ano | 37,0 | 3,0 | 40 |

Os tempos de Q19–Q21 não incluem a criação das tabelas intermédias (Q16–Q18), que foi feita antes da
medição. No CSV, o tempo inclui a leitura e a inferência de tipos do ficheiro em cada corrida.

## 5. Consistência com o `04_eda.py` e com `sql/`

| Verificação | Resultado |
|---|---|
| Q09: linhas, utilizadores, filmes avaliados | 100 836 / 610 / 9 724, iguais a `results/small/eda/eda_indicadores.csv` |
| Média global (C de Q06) | 3,502, igual a `rating_media` |
| Q10: primeira e última avaliação | 1996-03-29 e 2018-09-24, consistente com `ano_primeiro_rating`/`ano_ultimo_rating` (1996/2018) |
| Q01: n.º de géneros | 20 contra `n_generos` = 19: o EDA exclui `(no genres listed)`; Q01 inclui-o. Não é erro, mas convém dizer qual dos dois se reporta. |
| Q02 contra `sql/02` | Igual (com a percentagem arredondada a 1 casa) |
| Q05 contra `sql/04` | Mesmos 10 filmes, pela mesma ordem; não há empates no small |
| Q07 contra `sql/05` (fase 1, `epoch_ms`) | Igual (ano, n.º, média a 3 casas) |
| Q03 contra `sql/03` | 607/610 iguais. Os 3 restantes só diferem no arredondamento (ex.: 4,0625 dá 4,062 num lado e 4,063 no outro). |
| Q09 / Q12: qualidade | 0 nulos, 0 fora da escala, 0 pares repetidos, 0 ratings sem filme, 0 ids repetidos |
| Q21 contra a saída do notebook (small) | 99 538 / 70 858 / 0 / 0 / 0, igual ao que o colega gravou |

## 6. Problemas encontrados e correções propostas

As versões propostas ficam **ao lado** das originais e não as substituem. Foram testadas no small,
como se descreve em cada ponto.

### P1. Fuso horário em `to_timestamp` (Q07, Q08, Q11, Q13–Q15, Q18, Q22)

`to_timestamp(timestamp)` devolve `TIMESTAMP WITH TIME ZONE`. Por isso, `year()` e `strftime()`
dependem do fuso da sessão.
- **No notebook:** funciona porque a função `ligar()` faz `SET TimeZone='UTC'`.
- **Num script sem essa linha:** num Mac em Portugal, `mensal` muda em 6 meses (ex.: 2000-05: 157 em
  UTC contra 154 em Lisboa) e `grupos_atividade` também muda.
- **Na fase 1:** o ano é calculado com `epoch_ms(timestamp * 1000)` (UTC, sem depender do fuso) e vem
  já na coluna `year` de `${ratings}`.

**Correção:**
- usar a coluna `year` de `${ratings}`, como `sql/05`;
- onde for preciso o mês, usar `epoch_ms`;
- e fixar `SET TimeZone='UTC'` na ligação do script, por segurança.

No Athena, `from_unixtime` devolve UTC.

```sql
-- Original (Q07)
SELECT year(to_timestamp(timestamp))::BIGINT AS ano, COUNT(*) AS num_ratings,
       AVG(rating) AS media, COUNT(DISTINCT userId) AS utilizadores
FROM ratings GROUP BY ano ORDER BY ano

-- Proposta DuckDB (convenção da fase 1: ${ratings} já tem year em UTC)
SELECT year AS ano, COUNT(*) AS num_ratings, AVG(rating) AS media, COUNT(DISTINCT userId) AS utilizadores
FROM ${ratings} GROUP BY year ORDER BY year

-- Proposta DuckDB para Q11 (mês sem depender do fuso)
SELECT strftime(epoch_ms(timestamp * 1000), '%Y-%m') AS mes, COUNT(*) AS num_ratings, AVG(rating) AS media
FROM ${ratings} GROUP BY mes ORDER BY mes
```

Há uma vantagem extra: com `${ratings}.year`, a mesma query aproveita o `ratings_part` particionado
(no DuckDB e no Athena).

### P2. Q16: a regra de "atividade concentrada" deteta o registo, não bots

Decomposição dos 210 utilizadores sinalizados no small (34%):

| Sinal | Utilizadores |
|---|---:|
| `atividade_concentrada` (≥50 numa hora e ≥50% do histórico) | 197 |
| `mesmo_segundo` (≥10 no mesmo segundo) | 13 |
| `valor_unico` | 1 |
| `sobretudo_baixas` | 0 |
| `sobretudo_altas` | 9 |

Em **185 dos 197**, a hora de pico está nas primeiras 24 h de atividade do utilizador. O MovieLens
pede várias avaliações no registo, e cada utilizador do dataset tem pelo menos 20, por isso este pico
é o comportamento esperado de quem se regista. No 32M, a mesma regra sinaliza 76 437 utilizadores
(38%), segundo a saída do notebook.

**Correção proposta:** calcular os sinais de hora e de segundo **sem as primeiras 24 h** de cada
utilizador. No small, os sinalizados descem para **21 (3,4%)**: 12 por atividade concentrada, 1 por
valor único e 9 por "sobretudo altas". Os limites (50, 10, 0,8) continuam a ser do Luís. Vale a pena
decidi-los com uma distribuição de referência, por exemplo o percentil 99 de `max_hora` depois do
registo.

```sql
-- Original (Q16, excerto)
WITH h AS (SELECT userId, timestamp//3600 AS hora, COUNT(*) AS n FROM ratings GROUP BY userId, hora),
     s AS (SELECT userId, timestamp, COUNT(*) AS n FROM ratings GROUP BY userId, timestamp),
     ...

-- Proposta DuckDB (excerto; versão completa no anexo A)
WITH primeira AS (SELECT userId, MIN(timestamp) AS t0 FROM ${ratings} GROUP BY userId),
     apos AS (SELECT r.* FROM ${ratings} r JOIN primeira p USING (userId)
              WHERE r.timestamp >= p.t0 + 86400),          -- ignora as primeiras 24 h (registo)
     h AS (SELECT userId, timestamp // 3600 AS hora, COUNT(*) AS n FROM apos GROUP BY userId, hora),
     s AS (SELECT userId, timestamp, COUNT(*) AS n FROM apos GROUP BY userId, timestamp),
     ...
     f AS (SELECT u.*, COALESCE(p.max_hora, 0) AS max_hora, COALESCE(q.max_segundo, 0) AS max_segundo
           FROM u LEFT JOIN p USING (userId) LEFT JOIN q USING (userId))   -- LEFT: há quem só avalie no 1.º dia
```

O denominador de `max_hora / n` continua a ser o histórico total. Assim, um pico depois do registo
só conta se for, de facto, metade de tudo o que o utilizador fez.

### P3. Q18: último ano incompleto e `year()` repetido

- **Último ano incompleto:** o período "recente" acaba em `MAX(ano)`, que é um ano parcial. No small
  é 2018, até 24 de setembro; no 32M é 2023, até 13 de outubro. Os dois períodos ficam com durações
  diferentes.
- **`year()` repetido:** é calculado 4 vezes por linha e a query lê todos os anos, embora só use os
  últimos 10.

**Correção:**
- terminar no último ano completo;
- usar `${ratings}.year`;
- filtrar os 10 anos no `WHERE`, o que permite partition pruning no `ratings_part`.

No small, a correção passa de 300 para 366 filmes comparáveis.

```sql
-- Original (excerto)
WITH fim AS (SELECT MAX(year(to_timestamp(timestamp))) AS ano FROM ratings),
     s AS (SELECT movieId,
                  COUNT(*) FILTER (WHERE year(to_timestamp(timestamp)) BETWEEN ano-9 AND ano-5) AS n_anterior, ...
           FROM ratings CROSS JOIN fim GROUP BY movieId), ...

-- Proposta DuckDB (excerto)
WITH fim AS (SELECT CASE WHEN month(epoch_ms(MAX(timestamp) * 1000)) = 12
                         THEN MAX(year) ELSE MAX(year) - 1 END AS ano FROM ${ratings}),
     s AS (SELECT r.movieId,
                  COUNT(*) FILTER (WHERE r.year BETWEEN f.ano - 9 AND f.ano - 5) AS n_anterior, ...
           FROM ${ratings} r CROSS JOIN fim f
           WHERE r.year BETWEEN f.ano - 9 AND f.ano          -- só os 10 anos usados
           GROUP BY r.movieId), ...
```

A regra "ano completo se o último mês for dezembro" é uma aproximação; dá para refinar se for
preciso.

### P4. Q15: faixas de atividade vazias

O MovieLens só inclui utilizadores com pelo menos 20 avaliações (mínimo 20 no small). Por isso:
- a faixa "Até 5" fica sempre vazia;
- a faixa "6–20" só tem quem fez exatamente 20 avaliações.

No small, os pares (utilizador, ano) distribuem-se assim: 6–20: 14; 21–50: 227; 51–100: 154; mais
de 100: 543.

**Correção:**
- faixas adaptadas ao dataset, por exemplo `20–35`, `36–70`, `71–200` e `>200` (perto dos quartis do
  small), ou quantis calculados na própria query;
- `ANY_VALUE` (não existe no Athena) substituído por um join depois de agregar;
- `${ratings}.year` em vez de `to_timestamp`.

A coluna `utilizadores` conta pares (utilizador, ano) por faixa e ano. Está certo, mas convém dizê-lo
na legenda.

### P5. Q12: o nome não corresponde ao que se conta

`filmes_sem_metadados` faz `COUNT(*)` de `ratings ANTI JOIN movies`, ou seja, conta **linhas de
avaliações** cujo filme não existe em `movies`, não filmes. No small o valor é 0, por isso não se
nota. `ANTI JOIN` só existe no DuckDB.

**Correção:** separar em `ratings_sem_filme` (linhas) e `filmes_sem_metadados` (`COUNT(DISTINCT
movieId)`), com `NOT EXISTS`, que é portável. Ver o anexo A.

### P6. Q17 `dias_filme`: resultado intermédio com milhões de linhas

Q17 devolve uma linha por (filme, dia): 99 538 no small e **14 686 114 no 32M** (saída do notebook).
- **No notebook** não é problema, porque é escrita diretamente em Parquet.
- **No Athena** seria um CSV de resultado com centenas de MB no S3. A paginação do
  `get_query_results` teria milhares de páginas.

**Correção:** não a expor como query, e calcular Q19–Q21 numa só query com CTEs que devolve só o funil
(Q21) ou os eventos (Q20). A versão Athena do funil está no anexo B. Emulada, reproduz os números do
notebook no small.

### P7. Limites diferentes entre o capítulo 8 e o capítulo 9

| Limite | Capítulo 8 (célula 95, só Polars) | Capítulo 9 e SQL (Q19–Q21) |
|---|---|---|
| Avaliação baixa | ≤ 1 | ≤ 2 |
| Avaliação alta | ≥ 4,5 | ≥ 4 |
| Histórico mínimo | 20 | 5 |
| Proporção extrema | 0,80 | 0,51 |
| Variação mínima | 1,0 | 0,5 |

O colega já assinala isto no markdown (célula 111). Antes de integrar, convém escolher **um** conjunto
de limites. Com os do capítulo 9 há 90 108 "eventos" no 32M, o que sugere que são permissivos.

### P8. Rótulos inconsistentes dos perfis

A célula 60 (Polars) usa "Só meios pontos" e as células 63 e 109 (SQL) usam "Só não inteiros".
Proposta: "Só não inteiros" em todo o lado, porque um 0,5 não é um "meio ponto" de um inteiro.

### P9. Q06: divisão inteira na versão da célula 90

- **Célula 108:** `v/(v+100.0)` está correta nos dois motores.
- **Célula 90:** usa `s.v/(s.v+p.m)` com `m` inteiro. No DuckDB, `/` é divisão real e dá o valor
  certo. No **Athena, `bigint / bigint` é divisão inteira** e daria 0, sem erro.
- **Aliases:** os aliases `R` e `C` dependem de maiúsculas, e o Athena não distingue `r` de `R`.

Proposta Athena: `CAST(s.v AS double) / (s.v + 100)` e aliases `media_filme`/`media_global` (anexo B).

### P10. Afirmações no markdown

A célula 56 diz: "Demonstra-se assim que o sistema de ratings foi alterado em 2003." Os dados são
consistentes com isso: no small, o primeiro meio ponto é de 15/05/2003 e não há nenhum antes de 2003.
Mesmo assim, não o demonstram. A célula 57, do próprio colega, já o diz.

Proposta: reescrever como observação e citar a fonte documental. O README já cita Harper & Konstan
(2015), que descreve a história do MovieLens; falta confirmar a passagem exata.

Notas menores no mesmo sentido:
- a célula 42 refere "dataset 100K", quando é o `ml-latest-small`;
- a célula 61 tem só "G".

### P11. Arredondamentos

Q03 e `sql/03` diferem em 3 utilizadores só por causa do arredondamento. Ao integrar, arredondar só na
apresentação e comparar valores exatos (como o `same()` do notebook faz).

### P12. Organização do notebook e do repositório

- **Notebooks duplicados:** `v1_3` e `v2` são o mesmo código. Proposta: manter um só, idealmente o
  `v2` com as flags do `v1_3`, como estão por omissão.
- **Configuração do `v2`:** está para correr tudo (descarrega o 10M e o 32M, cerca de 300 MB de
  ZIPs, e usa 8 GB de memória). Correr "Run all" sem rever a configuração é pesado.
- **`dados/`:** é a pasta de dados do notebook e não está no `.gitignore`, por isso há risco de
  versionar centenas de MB. O mesmo vale para `lab_resultados.zip`.
- **Tipos:** o notebook usa `BIGINT` nos ids e o pipeline usa `INTEGER`. Não muda nenhum resultado.

## 7. Compatibilidade com o Athena (Trino)

Nenhuma das 22 queries lê ficheiros diretamente: todas usam as views `ratings`/`movies`, o que
facilita a tradução. Construções a traduzir:

| DuckDB | Onde | Athena / Trino |
|---|---|---|
| `SELECT unnest(string_split(g, '\|'))` | Q01, Q02 | `CROSS JOIN UNNEST(split(g, '\|')) AS t(genero)` |
| `to_timestamp(ts)`, `epoch_ms(ts*1000)` | Q07, Q08, Q11, Q13–Q15, Q18, Q22 | `from_unixtime("timestamp")` (UTC) ou a coluna `year` de `${ratings}` |
| `strftime(t, '%Y-%m')` | Q11 | `date_format(from_unixtime("timestamp"), '%Y-%m')` |
| `timestamp` sem aspas | quase todas | `"timestamp"` (palavra reservada) |
| `expr::BIGINT`, `(cond)::INTEGER` | Q07, Q08, Q13, Q14, Q16, Q17 | `CAST(expr AS bigint)`; para contar condições, `count_if(cond)` |
| `a // b` (divisão inteira) | Q16, Q17, Q20 | `a / b` com inteiros (no Trino já é divisão inteira) |
| `GROUP BY ano` (alias do SELECT) | Q07, Q08, Q11, Q13–Q15 | `GROUP BY 1` ou a expressão (o Trino não aceita aliases no GROUP BY) |
| `WINDOW w AS (...)` | Q13, Q14, Q17 | Repetir `OVER (PARTITION BY … ORDER BY … ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)` (mais seguro do que a cláusula `WINDOW`) |
| `range(a, b+1)` + `unnest` | Q14 | `CROSS JOIN UNNEST(sequence(a, b)) AS t(ano)` |
| `ANY_VALUE(x)` | Q15 | `arbitrary(x)`, ou juntar depois de agregar |
| `ANTI JOIN` | Q12 | `WHERE NOT EXISTS (SELECT 1 …)` |
| `COUNT(DISTINCT (a, b))` | Q09 | `(SELECT COUNT(*) FROM (SELECT DISTINCT a, b FROM …))` |
| `MEDIAN(x)` | Q03 | `approx_percentile(x, 0.5)` (aproximado) |
| `JOIN … USING (movieId)` + `r.movieId` | Q05, Q15, Q18, Q22 | `JOIN … ON r.movieid = m.movieid` |
| `(SELECT … LIMIT 1) UNION (SELECT … LIMIT 1)` | Q22 | `row_number() OVER (ORDER BY …)` em CTEs (mais robusto) |
| `bigint / bigint` (divisão real no DuckDB) | Q06 da célula 90 | `CAST(v AS double) / …` |
| `FILTER (WHERE …)` | Q09, Q12, Q18 | Suportado no Trino (sem alteração) |
| `ILIKE`, `QUALIFY`, regex, `list_*` | não usados nas 22 | — |

Nomes de colunas: o Athena guarda-os em minúsculas, mas, sem aspas, `movieId` resolve para `movieid`.
Nenhuma query cita nomes entre aspas, por isso o único efeito é que os resultados saem com nomes em
minúsculas. Os aliases que diferem só em maiúsculas (`R`/`r`, `C`/`c`) passam a colidir (P9).

As versões Athena propostas estão no anexo B. Emuladas no DuckDB, `qualidade`, `ponderado`, `anual`,
`valores_ano`, `mensal`, `perfis_ativos` e `perfis_cumulativos` dão **exatamente** os resultados das
originais no small. **Nenhuma foi executada no Athena.** A primeira corrida real pode revelar detalhes
de sintaxe.

## 8. Escalabilidade (32M)

**DuckDB local.** O colega correu todas as queries no 32M. Tempos das saídas gravadas:

| Bloco | Tempo no 32M |
|---|---|
| Q01–Q09 + Q10–Q15 | 150 s (cada uma das 9 perguntas corre em SQL e Polars e é comparada) |
| Q16–Q22 | 117 s |

Há três questões de escala a ter em conta:
- **Dados para Python:** nada traz os dados completos para Python. O maior resultado materializado é
  Q16 (200 948 linhas, uma por utilizador); Q17 vai diretamente para Parquet. Num script, o resultado
  de Q16 deve ir para CSV e Parquet, e para o relatório só o resumo.
- **Produtos cartesianos:**
  - Só existe um intencional: em Q14, a grelha utilizadores × anos (200 948 × 29 ≈ 5,8 M linhas no
    32M), que se aguenta bem.
  - Os `CROSS JOIN` de Q06 e Q18 são com uma única linha, por isso inofensivos.
  - Verifiquei os joins: todos são 1:1 por `userId` ou `movieId`, ou contra chaves únicas
    (`movies.movieId`, (filme, dia)), e nenhum multiplica linhas.
- **Pior caso de memória:** `COUNT(DISTINCT (userId, movieId))` em Q09 tem de guardar 32 M pares.
  O DuckDB despeja para disco se precisar.

**Athena: volume lido.** Estimativa para o 32M em Parquet sem partição (158,9 MB). A distribuição por
coluna é a do small: timestamp 55%, movieId 37%, rating 7,5% e userId 0,6%. O Athena cobra no mínimo
10 MB por query, a 5 USD por TB.

| Query | Colunas e leituras | MB lidos (estim.) | Custo |
|---|---|---:|---:|
| Q06 ponderado | movieId, rating (2 leituras) + movies | ~85 | < 0,001 USD |
| Q07 anual / Q08 valores_ano | timestamp, rating (+ userId) | ~100 | < 0,001 USD |
| Q09 qualidade | todas, 2 leituras | ~320 | ~0,002 USD |
| Q12 integridade | movieId (2 leituras) + movies | ~120 | < 0,001 USD |
| Q14 perfis_cumulativos | 3 leituras de ratings | ~190 | ~0,001 USD |
| Q16 sinais (proposta) | 4 leituras de ratings | ~350 | ~0,002 USD |
| Q18 evolucao_filmes | só 10 anos em `ratings_part` | ~60–100 | < 0,001 USD |
| Q21 funil de eventos | todas | ~160 | < 0,001 USD |

Sobre o CSV (`ratings_csv`, 877 MB), cada leitura custa 877 MB: Q16 leria cerca de 3,5 GB, ou seja
cerca de 0,02 USD. **O custo não é o problema.** O risco no Athena é o **tamanho dos resultados**
(Q17, e Q16 completa com 200 948 linhas). A proposta devolve agregados ou resumos e deixa as tabelas
grandes para `CREATE TABLE AS` (CTAS) em Parquet, se forem precisas.

## 9. Sobreposições com o que já existe

| Query do colega | Já existe | Diferença | Proposta |
|---|---|---|---|
| Q01 generos | `sql/01_generos.sql`, `04_eda` (`n_generos`) | Q01 inclui `(no genres listed)`; o EDA exclui-o (19 contra 20) | Não integrar; uniformizar a definição no relatório |
| Q02 filmes_genero | `sql/02_filmes_por_genero.sql`, figura 06 do EDA | Igual (Q02 não arredonda) | Não integrar |
| Q03 utilizadores | `sql/03_avaliacoes_por_utilizador.sql` | Só arredondamento | Não integrar |
| Q05 top10 | `sql/04_top_filmes.sql`, células 14/86 | Q05 desempata por `movieId` | Não integrar; propor o desempate em `sql/04` (alteração à fase 1, decisão vossa) |
| Q07 anual | `sql/05_ratings_por_ano.sql`, figura 05 do EDA | Q07 acrescenta utilizadores ativos | Integrar como análise; `sql/05` fica no benchmark |
| Q10 cobertura | `eda_indicadores.csv` (anos, totais) | Q10 dá o timestamp exato | Não integrar (ou juntar a Q09) |
| Q09 qualidade | `eda_resumo_tabelas.csv` (nulos, distintos) | Q09 acrescenta o domínio da escala e os pares repetidos | Integrar |
| Q16 sinais | `sql/10_flag_bots.sql` (esqueleto atribuído ao Luís) | Q16 é o conteúdo previsto | Integrar aqui, depois de corrigida |
| Nomes | `sql/athena/queries/06_ratings_desde_2015.sql`, `sql/cloud/06…` | O número 06 já está ocupado | Queries novas em `sql/analise/` com nomes, sem números |

## 10. Proposta de integração (sem implementar)

Princípios:
1. **Não pôr queries novas em `sql/*.sql`.** O `03_benchmark.py` corre automaticamente todos os
   ficheiros de `sql/`, e acrescentar 15 queries mudaria o benchmark da fase 1. A exceção é Q16, que
   ocupa o lugar já previsto em `sql/10_flag_bots.sql`.
2. **Mesma convenção da fase 1:** `${ratings}` (com `year` em UTC) e `${movies}`. Assim cada query
   funciona com CSV, Parquet e Parquet particionado.
3. **Athena:** `${ratings}`/`${movies}` também, substituídos por nomes de tabelas, como em
   `athena_benchmark.py`. Serve tanto para `ratings`/`movies` (DDL do repositório) como para
   `smallratingsparquet`/`smallmoviesparquet`, se essas tabelas existirem.

### Pipeline local: `scripts/05_analises.py` (novo)

- **Opções:** `--dataset {small,1m,32m}` e `--fonte {auto,parquet,csv}`, com o mesmo comportamento do
  `04_eda.py`.
- **O que faz:**
  - lê `sql/analise/*.sql`;
  - liga ao DuckDB com `SET TimeZone='UTC'`;
  - corre cada query e escreve `results/<dataset>/analises/<query>.csv`;
  - gera figuras numeradas `results/<dataset>/analises/NN_<query>.png`, com o estilo NOVA do
    `04_eda.py`;
  - escreve um `analises_relatorio.md`.
- **Verificações que falham o script:** Q09 tem de ter 0 nulos e 0 valores fora da escala, e Q12 tem
  de ter 0 ratings sem filme e 0 ids repetidos. São as mesmas asserções que o notebook faz.
- **Integração no pipeline:** novo passo `analises` no `run_pipeline.py`. Isto altera um ficheiro
  existente e precisa de aprovação.
- **Estilo NOVA:** reutilizar as funções do `04_eda.py` obriga a movê-las para um módulo partilhado
  (alteração a ficheiro existente) ou a duplicá-las. Decisão vossa.

### Pipeline cloud: `sql/athena/analise/*.sql`

- **Tabelas:** só `ratings` (ou `ratings_part`) e `movies`, que já estão no DDL. **Nenhuma query
  precisa de `tags` nem de `links`.**
- **Execução:** um script novo (`scripts/athena_analises.py`) que reutiliza `athena_common.py`,
  escreve `results/<dataset>/analises_athena/<query>.csv` e compara com os CSV locais (n.º de linhas e
  valores com tolerância).

### Destino por query

| Prioridade | Query | Local (DuckDB) | Cloud (Athena) | Saídas |
|---|---|---|---|---|
| A | Q06 ponderado | `sql/analise/ponderado.sql` | `sql/athena/analise/ponderado.sql` | CSV |
| A | Q07 anual | `sql/analise/anual.sql` | `sql/athena/analise/anual.sql` | CSV + PNG (volume, média, utilizadores) |
| A | Q08 valores_ano | `sql/analise/valores_ano.sql` | `sql/athena/analise/valores_ano.sql` | CSV + PNG (% por valor e ano) |
| A | Q09 qualidade | `sql/analise/qualidade.sql` | `sql/athena/analise/qualidade.sql` | CSV + verificação |
| B | Q11 mensal | `sql/analise/mensal.sql` (P1) | `sql/athena/analise/mensal.sql` | CSV + PNG |
| B | Q12 integridade | `sql/analise/integridade.sql` (P5) | `sql/athena/analise/integridade.sql` | CSV + verificação |
| B | Q13 perfis_ativos | `sql/analise/perfis_ativos.sql` (P1, P8) | `sql/athena/analise/perfis_ativos.sql` | CSV + PNG |
| B | Q14 perfis_cumulativos | `sql/analise/perfis_cumulativos.sql` (P1, P8) | `sql/athena/analise/perfis_cumulativos.sql` | CSV + PNG |
| B | Q15 grupos_atividade | `sql/analise/grupos_atividade.sql` (P1, P4) | `sql/athena/analise/grupos_atividade.sql` | CSV + PNG |
| B | Q16 sinais | `sql/10_flag_bots.sql` (P2) | `sql/athena/analise/sinais_resumo.sql` (só o resumo) | CSV por utilizador (local) + resumo |
| B | Q18 evolucao_filmes | `sql/analise/evolucao_filmes.sql` (P1, P3) | `sql/athena/analise/evolucao_filmes.sql` | CSV + PNG (Q22) |
| B | Q19–Q21 eventos | `sql/analise/filtros_eventos.sql`, `sql/analise/eventos.sql` (P6, P7) | `sql/athena/analise/filtros_eventos.sql` | CSV |
| B | Q22 filmes_ano | dentro do `05_analises.py` (figura de Q18) | — | PNG |
| F | Q01, Q02, Q03, Q05, Q10 | já existem (secção 9) | já existem | — |
| F | Q04 distribuicao | — (só o heatmap do notebook) | — | — |
| F | Q17 dias_filme | absorvida em Q19–Q21 | absorvida | — |

## 11. Plano de integração, passo a passo

1. **Decisões vossas** (secção 12), em particular os limites da deteção de bots (P2, P7), que são
   trabalho do Luís.
2. **Branch:** criar `integracao-queries-colega` a partir de `fase2-cloud-prep` e fazer
   `git merge origin/main`, que traz os notebooks sem conflitos. Sem `rebase` nem `reset`.
3. **`.gitignore`:** acrescentar `dados/` e `lab_resultados.zip`, antes de alguém correr o notebook na
   raiz do repositório.
4. **Prioridade A:** criar `sql/analise/` com Q06–Q09 na convenção `${ratings}`/`${movies}`, e o
   `scripts/05_analises.py`.
   - Testar com `--dataset small --fonte parquet` e `--fonte csv`.
   - Comparar com as saídas do notebook (Q09 e Q21 já batem) e com `eda_indicadores.csv`.
5. **Prioridade A no Athena:** criar `sql/athena/analise/` com as versões do anexo B e um
   `scripts/athena_analises.py` (com `--dry-run`).
   - Testar com a emulação local agora e no Athena quando houver conta.
6. **Prioridade B:** aplicar as correções P1–P8, depois de validadas com o Luís.
   - Q16 passa a ser `sql/10_flag_bots.sql`; isto altera o benchmark da fase 1, como já estava
     previsto.
   - Testar no small e comparar com o notebook (antes e depois das correções).
7. **Documentação:** secção "Análises" no README; indicar qual notebook é o oficial e remover o
   duplicado (com o colega).
8. **32M:** só depois da vossa aprovação, correr `05_analises.py --dataset 32m` e, no Athena, as
   queries A e B.

## 12. Questões em aberto

1. As tabelas `smallmoviesparquet`/`smallratingsparquet` e o Glue Crawler existem na conta AWS? Se
   sim, qual dos esquemas fica: o crawler ou o DDL do repositório?
2. O Luís concorda com as correções P2 (excluir as primeiras 24 h), P3, P4 e P7 (um só conjunto de
   limites)?
3. Integramos só as queries no pipeline e deixamos o notebook como está, ou o notebook passa a ler os
   resultados de `results/<dataset>/analises/`?
4. Acrescentamos o desempate por `movieId` ao `sql/04_top_filmes.sql`? Isto altera uma query da fase 1.
5. Podemos alterar o `run_pipeline.py` (passo `analises`) e mover o estilo NOVA do `04_eda.py` para um
   módulo partilhado?

## 13. Fase 2: implementação (5 de novembro de 2026)

Branch `integracao-queries-luis`, criado a partir de `fase2-cloud-prep`, com merge do `origin/main`
(limpo; traz os dois notebooks). Commits locais por bloco, **sem push**. O notebook do Luís não foi
alterado.

### 13.0 Decisões tomadas (respostas à secção 12) e correções ao contexto

| Questão | Decisão |
|---|---|
| 1. Tabelas do Athena | As do nosso DDL: base `movielens_<ds>`, tabelas `ratings`, `ratings_part`, `movies`, … Sem Glue Crawler nem tabelas `small…parquet` (a nota "a confirmar" da secção 1 fica resolvida). |
| 2. Deteção de bots | A regra original do Luís não é corrigida: é **substituída** por uma abordagem nova (13.5), num ficheiro próprio marcado "a validar com o Luís". As propostas P2 e o anexo A (Q16) deixam de se aplicar. |
| 3. Notebook | Fica como está. As queries são extraídas para `.sql` com um comentário de origem (notebook, célula, id da célula e chave do dicionário). |
| 4. Desempate em `sql/04` | Sim, por `movieId` (13.1). |
| 5. Ficheiros existentes | `run_pipeline.py` só para o passo 05 e `04_eda.py` só para o fuso. Diffs aprovados antes de gravar (13.1). |

Outras regras seguidas:
- `--fonte` só existe no `04_eda.py`. O `05_analises.py` novo tem `--fonte {parquet,csv}`.
- Nada novo entrou em `sql/` (o `03_benchmark.py` corre tudo o que lá estiver). A única alteração
  em `sql/` foi o desempate em `sql/04`. As queries novas estão em `sql/analise/` e as versões
  Athena em `sql/athena/analise/`, com os mesmos nomes de ficheiro.
- **Cloud:** as versões Athena foram escritas e emuladas no DuckDB, mas não foram executadas na AWS.
- **32M:** não corri nada sobre o 32M. Os números do 32M citados vêm do notebook ou do
  `results/32m/eda/` que já existia.

O que foi criado:

| Ficheiro | Conteúdo |
|---|---|
| `scripts/05_analises.py` | Corre `sql/analise/*.sql` (`--dataset`, `--fonte {parquet,csv}`, `--queries`, `--emular-athena`). Escreve `results/<ds>/analises/<query>.csv`, `analises_resumo.csv` e `analises_relatorio.md`. **Falha** se alguma verificação falhar (ver abaixo). |
| `sql/analise/*.sql` (16) | 14 queries do Luís integradas ou corrigidas, mais `10_flag_bots.sql` e `10_flag_bots_calibracao.sql` |
| `sql/athena/analise/*.sql` (16) | As versões Athena, com os mesmos nomes |
| `results/{small,1m}/analises/` | Resultados, relatório e `athena_emulado/` (resultados emulados e `comparacao.csv`) |

Verificações do `05_analises.py`, que fazem o script falhar:
- `qualidade`: 0 nulos e 0 valores fora da escala; no 1M, só estrelas inteiras de 1 a 5.
- `integridade`: 0 ids de filmes repetidos e 0 avaliações sem filme.
- Totais iguais aos de `results/<ds>/eda/eda_indicadores.csv`: linhas, utilizadores, filmes
  avaliados e média global.
- A soma de `anual` é igual ao total de linhas.
- No small, os 5 utilizadores de referência têm a classificação esperada (13.5).
- Com `--emular-athena`: o resultado de cada versão Athena é igual ao da versão DuckDB (pela
  posição das colunas, com tolerância de 1e-6).
- Também com `--emular-athena`: nenhuma versão Athena pode ter um literal decimal numa
  multiplicação ou divisão (ver 13.6).

### 13.1 Bloco 1: correções transversais

**Fuso horário.** `SET TimeZone = 'UTC'` passou a ser executado logo após abrir a ligação, no
`03_benchmark.py`, no `04_eda.py` e no `05_analises.py`. O `run_pipeline.py` não abre nenhuma ligação
DuckDB (lança cada passo noutro processo), por isso não precisou dessa linha.

Teste com as duas queries afetadas, no small. O valor indicado é o hash do resultado.

| `TZ` da máquina | `mensal` original sem `SET` | `mensal` original com `SET` | `grupos_atividade` original sem `SET` | `grupos_atividade` original com `SET` | `mensal` com `epoch_ms`, sem `SET` |
|---|---|---|---|---|---|
| UTC | cdc961ee34 | cdc961ee34 | b2afed2c70 | b2afed2c70 | cdc961ee34 |
| America/New_York | **0a801e1c06** | cdc961ee34 | **b7d127f4da** | b2afed2c70 | cdc961ee34 |
| Asia/Tokyo | **bffe5ff43f** | cdc961ee34 | **83ed23809c** | b2afed2c70 | cdc961ee34 |

Sem o `SET`, as duas queries originais mudam com o fuso da máquina. Com o `SET`, ou usando
`epoch_ms` em vez de `to_timestamp`, o resultado é sempre o mesmo.

Depois, corri o `05_analises.py` completo (16 queries mais as 16 versões Athena emuladas, no small e
no 1M) com `TZ=UTC`, `TZ=America/New_York` e `TZ=Asia/Tokyo`:
- Os 66 CSV têm os mesmos valores nos três fusos. A maior diferença é 2,2e-15.
- Essa diferença também aparece entre duas corridas seguidas em UTC. Vem da ordem das somas em
  vírgula flutuante na agregação paralela do DuckDB, e não do fuso. Afeta só os ficheiros com somas
  de frações (`distribuicao`, `grupos_atividade`), que podem mudar no último dígito de uma corrida
  para a outra.

**No Athena:** `from_unixtime("timestamp")` devolve o instante em UTC, e `year` vem das pastas de
`ratings_part`, calculado em UTC no `prepare_cloud.py`. Isto está escrito no cabeçalho de cada
versão Athena que usa datas.

**Desempate em `sql/04`.** O `03_benchmark.py` voltou a correr no small:
- O n.º de linhas é igual ao da fase 1 nas 5 queries e nos 2 formatos.
- Os tempos ficaram dentro da variação habitual. Por exemplo, `04_top_filmes`: 4,4 ms e 4,1 ms,
  contra 6,4 ms e 4,5 ms em 2026-11-01.
- O top 10 é igual antes e depois, no small e no 1M. Há empates na média exata (1 grupo no small e
  33 no 1M), mas nenhum dentro do top 10, por isso não mudou a ordem.

**Diffs aplicados** (aprovados antes de gravar os do `run_pipeline.py` e do `04_eda.py`):

```diff
--- a/run_pipeline.py
+++ b/run_pipeline.py
@@ -7,6 +7,7 @@ Objetivo:
         parquet    scripts/02_to_parquet.py  converter para Parquet (sem partição e por ano)
         benchmark  scripts/03_benchmark.py   medir o tempo das queries de sql/
         eda        scripts/04_eda.py         análise exploratória (figuras e relatório)
+        analises   scripts/05_analises.py    queries de análise de sql/analise/ (CSV e relatório)
@@ -46,6 +47,7 @@ STEPS = {
     'parquet': 'scripts/02_to_parquet.py',
     'benchmark': 'scripts/03_benchmark.py',
     'eda': 'scripts/04_eda.py',
+    'analises': 'scripts/05_analises.py',
 }
--- a/scripts/04_eda.py
+++ b/scripts/04_eda.py
@@ -154,6 +154,10 @@ def localizar(base, dataset, tabela, fonte):
 def ligar(base, dataset, fonte):
     """Cria uma ligação DuckDB com uma view por tabela encontrada. Devolve (ligação, origem)."""
     con = duckdb.connect()
+    # Fuso fixo em UTC: funções como to_timestamp devolvem TIMESTAMP WITH TIME ZONE e o ano
+    # ou o mês dependeriam do fuso da máquina. Este script usa epoch_ms (sem fuso), mas
+    # assim nenhuma query futura fica dependente do sítio onde corre.
+    con.execute("SET TimeZone = 'UTC'")
     origem = {}
--- a/sql/04_top_filmes.sql
+++ b/sql/04_top_filmes.sql
@@ -4,7 +4,8 @@
--- exata e não pela arredondada, para o desempate ser correto.
+-- exata e não pela arredondada, para o desempate ser correto. Em caso de empate na
+-- média, o movieId decide a ordem, para o resultado ser sempre o mesmo (determinístico).
@@ -18,5 +19,5 @@ FROM ${ratings} r
 HAVING COUNT(*) >= 100
-ORDER BY AVG(r.rating) DESC
+ORDER BY AVG(r.rating) DESC, m.movieId
 LIMIT 10;
--- a/scripts/03_benchmark.py
+++ b/scripts/03_benchmark.py
@@ -86,6 +86,9 @@ def main():
                 con = duckdb.connect()
+                # Fuso fixo em UTC: funções como to_timestamp dependem do fuso da sessão.
+                # As queries de sql/ usam epoch_ms (sem fuso), mas assim nenhuma depende da máquina.
+                con.execute("SET TimeZone = 'UTC'")
                 t0 = time.perf_counter()
```

O `04_eda.py` alterado foi corrido numa cópia, com `TZ=Asia/Tokyo`: `eda_indicadores.csv` ficou
igual.

### 13.2 Bloco 2: queries que entram já

`ponderado`, `anual`, `valores_ano` e `qualidade` foram extraídas tal como estavam, com estas
alterações mínimas:
- `${ratings}`/`${movies}` em vez das views do notebook;
- a coluna `year` (UTC) em vez de `year(to_timestamp(...))`;
- em `ponderado`, os aliases `R`/`C` passam a `media_filme`/`media_global`, e acrescenta-se a
  coluna `media_global`, para validar a média contra o `04_eda.py`.

| Verificação | small | 1M |
|---|---|---|
| Linhas / utilizadores / filmes avaliados (`qualidade`) | 100 836 / 610 / 9 724 | 1 000 209 / 6 040 / 3 706 |
| Média global (`ponderado.media_global`) | 3,502 | 3,582 |
| Iguais ao `04_eda.py` | sim | sim |
| Soma de `anual` = linhas | sim | sim |
| Nulos / fora da escala / pares repetidos | 0 / 0 / 0 | 0 / 0 / 0 (só inteiros 1–5) |
| `--fonte parquet` e `--fonte csv` | as verificações passam nas duas | as verificações passam nas duas |
| Athena emulado = DuckDB | 4/4 | 4/4 |

### 13.3 Bloco 3: queries corrigidas

Comparação entre a versão original, extraída do notebook com `ast` e corrida em DuckDB com a sessão
em UTC, e a versão corrigida. Script de comparação: fora do repositório, na pasta temporária da
sessão.

| Query | small: original → corrigida | 1M: original → corrigida | Diferenças e porquê |
|---|---|---|---|
| Q04 `distribuicao` | 3 976 → 10 linhas | 28 370 → 5 linhas | O original devolvia (utilizador × valor): no 32M seriam ~1,5 M linhas, só para o heatmap. A corrigida agrega por valor (utilizadores que o usam, % de avaliações e peso médio no histórico de cada utilizador). Os agregados reconstruídos a partir da saída original são **iguais** nos dois datasets. |
| Q11 `mensal` | 267 → 267, iguais | 35 → 35, iguais | Em UTC, igual. A corrigida usa `epoch_ms` e não depende do fuso (13.1). |
| Q12 `integridade` | 0/0/0 → 0/0/0/0 | idem | O original chamava `filmes_sem_metadados` a uma contagem de linhas. A corrigida separa `ratings_sem_filme` (linhas) de `filmes_sem_metadados` (filmes distintos) e usa `NOT EXISTS`. |
| Q13 `perfis_ativos` | 28 → 28, iguais | 4 → 4, iguais | Só a forma muda: `year` em UTC, `count_if`, janela por extenso e rótulo "Só não inteiros". |
| Q14 `perfis_cumulativos` | 39 → 39, iguais | 4 → 4, iguais | Idem. A grelha utilizadores × anos fica dentro da query. |
| Q15 `grupos_atividade` | 79 → 108 linhas | 15 → 20 linhas | Faixas novas, fixas e iguais em todos os datasets: **20–49, 50–99, 100–249, 250–999, 1000+** (o mínimo de 20 é o garantido pelo MovieLens). Utilizadores por faixa: small 225/137/143/93/12; 1M 1743/1352/1720/1184/41. No 32M (mediana 73, p90 364, máximo 33 332, segundo o EDA) nenhuma fica vazia. No original, "Até 5" ficava sempre vazia e "6–20" só tinha quem fez exatamente 20. Os totais por ano (utilizadores ativos e avaliações) são **iguais** nas duas versões. Acrescenta `faixa_min` para ordenar as faixas. |
| Q18 `evolucao_filmes` | 300 → 366 filmes | 0 → 0 | **Opção usada: só anos completos** (não se anualiza). O último ano só conta se o último rating for de 31/12; senão o fim passa para o ano anterior. As colunas `periodo_anterior`, `periodo_recente` e `criterio` dizem-no em cada linha, por exemplo "só anos completos: exclui 2018 (parcial, último rating 2018-09-24)". No small, os períodos passam de 2009–2013 / 2014–2018 (parcial) para 2008–2012 / 2013–2017, e 289 filmes são comuns às duas versões. Muda a maior subida (de *Ace Ventura* para *Starship Troopers*); a maior descida continua a ser *Grease*. No 1M (2000-04 a 2003-02) não há 10 anos, por isso as duas versões devolvem 0 linhas. |
| Q22 `filmes_ano` | 40 → 39 linhas | 0 → 0 | Os filmes são escolhidos com a Q18 corrigida (*Starship Troopers* e *Grease*, em vez de *Ace Ventura* e *Grease*). `ROW_NUMBER()` em vez de `UNION` com `LIMIT` dentro de subqueries, e uma coluna `tipo`. |
| Q21 `filtros_eventos` | 99 538 / 70 858 / 0 / 0 / 0, **iguais** | 407 251 / 393 200 / 43 440 / 30 551 / 3 884, **iguais** | A tabela filme × dia (`dias_filme`) só existe como CTE. Os limites estão numa CTE `lim` e saem no resultado. |
| Q20 `eventos` | 0 → 0 eventos | 3 884 → 3 884 eventos; devolve 100 | Os eventos são os mesmos. A corrigida devolve os 100 com mais suspeitos (`LIMIT` justificado: são para inspeção) e o total na coluna `total_eventos`. O cruzamento passa a usar a nova deteção: com a regra antiga, 3 844 dos 3 884 eventos do 1M tinham pelo menos um "sinalizado", porque a regra sinalizava 47% dos utilizadores. Com a nova, só 56 têm um suspeito, e nunca mais de 1 por evento. 2 246 têm pelo menos um utilizador em lote, que se conta à parte. |

Sobre `dias_filme` (14,7 M linhas no 32M): já não é devolvida em lado nenhum. No DuckDB é uma CTE
de `filtros_eventos` e de `eventos`. No Athena também; se for precisa como tabela, cria-se com CTAS
em Parquet (está indicado no cabeçalho das duas versões Athena).

Resultados devolvidos pelas versões Athena:
- **Agregados:** todas, exceto as duas abaixo.
- **`evolucao_filmes`:** devolve uma linha por filme comparável (366 no small; no 32M, no máximo
  algumas dezenas de milhares).
- **`10_flag_bots`:** uma linha por utilizador; corre como CTAS (13.5).
- **`LIMIT` justificado:** `ponderado` (top 10) e `eventos` (top 100).

Os limites dos eventos continuam a ser os do capítulo 9 do notebook (P7). Escolher um só conjunto
fica para decidir com o Luís.

### 13.4 Bloco 4: queries que ficam de fora (7)

| Query | Porquê | Onde está a resposta |
|---|---|---|
| Q01 `generos` | Duplica | `sql/01_generos.sql` (e `n_generos` do `04_eda.py`; 20 contra 19, porque o EDA exclui `(no genres listed)`) |
| Q02 `filmes_genero` | Duplica | `sql/02_filmes_por_genero.sql` |
| Q03 `utilizadores` | Duplica (difere só no arredondamento de 3 utilizadores) | `sql/03_avaliacoes_por_utilizador.sql` |
| Q05 `top10` | Duplica. A única diferença, o desempate por `movieId`, foi adotada em `sql/04` (13.1) | `sql/04_top_filmes.sql` |
| Q10 `cobertura` | Duplica | `eda_indicadores.csv` (`ano_primeiro_rating`, `ano_ultimo_rating`, totais) e `sql/analise/qualidade.sql` (totais) |
| Q17 `dias_filme` | Passo intermédio (tabela filme × dia) | É absorvida como CTEs `d`, `h` e `v` em `sql/analise/filtros_eventos.sql` e `sql/analise/eventos.sql` (e nas versões Athena). No Athena, se for precisa como tabela: CTAS em Parquet. |
| Q19 `eventos` (view) | Passo intermédio (filtro dos eventos sobre Q17) | As condições estão nos `count_if` de `filtros_eventos.sql` e nas CTEs `ev`/`e` de `eventos.sql` |

Ao todo são 22 queries: 4 integradas, 10 corrigidas, 7 fora e 1 substituída (Q16, pela deteção de
bots).

### 13.5 Bloco 5: deteção de bots (substitui a regra do Luís)

Ficheiros:
- `sql/analise/10_flag_bots.sql`: uma linha por utilizador.
- `sql/analise/10_flag_bots_calibracao.sql`: distribuição e n.º de sinalizados por limiar.
- As versões Athena, com os mesmos nomes. No Athena, a tabela por utilizador corre como **CTAS em
  Parquet** (`flag_bots`) e só a calibração (uma linha) é devolvida.
- Os dois cabeçalhos dizem **"A VALIDAR COM O LUÍS"**.
- O esqueleto `sql/10_flag_bots.sql` do benchmark ficou intacto.

**Regras:**
1. **Eventos de submissão.** As avaliações com o mesmo `(userId, timestamp)` formam um evento, e o
   n.º de avaliações é um atributo do evento. Todos os ritmos são medidos em eventos. Assim, uma
   página de avaliações gravada no mesmo segundo conta como uma única ação.
2. **Submissão em lote.** Utilizadores com pelo menos um evento com 10 ou mais avaliações no mesmo
   segundo. O 10 é o limite do sinal `mesmo_segundo` do Luís. Não é bot e aparece numa categoria à
   parte.
3. **Regra A: ritmo sustentado fora do registo.**
   - Ignora as primeiras 24 h de cada utilizador.
   - `eventos_10min` = `COUNT(*) OVER (PARTITION BY userId, fase ORDER BY ts RANGE BETWEEN CURRENT
     ROW AND 599 FOLLOWING)`. A janela é calculada dentro de cada fase (registo / depois), para não
     misturar as duas.
   - Também se calcula o intervalo mediano entre eventos.
   - O limiar é o **quantil 99,9%** do máximo de `eventos_10min` entre os utilizadores com
     atividade depois do registo. É calculado na própria query, por isso não há nenhum valor fixo
     do tipo "x por minuto".
4. **Regra B: registo extremo.** Nas primeiras 24 h, pelo menos 100 eventos ("centenas") **e**
   intervalo mediano ≤ 2 s. Os dois valores vêm da definição pedida, não de uma calibração.
5. **Sinais complementares**, que não classificam sozinhos e são contados de 0 a 3:
   - desvio-padrão das notas no 1% mais baixo;
   - % de notas iguais (nota modal) no 1% mais alto;
   - % de eventos em lote (2 ou mais avaliações) no 1% mais alto.
   Todos os quantis são calculados dentro do dataset.
6. **Classificação:**
   - `suspeito (regra A)`, `suspeito (regra B)` ou `suspeito (regras A e B)`;
   - senão, `submissão em lote`;
   - senão, `sem sinais`.
   Nunca "bot confirmado".

**Utilizadores de referência (small).** A classificação obtida é a esperada nos 5. O
`05_analises.py` verifica-o e grava `10_flag_bots_referencia.csv`.

| userId | Caso | Esperado | Obtido | Justificação (números da query) |
|---|---|---|---|---|
| 257 | 20 avaliações em 11 min no registo | não sinalizado | **sem sinais** | Registo: 19 eventos, mediana de 4 s (a regra B exige ≥ 100 eventos e ≤ 2 s). Sem atividade depois do registo. Máx. 2 avaliações no mesmo segundo. 0/3 sinais complementares. |
| 7 | uso normal | não sinalizado | **sem sinais** | Registo: 102 eventos, mediana de 5 s (> 2 s). Depois do registo: máx. 4 eventos em 10 min (limiar 114,8). Máx. 1 avaliação no mesmo segundo. 0/3. |
| 89 | 518 avaliações em 23 min, ~2 s cada | candidato | **suspeito (regra B)** | 481 eventos nas primeiras 24 h, mediana de 2 s. 0/3. |
| 610 | 566 avaliações numa hora, ~4 s cada, ~6 meses depois do registo | sinalizado | **suspeito (regra A)** | 119 eventos em 10 min depois do registo (limiar p99,9 = 114,8; é o máximo do small), mediana de 4,5 s. 0/3. |
| 534 | muitas avaliações no mesmo segundo (2016) | lote, não bot | **submissão em lote** | Até 128 avaliações no mesmo segundo, desde 2016-04-04. 0/3. |

Os casos de submissão em lote dos anos 90 indicados (191, 429, 99, 163) são todos classificados como
**submissão em lote**: até 34, 37, 23 e 10 avaliações no mesmo segundo, em 3 a 4 eventos cada. No
small há 13 utilizadores nesta categoria:
- 9 com o primeiro rating entre 1996 e 1998: 99, 163, 191, 206, 270, 337, 429, 492 e 544;
- 3 entre 2000 e 2003: 185, 294 e 500;
- 1 em 2016: o 534.
No 1M (2000–2003) são 339.

**Distribuição do ritmo sustentado e limiares** (máximo de eventos numa janela de 10 min, depois
das primeiras 24 h):

| | small | 1M |
|---|---:|---:|
| Utilizadores com atividade depois do registo | 248 de 610 | 2 239 de 6 040 |
| p50 / p90 / p95 | 18 / 52,3 / 61,7 | 14 / 26 / 29 |
| p99 / p99,5 / p99,9 | 90,8 / 100,6 / 114,8 | 35 / 38 / 40 |
| Máximo | 119 (o 610) | 45 |
| Sinalizados pela regra A no p99 / p99,5 / p99,9 | 3 / 2 / 1 | 25 / 13 / 6 |
| Sinalizados pela regra B | 1 (o 89) | 0 |
| **Suspeitos (A ou B), com o p99,9** | **2 (0,33%)** | **6 (0,10%)** |
| Submissão em lote (à parte) | 13 (2,1%) | 339 (5,6%) |
| **Regra original do Luís** (`num_sinais > 0`) | **210 (34,4%)** | **2 829 (46,8%)** |

Sensibilidade da regra B: com ≥ 200 eventos em vez de ≥ 100, o resultado é o mesmo (só o 89 no
small, ninguém no 1M).

**Ponto a calibrar no 32M.** A regra A, só com um quantil, sinaliza sempre a cauda da distribuição,
mesmo quando a cauda é humana:
- **1M:** os 6 sinalizados no p99,9 fazem 40–45 eventos em 10 min, com intervalos medianos de 14 a
  19 s, o que é plausível para uma pessoa a avaliar filmes que já conhece.
- **Small:** o p99,9 é, na prática, o máximo (só há 248 utilizadores com atividade depois do
  registo).
- **O que falta saber:** se, no 32M, a cauda se separa claramente do resto (como o 610 no small) ou
  se é contínua (como no 1M).
- **Se for contínua:** proponho, como decisão vossa e do Luís, exigir também um mínimo de
  plausibilidade física para a regra A, derivado da própria distribuição do 32M.
- **O quantil usado está num só sítio** (`limiar_regra_a` em `10_flag_bots.sql`), por isso é fácil
  de mudar.

**Proposta, não implementada.** Neste momento, a deteção já corre dentro do passo `analises` (o
`05_analises.py` corre tudo o que está em `sql/analise/`). Proponho que **não** passe a ser um passo
próprio do pipeline, nem vá para `sql/10_flag_bots.sql`, enquanto não estiver validada com o Luís e
calibrada no 32M. Em `sql/` mudaria o benchmark da fase 1. Depois disso, um passo próprio só faz
sentido se outras análises dependerem da classificação, além de `eventos`.

### 13.6 Compatibilidade com o Athena: o que a emulação mostrou

- As 16 versões Athena, emuladas no DuckDB, dão resultados iguais às versões DuckDB no small e no 1M.
- **Como se emula:**
  - `SET integer_division = true` (no Trino, `bigint / bigint` é divisão inteira);
  - macros para `from_unixtime`, `date_format`, `sequence` e `approx_percentile`.
- **Problema encontrado e corrigido:** a emulação não reproduz a aritmética decimal do Trino. Pelas
  regras de tipos decimais do Trino, uma divisão com um literal decimal (`100.0 * x / y`,
  `count_if(...) * 1.0 / COUNT(*)`, `100.0 / (v + 100)`) dá um `decimal` com a escala do literal,
  isto é, 1 casa decimal. Em `filtros_eventos`, isso compararia 0,5 com o limite 0,51.
  - **Correção:** todas as versões Athena passaram a usar `CAST(... AS double)`.
  - **Prevenção:** o `05_analises.py --emular-athena` falha se encontrar um literal decimal numa
    conta.
  - **Atenção:** as propostas do **anexo B** (Q06, Q16 e Q21) ainda têm este padrão. Ficam
    substituídas pelos ficheiros de `sql/athena/analise/`.
- **A confirmar na primeira execução real:**
  - a janela `RANGE BETWEEN CURRENT ROW AND 599 FOLLOWING` em `10_flag_bots.sql` (se não for
    aceite, a alternativa é um self-join, indicada no cabeçalho);
  - `approx_percentile` é aproximado: pode mudar quem está exatamente no limiar;
  - as frações (`FILTER` e `CASE` dentro de agregados);
  - o CTAS de `flag_bots`.

### 13.7 Tabela final por query

| ID | Query | Estado | Ficheiro DuckDB | Ficheiro Athena | Validado em |
|---|---|---|---|---|---|
| Q01 | `generos` | fora (duplica) | `sql/01_generos.sql` (já existia) | `sql/athena/queries/01_generos.sql` (já existia) | — |
| Q02 | `filmes_genero` | fora (duplica) | `sql/02_filmes_por_genero.sql` (já existia) | `sql/athena/queries/02_…` (já existia) | — |
| Q03 | `utilizadores` | fora (duplica) | `sql/03_avaliacoes_por_utilizador.sql` (já existia) | `sql/athena/queries/03_…` (já existia) | — |
| Q04 | `distribuicao` | corrigida | `sql/analise/distribuicao.sql` | `sql/athena/analise/distribuicao.sql` | small, 1M |
| Q05 | `top10` | fora (duplica; desempate adotado em `sql/04`) | `sql/04_top_filmes.sql` | `sql/athena/queries/04_top_filmes.sql` (sem desempate) | small, 1M (`sql/04`) |
| Q06 | `ponderado` | integrada | `sql/analise/ponderado.sql` | `sql/athena/analise/ponderado.sql` | small, 1M |
| Q07 | `anual` | integrada | `sql/analise/anual.sql` | `sql/athena/analise/anual.sql` | small, 1M |
| Q08 | `valores_ano` | integrada | `sql/analise/valores_ano.sql` | `sql/athena/analise/valores_ano.sql` | small, 1M |
| Q09 | `qualidade` | integrada | `sql/analise/qualidade.sql` | `sql/athena/analise/qualidade.sql` | small, 1M |
| Q10 | `cobertura` | fora (duplica) | — (`eda_indicadores.csv`, `qualidade.sql`) | — | — |
| Q11 | `mensal` | corrigida | `sql/analise/mensal.sql` | `sql/athena/analise/mensal.sql` | small, 1M |
| Q12 | `integridade` | corrigida | `sql/analise/integridade.sql` | `sql/athena/analise/integridade.sql` | small, 1M |
| Q13 | `perfis_ativos` | corrigida | `sql/analise/perfis_ativos.sql` | `sql/athena/analise/perfis_ativos.sql` | small, 1M |
| Q14 | `perfis_cumulativos` | corrigida | `sql/analise/perfis_cumulativos.sql` | `sql/athena/analise/perfis_cumulativos.sql` | small, 1M |
| Q15 | `grupos_atividade` | corrigida | `sql/analise/grupos_atividade.sql` | `sql/athena/analise/grupos_atividade.sql` | small, 1M |
| Q16 | `utilizadores_sinalizados` | **substituída** (a validar com o Luís) | `sql/analise/10_flag_bots.sql` + `10_flag_bots_calibracao.sql` | idem em `sql/athena/analise/` (CTAS + calibração) | small, 1M |
| Q17 | `dias_filme` | fora (intermédia) | absorvida em `filtros_eventos.sql` e `eventos.sql` | idem | small, 1M |
| Q18 | `evolucao_filmes` | corrigida | `sql/analise/evolucao_filmes.sql` | `sql/athena/analise/evolucao_filmes.sql` | small, 1M (0 linhas no 1M) |
| Q19 | `eventos` (view) | fora (intermédia) | absorvida em `filtros_eventos.sql` e `eventos.sql` | idem | small, 1M |
| Q20 | `eventos` (participantes) | corrigida | `sql/analise/eventos.sql` | `sql/athena/analise/eventos.sql` | small, 1M |
| Q21 | `filtros` | corrigida | `sql/analise/filtros_eventos.sql` | `sql/athena/analise/filtros_eventos.sql` | small, 1M |
| Q22 | `filmes_ano` | corrigida | `sql/analise/filmes_ano.sql` | `sql/athena/analise/filmes_ano.sql` | small, 1M (0 linhas no 1M) |

"Validado em" quer dizer o seguinte:
- **DuckDB:** corrida com Parquet e com CSV, verificações do `05_analises.py` e comparação com o
  original.
- **Athena:** emulação no DuckDB, igual à versão DuckDB.
- **Nada foi executado no Athena. No 32M só o bloco 6 (13.8.2).**

### 13.8 Bloco 6: teste de coordenação entre contas

#### 13.8.1 1M

Script `scripts/06_coordenacao.py --dataset 1m` (20 permutações, ~2 s). Saídas em
`results/1m/bots_coordenacao/`. **A validar com o Luís.**

Depois do 32M, o script passou a testar também U ≥ 20 e a reportar Bonferroni e z. Voltei a
correr o 1M: as 18 comparações anteriores e as contas do top 10 ficaram iguais, U ≥ 20 dá 0 rajadas,
e nenhuma das 24 comparações passa o limiar corrigido (0,05/24 ≈ 0,0021; com 20 permutações o menor
valor-p possível é 0,048).

**Definição**
- Rajada: (filme, nota extrema, hora UTC) com ≥ U utilizadores distintos e |nota − média do
  filme| ≥ D. Notas 1 e 5 no 1M (0,5 e 5,0 no 32M). U ∈ {3, 5, 10}, D ∈ {1,5; 2}.
- A hora é a hora de relógio (`timestamp // 3600`), não uma janela deslizante.
- Linha de base: os timestamps são permutados dentro de cada filme (o filme mantém a atividade
  por hora; a ligação nota–momento é quebrada). 20 repetições com sementes 1..20.
- A permutação usa `hash(userId, movieId, semente)` em vez de `setseed` + `random()`: é
  equivalente, mas reprodutível com várias threads. Duas corridas deram CSV idênticos.
- Valor-p empírico = (1 + n.º de permutações ≥ real) / 21; o menor possível é 0,048.

**Real vs linha de base (notas 1 e 5 juntas)**

| U | D | Real | Média permutações | p95 | Valor-p |
|---:|---:|---:|---:|---:|---:|
| 3 | 1,5 | 87 | 73,1 | 84,4 | 0,095 |
| 3 | 2 | 20 | 14,8 | 20,3 | 0,143 |
| 5 | 1,5 | 3 | 2,0 | 3,1 | 0,429 |
| 5 | 2 | 2 | 0,35 | 1,05 | 0,095 |
| 10 | 1,5 / 2 | 0 | 0 | 0 | 1 |

- Nenhuma combinação fica abaixo de 0,05. A única no limite (nota 5, U ≥ 3, D ≥ 2: 3 reais
  contra 0,6) é uma de 18 comparações e assenta em 3 rajadas; não resiste a correção para
  comparações múltiplas. Tabela completa por nota em `teste.csv`.
- Não há nenhuma rajada com 10 ou mais utilizadores, real ou permutada.

**As 10 rajadas mais fortes** (`top10_rajadas.csv`, contas em `top10_contas.csv`)
- Todas em 20–21/11/2000, o pico de registos do 1M; 70 das 87 rajadas são desses dois dias.
- 7 utilizadores no máximo (Rocky Horror Picture Show, nota 5, 7 de 8 avaliações dessa hora).
- Contas: 45 presenças, 34 contas distintas; 98% estavam nas primeiras 24 h da conta
  (antiguidade mediana < 0,1 dias) e 49% voltaram a avaliar mais de 24 h depois.
- Contas grandes (mediana de 218 a 565 avaliações), nenhuma suspeita no bloco 5
  (37 "sem sinais", 8 "submissão em lote").
- Jaccard médio entre as contas de cada rajada: 0,08–0,24, contra 0,056 (p95 0,156) entre pares
  de contas quaisquer. É mais alto, mas é o esperado para contas grandes que se registaram no
  mesmo dia e viram o mesmo formulário de registo; não é, por si, sinal de coordenação.
- Nenhuma coincide com a "estreia" do filme no dataset (primeira avaliação 181–209 dias antes);
  os filmes são de 1975–1999.

**Leitura**: no 1M não há evidência de contas coordenadas. As rajadas reais são quase tantas como
as que a atividade dos filmes produz por acaso, e as mais fortes explicam-se pelo registo em massa
de novembro de 2000 (filmes de culto e polarizadores, como Rocky Horror e Blair Witch). O 32M,
com 200 mil contas e 25 anos, é onde o teste pode mostrar alguma coisa.

#### 13.8.2 32M

`python scripts/06_coordenacao.py --dataset 32m --repeticoes 200 --memoria 12GB`. Saídas em
`results/32m/bots_coordenacao/`. **A validar com o Luís.**

**Execução**
- Fonte Parquet, `SET memory_limit = '12GB'`, pasta temporária do DuckDB em `data/32m/duckdb_tmp/`
  (apagada no fim). Memória máxima do processo: ~6,3 GB.
- Medição prévia: 1 permutação = 2,4 s. Logo 200 permutações (~8 min previstos) ficavam abaixo dos
  30 min e correram as 200.
- Tempo total: 596,8 s (9,9 min); 2,98 s por permutação em média.

**Ajustes face ao 1M**
- Análise principal com 0,5 e 5,0. Sensibilidade com ≤ 1,0 (0,5 e 1,0 juntos) e 5,0; o lado 5,0
  é o mesmo e só conta uma vez.
- U ∈ {3, 5, 10, 20}, D ∈ {1,5; 2}. 5 conjuntos de notas × 8 limiares = 40 comparações.
- Bonferroni: 0,05/40 = 0,00125. Com 200 permutações o menor valor-p empírico é 1/201 = 0,005, por
  isso **nenhuma comparação pode passar o limiar corrigido**. Seriam precisas ≥ 800 permutações
  (~40 min ao ritmo medido). O z = (real − média)/desvio-padrão vai como informação complementar.

**A permutação troca timestamps, não reordena linhas** (verificado no código, semente 1)
- Cada avaliação de um filme recebe uma posição pela ordem de `hash(userId, movieId, semente)`, e a
  avaliação na posição k recebe o k-ésimo timestamp desse filme por ordem cronológica.
- Nos 84 432 filmes, o conjunto de timestamps (n.º, mínimo, máximo e soma dos hashes) e o conjunto
  de avaliações (utilizador, nota) ficam iguais; o script falha se não ficarem.
- 99,7% das avaliações ficam com outro timestamp e outra hora.
- Exemplo, filme 604 (6 avaliações, `verificacao_permutacao.csv`): os mesmos 6 timestamps, noutras
  avaliações.

| userId | Nota | Timestamp original | Timestamp permutado |
|---:|---:|---|---|
| 84603 | 1,0 | 1997-02-03 20:41:19 | 2002-04-07 14:01:01 |
| 92958 | 1,0 | 1997-05-06 14:53:11 | 1999-12-01 16:31:47 |
| 186566 | 1,0 | 1999-12-01 16:31:47 | 1997-05-06 14:53:11 |
| 1474 | 4,0 | 2000-01-31 23:33:34 | 2004-07-30 07:53:32 |
| 200493 | 4,0 | 2002-04-07 14:01:01 | 2000-01-31 23:33:34 |
| 27841 | 0,5 | 2004-07-30 07:53:32 | 1997-02-03 20:41:19 |

**Real vs linha de base (seleção; as 40 comparações estão em `teste.csv`)**

| Análise | Notas | U | D | Real | Média perm. | p95 | z | Valor-p |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| principal | 0,5 e 5,0 | 3 | 1,5 | 2 200 | 931,1 | 977,1 | 47,4 | 0,005 |
| principal | 0,5 e 5,0 | 5 | 2 | 19 | 2,9 | 5,0 | 11,7 | 0,005 |
| principal | 0,5 e 5,0 | 10 | 1,5 | 3 | 1,0 | 3,0 | 2,0 | 0,090 |
| principal | 0,5 | 5 | 1,5 | 15 | 0,7 | 2,0 | 17,1 | 0,005 |
| principal | 5,0 | 5 | 2 | 4 | 2,2 | 4,0 | 1,5 | 0,129 |
| sensibilidade | ≤ 1,0 | 3 | 1,5 | 841 | 593,7 | 635,1 | 10,6 | 0,005 |
| sensibilidade | ≤ 1,0 | 10 | 1,5 | 9 | 1,9 | 4,0 | 5,6 | 0,005 |
| sensibilidade | ≤ 1,0 | 20 | 1,5 | 1 | 0 | 0 | — | 0,005 |
| todas | todas | 20 | 2 | 0 | 0 | 0 | — | 1 |

- Em 25 das 40 comparações o real fica acima de todas as 200 permutações (valor-p 0,005, o mínimo).
  Nenhuma passa Bonferroni, pela resolução do teste, não por falta de excesso.
- Só uma rajada chega a 20 utilizadores (sensibilidade ≤ 1,0, D ≥ 1,5), e nenhuma a 20 com D ≥ 2.

**Rajadas por ano** (análise principal, U ≥ 3, D ≥ 1,5; `rajadas_por_ano.csv`)
- 1996: 1 253 reais contra 527 nas permutações (25 304 contas novas, o maior ano de registos).
- 1999–2000: 553 contra 151.
- Até 2002: 2 016 reais contra 729. **De 2003 em diante: 184 contra 202**, sem excesso; 2005 e 2008
  ficam até abaixo da linha de base.

**Porque é que o excesso não é coordenação**
- A escala de meias estrelas começa a 2003-02-18. Antes, 21,3% das avaliações eram 5,0; depois, 12,1%.
  O ≤ 1,0 passa de 5,2% para 4,4%.
- A permutação dentro do filme espalha as avaliações de antes de 2003 (com mais notas extremas) por
  todo o período do filme. Assim, a linha de base subestima as notas extremas nas horas de muita
  atividade antes de 2003, como o arranque em 1996 e 1999–2000.
- O excesso coincide exatamente com esse período e desaparece depois. É um efeito da mudança de
  escala, e mais em geral de a linha de base supor que a distribuição das notas não muda no tempo.
- Proposta (não implementada): permutar dentro de (filme, era antes/depois de 2003-02-18), ou
  dentro de (filme, ano), e repetir com ≥ 800 permutações para Bonferroni poder ser atingido.

**As 10 rajadas mais fortes** (análise principal; `top10_rajadas.csv`, `top10_contas.csv`)
- 94 presenças, 85 contas distintas. 82% estavam nas primeiras 24 h da conta e 28% voltaram a
  avaliar mais de 24 h depois.
- Nenhuma coincide com a "estreia" do filme no dataset (153 a 2 442 dias depois).
- Sem a coluna de suspeitos do bloco 5: o `10_flag_bots.csv` do 32M ainda não existe.
- Jaccard de referência entre pares de contas quaisquer: média 0,043, p95 0,130.
- Três grupos:
  - **26/11/1996, 05–06 h** (rajadas 2, 8, 9, 10: Mrs. Doubtfire, Pretty Woman, True Lies; nota 5).
    Contas novas com ~40–60 avaliações e Jaccard alto (médio 0,20–0,35, máximo 0,67). É o perfil
    de contas no formulário de registo de 1996, que mostrava os mesmos filmes populares.
  - **Registo, outras datas** (1: Honey, I Shrunk the Kids, 0,5 por 14 contas novas em 2005-03-22 06 h,
    63 avaliações do filme nessa hora; 3: Independence Day, 1997; 4 e 5: Blair Witch e Phantom
    Menace, 1999-12-11). Também contas no registo; Jaccard 0,07–0,31.
  - **22/05/1998, 12–14 h** (6: Body Snatchers; 7: Money Talks; nota 5). **O único caso com contas
    antigas**: antiguidade mediana de 354 e 157 dias, 0% no registo, 103 e 74 avaliações do filme
    nessa hora. Jaccard 0,11–0,16 (máximo 0,37). Não se explica pelo registo e é o caso a rever com
    o Luís (ex.: uma página ou funcionalidade do site nesse dia).

**Leitura**: no 32M, o teste com permutação simples dentro do filme mostra mais rajadas do que o
acaso, mas o excesso está todo antes de 2003 e explica-se pela mudança da escala de notas. Depois de
2003 as rajadas reais estão ao nível da linha de base. As mais fortes são, quase todas, contas no
registo. Não há evidência de coordenação; o único padrão por explicar é 22/05/1998.

### 13.9 Pendentes

**Validação pelo Luís**
- [ ] Deteção de bots (13.5):
  - as regras A e B;
  - o quantil da regra A (p99,9);
  - os valores da regra B (≥ 100 eventos, ≤ 2 s) e o limite de lote (10);
  - os sinais complementares;
  - a proposta de um mínimo de plausibilidade física, se a cauda no 32M for contínua.
- [ ] Um só conjunto de limites para os eventos (P7). Por agora ficam os do capítulo 9.
- [ ] As faixas de `grupos_atividade` e a opção "só anos completos" de `evolucao_filmes`.
- [ ] Qual notebook fica como oficial (P12). O notebook não foi alterado.
- [ ] Bloco 6 (13.8.2): a linha de base estratificada por era e as ≥ 800 permutações, e o caso de
  22/05/1998.

**Execução no 32M** (só com autorização)
- [ ] `python scripts/05_analises.py --dataset 32m --emular-athena`.
- [ ] Antes disso, decidir onde gravar `10_flag_bots.csv` do 32M: tem 200 948 linhas, dezenas de MB,
  e o `.gitignore` versiona `results/**/*.csv`.
- [ ] Calibrar a regra A no 32M (distribuição e sinalizados no p99, p99,5 e p99,9).

**Execução real no Athena**
- [ ] Um script (por exemplo `scripts/athena_analises.py`, ainda por criar) que corra
  `sql/athena/analise/` com as substituições de `athena_benchmark.py`, crie `flag_bots` por CTAS
  antes de `10_flag_bots_calibracao` e `eventos`, e compare com `results/<ds>/analises/`.
- [ ] Confirmar a janela `RANGE … 599 FOLLOWING`, `approx_percentile`, a aritmética decimal e o
  CTAS.

**Outros**
- [ ] O desempate por `movieId` em `sql/athena/queries/04_top_filmes.sql` não foi feito: fica para
  decidirem se a versão Athena deve acompanhar o `sql/04`.
- [ ] Figuras do `05_analises.py`: não foram feitas. Obrigavam a duplicar o estilo NOVA do
  `04_eda.py` ou a movê-lo para um módulo partilhado.
- [ ] Acrescentar `dados/` e `lab_resultados.zip` ao `.gitignore` (P12): não foi feito.
- [ ] Os CSV com somas de frações podem mudar no último dígito de uma corrida para a outra (13.1).
  Se isso incomodar no git, arredondar à escrita.

---

## Anexo A: versões DuckDB corrigidas (testadas no small)

Convenção: `${ratings}` = ratings com `year` em UTC; `${movies}` = filmes.

**Q12 `integridade`** (P5)

```sql
SELECT (SELECT COUNT(*) - COUNT(DISTINCT movieId) FROM ${movies}) AS ids_filmes_repetidos,
       (SELECT COUNT(*) FROM ${ratings} r WHERE NOT EXISTS
            (SELECT 1 FROM ${movies} m WHERE m.movieId = r.movieId)) AS ratings_sem_filme,
       (SELECT COUNT(DISTINCT r.movieId) FROM ${ratings} r WHERE NOT EXISTS
            (SELECT 1 FROM ${movies} m WHERE m.movieId = r.movieId)) AS filmes_sem_metadados,
       (SELECT COUNT(*) FROM ${movies} WHERE title IS NULL OR genres IS NULL) AS filmes_com_nulos
```

**Q15 `grupos_atividade`** (P1, P4)

```sql
WITH totais AS (SELECT userId, COUNT(*) AS total FROM ${ratings} GROUP BY userId),
     u AS (SELECT r.userId, r.year AS ano, AVG(r.rating) AS media_utilizador, COUNT(*) AS n
           FROM ${ratings} r GROUP BY r.userId, r.year),
     g AS (SELECT u.*, CASE WHEN t.total <= 35 THEN '20–35' WHEN t.total <= 70 THEN '36–70'
                            WHEN t.total <= 200 THEN '71–200' ELSE 'Mais de 200' END AS grupo
           FROM u JOIN totais t USING (userId))
SELECT ano, grupo, AVG(media_utilizador) AS media, COUNT(*) AS utilizadores, SUM(n) AS avaliacoes
FROM g GROUP BY ano, grupo ORDER BY ano, grupo
```

**Q16 `utilizadores_sinalizados`** (P2), para `sql/10_flag_bots.sql`

```sql
WITH primeira AS (SELECT userId, MIN(timestamp) AS t0 FROM ${ratings} GROUP BY userId),
     apos AS (SELECT r.* FROM ${ratings} r JOIN primeira p USING (userId)
              WHERE r.timestamp >= p.t0 + 86400),   -- ignora as primeiras 24 h (registo)
     h AS (SELECT userId, timestamp // 3600 AS hora, COUNT(*) AS n FROM apos GROUP BY userId, hora),
     s AS (SELECT userId, timestamp, COUNT(*) AS n FROM apos GROUP BY userId, timestamp),
     p AS (SELECT userId, MAX(n) AS max_hora FROM h GROUP BY userId),
     q AS (SELECT userId, MAX(n) AS max_segundo FROM s GROUP BY userId),
     u AS (SELECT userId, COUNT(*) AS n, COUNT(DISTINCT rating) AS valores,
                  AVG(CASE WHEN rating <= 1 THEN 1.0 ELSE 0.0 END) AS frac_baixas,
                  AVG(CASE WHEN rating >= 4.5 THEN 1.0 ELSE 0.0 END) AS frac_altas
           FROM ${ratings} GROUP BY userId),
     f AS (SELECT u.*, COALESCE(p.max_hora, 0) AS max_hora, COALESCE(q.max_segundo, 0) AS max_segundo
           FROM u LEFT JOIN p USING (userId) LEFT JOIN q USING (userId))
SELECT *,
       CASE WHEN max_hora >= 50 AND max_hora * 1.0 / n >= 0.5 THEN 1 ELSE 0 END AS atividade_concentrada,
       CASE WHEN max_segundo >= 10 THEN 1 ELSE 0 END AS mesmo_segundo,
       CASE WHEN n >= 20 AND valores = 1 THEN 1 ELSE 0 END AS valor_unico,
       CASE WHEN n >= 20 AND frac_baixas >= 0.8 THEN 1 ELSE 0 END AS sobretudo_baixas,
       CASE WHEN n >= 20 AND frac_altas >= 0.8 THEN 1 ELSE 0 END AS sobretudo_altas
FROM f ORDER BY userId
```

Resultado no small: 21 sinalizados (12 / 0 / 1 / 0 / 9), contra 210 na versão original.

**Q18 `evolucao_filmes`** (P1, P3)

```sql
WITH fim AS (SELECT CASE WHEN month(epoch_ms(MAX(timestamp) * 1000)) = 12
                         THEN MAX(year) ELSE MAX(year) - 1 END AS ano FROM ${ratings}),
     s AS (SELECT r.movieId,
                  COUNT(*) FILTER (WHERE r.year BETWEEN f.ano - 9 AND f.ano - 5) AS n_anterior,
                  COUNT(*) FILTER (WHERE r.year BETWEEN f.ano - 4 AND f.ano) AS n_recente,
                  AVG(r.rating) FILTER (WHERE r.year BETWEEN f.ano - 9 AND f.ano - 5) AS media_anterior,
                  AVG(r.rating) FILTER (WHERE r.year BETWEEN f.ano - 4 AND f.ano) AS media_recente
           FROM ${ratings} r CROSS JOIN fim f
           WHERE r.year BETWEEN f.ano - 9 AND f.ano
           GROUP BY r.movieId),
     e AS (SELECT *, media_recente - media_anterior AS variacao,
                  RANK() OVER (ORDER BY media_anterior DESC) AS posicao_anterior,
                  RANK() OVER (ORDER BY media_recente DESC) AS posicao_recente
           FROM s WHERE n_anterior >= 10 AND n_recente >= 10)
SELECT e.*, m.title FROM e JOIN ${movies} m USING (movieId) ORDER BY variacao DESC, movieId
```

Resultado no small: 366 filmes (2008–2012 contra 2013–2017), contra 300 na original (2009–2013 contra
2014–2018 incompleto).

## Anexo B: versões Athena propostas (emuladas no DuckDB, não executadas no Athena)

Convenção do `athena_benchmark.py`: `${ratings}` é `ratings_part`, ou
`(SELECT x.*, year(from_unixtime(x."timestamp")) AS year FROM ratings AS x)` nas tabelas sem partição;
`${movies}` é `movies`.

**Q06 `ponderado`**

```sql
WITH s AS (SELECT r.movieid, AVG(r.rating) AS media_filme, COUNT(*) AS v FROM ${ratings} AS r GROUP BY r.movieid),
     p AS (SELECT AVG(r.rating) AS media_global FROM ${ratings} AS r)
SELECT s.movieid, m.title, s.media_filme AS avg_rating, s.v AS num_ratings,
       CAST(s.v AS double) / (s.v + 100) * s.media_filme
         + 100.0 / (s.v + 100) * p.media_global AS weighted
FROM s CROSS JOIN p JOIN ${movies} AS m ON s.movieid = m.movieid
ORDER BY weighted DESC, s.movieid
LIMIT 10
```

**Q07 `anual`** e **Q08 `valores_ano`**

```sql
SELECT r.year AS ano, COUNT(*) AS num_ratings, AVG(r.rating) AS media, COUNT(DISTINCT r.userid) AS utilizadores
FROM ${ratings} AS r GROUP BY r.year ORDER BY r.year

SELECT r.year AS ano, r.rating, COUNT(*) AS num_ratings
FROM ${ratings} AS r GROUP BY r.year, r.rating ORDER BY r.year, r.rating
```

**Q09 `qualidade`**

```sql
SELECT COUNT(*) AS linhas, COUNT(DISTINCT r.userid) AS utilizadores, COUNT(DISTINCT r.movieid) AS filmes,
       COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT d.userid, d.movieid FROM ${ratings} AS d) AS pares) AS pares_repetidos,
       count_if(r.userid IS NULL OR r.movieid IS NULL OR r.rating IS NULL OR r."timestamp" IS NULL) AS linhas_com_nulos,
       count_if(r.rating < 0.5 OR r.rating > 5 OR r.rating * 2 <> floor(r.rating * 2)) AS fora_dominio_comum,
       count_if(r.rating <> floor(r.rating)) AS nao_inteiros,
       count_if(r.rating < 1) AS inferior_a_um
FROM ${ratings} AS r
```

**Q11 `mensal`**

```sql
SELECT date_format(from_unixtime(r."timestamp"), '%Y-%m') AS mes, COUNT(*) AS num_ratings, AVG(r.rating) AS media
FROM ${ratings} AS r GROUP BY 1 ORDER BY 1
```

**Q12 `integridade`**

```sql
SELECT (SELECT COUNT(*) - COUNT(DISTINCT m.movieid) FROM ${movies} AS m) AS ids_filmes_repetidos,
       (SELECT COUNT(*) FROM ${ratings} AS r WHERE NOT EXISTS
            (SELECT 1 FROM ${movies} AS m WHERE m.movieid = r.movieid)) AS ratings_sem_filme,
       (SELECT COUNT(DISTINCT r.movieid) FROM ${ratings} AS r WHERE NOT EXISTS
            (SELECT 1 FROM ${movies} AS m WHERE m.movieid = r.movieid)) AS filmes_sem_metadados,
       (SELECT COUNT(*) FROM ${movies} AS m WHERE m.title IS NULL OR m.genres IS NULL) AS filmes_com_nulos
```

**Q13 `perfis_ativos`**

```sql
WITH y AS (SELECT r.userid, r.year AS ano, COUNT(*) AS n,
                  count_if(r.rating = floor(r.rating)) AS inteiros,
                  count_if(r.rating <> floor(r.rating)) AS nao_inteiros
           FROM ${ratings} AS r GROUP BY r.userid, r.year),
     c AS (SELECT ano,
                  SUM(n) OVER (PARTITION BY userid ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS total,
                  SUM(inteiros) OVER (PARTITION BY userid ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS i,
                  SUM(nao_inteiros) OVER (PARTITION BY userid ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ni
           FROM y)
SELECT ano, CASE WHEN ni = 0 THEN 'Só inteiros' WHEN i = 0 THEN 'Só não inteiros' ELSE 'Misto' END AS perfil,
       COUNT(*) AS utilizadores
FROM c WHERE total >= 2 GROUP BY 1, 2 ORDER BY 1, 2
```

**Q14 `perfis_cumulativos`**

```sql
WITH limites AS (SELECT MIN(r.year) AS a, MAX(r.year) AS b FROM ${ratings} AS r),
     anos AS (SELECT t.ano FROM limites CROSS JOIN UNNEST(sequence(a, b)) AS t(ano)),
     y AS (SELECT r.userid, r.year AS ano, count_if(r.rating = floor(r.rating)) AS i,
                  count_if(r.rating <> floor(r.rating)) AS ni
           FROM ${ratings} AS r GROUP BY r.userid, r.year),
     grelha AS (SELECT u.userid, a.ano, COALESCE(y.i, 0) AS i, COALESCE(y.ni, 0) AS ni
                FROM (SELECT DISTINCT r.userid FROM ${ratings} AS r) AS u CROSS JOIN anos AS a
                LEFT JOIN y ON u.userid = y.userid AND a.ano = y.ano),
     c AS (SELECT ano,
                  SUM(i) OVER (PARTITION BY userid ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS i,
                  SUM(ni) OVER (PARTITION BY userid ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ni
           FROM grelha)
SELECT ano, CASE WHEN ni = 0 THEN 'Só inteiros' WHEN i = 0 THEN 'Só não inteiros' ELSE 'Misto' END AS perfil,
       COUNT(*) AS utilizadores
FROM c WHERE i + ni >= 2 GROUP BY 1, 2 ORDER BY 1, 2
```

**Q15 `grupos_atividade`**

```sql
WITH totais AS (SELECT r.userid, COUNT(*) AS total FROM ${ratings} AS r GROUP BY r.userid),
     u AS (SELECT r.userid, r.year AS ano, AVG(r.rating) AS media_utilizador, COUNT(*) AS n
           FROM ${ratings} AS r GROUP BY r.userid, r.year),
     g AS (SELECT u.ano, u.media_utilizador, u.n,
                  CASE WHEN t.total <= 35 THEN '20–35' WHEN t.total <= 70 THEN '36–70'
                       WHEN t.total <= 200 THEN '71–200' ELSE 'Mais de 200' END AS grupo
           FROM u JOIN totais AS t ON u.userid = t.userid)
SELECT ano, grupo, AVG(media_utilizador) AS media, COUNT(*) AS utilizadores, SUM(n) AS avaliacoes
FROM g GROUP BY ano, grupo ORDER BY ano, grupo
```

**Q16 `sinais_resumo`** (devolve 1 linha; a tabela por utilizador fica para CTAS, se for precisa)

```sql
WITH primeira AS (SELECT r.userid, MIN(r."timestamp") AS t0 FROM ${ratings} AS r GROUP BY r.userid),
     apos AS (SELECT r.userid, r."timestamp" AS ts FROM ${ratings} AS r JOIN primeira AS p ON r.userid = p.userid
              WHERE r."timestamp" >= p.t0 + 86400),
     h AS (SELECT userid, ts / 3600 AS hora, COUNT(*) AS n FROM apos GROUP BY 1, 2),
     s AS (SELECT userid, ts, COUNT(*) AS n FROM apos GROUP BY 1, 2),
     p AS (SELECT userid, MAX(n) AS max_hora FROM h GROUP BY userid),
     q AS (SELECT userid, MAX(n) AS max_segundo FROM s GROUP BY userid),
     u AS (SELECT r.userid, COUNT(*) AS n, COUNT(DISTINCT r.rating) AS valores,
                  count_if(r.rating <= 1) * 1.0 / COUNT(*) AS frac_baixas,
                  count_if(r.rating >= 4.5) * 1.0 / COUNT(*) AS frac_altas
           FROM ${ratings} AS r GROUP BY r.userid),
     f AS (SELECT u.userid,
                  IF(COALESCE(p.max_hora, 0) >= 50 AND COALESCE(p.max_hora, 0) * 1.0 / u.n >= 0.5, 1, 0) AS atividade_concentrada,
                  IF(COALESCE(q.max_segundo, 0) >= 10, 1, 0) AS mesmo_segundo,
                  IF(u.n >= 20 AND u.valores = 1, 1, 0) AS valor_unico,
                  IF(u.n >= 20 AND u.frac_baixas >= 0.8, 1, 0) AS sobretudo_baixas,
                  IF(u.n >= 20 AND u.frac_altas >= 0.8, 1, 0) AS sobretudo_altas
           FROM u LEFT JOIN p ON u.userid = p.userid LEFT JOIN q ON u.userid = q.userid)
SELECT COUNT(*) AS utilizadores,
       SUM(atividade_concentrada) AS atividade_concentrada, SUM(mesmo_segundo) AS mesmo_segundo,
       SUM(valor_unico) AS valor_unico, SUM(sobretudo_baixas) AS sobretudo_baixas, SUM(sobretudo_altas) AS sobretudo_altas,
       count_if(atividade_concentrada + mesmo_segundo + valor_unico + sobretudo_baixas + sobretudo_altas > 0) AS sinalizados
FROM f
```

**Q21 `filtros_eventos`** (absorve Q17 e não devolve a tabela filme × dia)

```sql
WITH d AS (SELECT r.movieid, r."timestamp" / 86400 AS dia, COUNT(*) AS n, COUNT(DISTINCT r.userid) AS utilizadores,
                  SUM(r.rating) AS soma, AVG(r.rating) AS media,
                  count_if(r.rating <= 2) * 1.0 / COUNT(*) AS frac_baixas,
                  count_if(r.rating >= 4) * 1.0 / COUNT(*) AS frac_altas
           FROM ${ratings} AS r GROUP BY 1, 2),
     h AS (SELECT d.*,
                  SUM(n) OVER (PARTITION BY movieid ORDER BY dia ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - n AS n_anterior,
                  SUM(soma) OVER (PARTITION BY movieid ORDER BY dia ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - soma AS soma_anterior
           FROM d),
     v AS (SELECT h.*, media - soma_anterior / NULLIF(n_anterior, 0) AS variacao FROM h)
SELECT COUNT(*) AS todos_filme_dia,
       count_if(n_anterior >= 5) AS com_historico,
       count_if(n_anterior >= 5 AND utilizadores >= 5) AS com_utilizadores,
       count_if(n_anterior >= 5 AND utilizadores >= 5 AND (frac_baixas >= 0.51 OR frac_altas >= 0.51)) AS com_extremos,
       count_if(n_anterior >= 5 AND utilizadores >= 5
                AND ((frac_baixas >= 0.51 AND variacao <= -0.5) OR (frac_altas >= 0.51 AND variacao >= 0.5))) AS eventos
FROM v
```

Resultado emulado no small: 99 538 / 70 858 / 0 / 0 / 0, igual ao do notebook.
