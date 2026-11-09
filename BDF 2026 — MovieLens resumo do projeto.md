# BDF 2026 — MovieLens: resumo do projeto

Nov 8, 2026 · @Tiago Felgueira

## Visão geral

O pipeline local está completo e testado no small, no 1M e no 32M. A parte cloud (S3 → Glue → Athena) já correu no small e no 32M, e nada está ainda integrado no `main`.

O projeto é a case analysis MovieLens da cadeira Big Data Foundations (NOVA IMS 2026). O objetivo é mostrar um pipeline reprodutível que escala de 100 mil para 32 milhões de avaliações, com evidência de desempenho (CSV vs Parquet vs Parquet particionado, DuckDB local vs Athena).

| Dataset | Avaliações | Utilizadores | Filmes no catálogo | Período | Formato original |
| --- | --: | --: | --: | --- | --- |
| small (ml-latest-small) | 100 836 | 610 | 9 742 | 1996–2018 | CSV com cabeçalho |
| 1M (ml-1m) | 1 000 209 | 6 040 | 3 883 | 2000–2003 | `.dat`, separador `::`, latin-1, sem tags |
| 32M (ml-32m) | 32 000 204 | 200 948 | 87 585 | 1995–2023 | CSV com cabeçalho |

| Fase | O que entrega | Estado |
| --- | --- | --- |
| 0. Limpeza | `.gitignore`, README, remoção de `.DS_Store` | Concluída |
| 1. Pipeline local | Ingestão, Parquet, 5 queries com benchmark, EDA | Concluída nos 3 datasets |
| 2. Preparação cloud | Ficheiros para o S3, DDL do Glue, queries em Trino, benchmark | Executada no small e no 32M (8/11/2026) |
| 3. Queries do Luís | 16 análises revistas (DuckDB e Athena) | Validadas no small e no 1M; 32M por correr |
| 4. Bots e coordenação | Regras A/B de bots; teste de rajadas | Bots no small e 1M; coordenação no 1M e 32M |

Grupo: Tiago, Luís (análise e regras de bots), José e Francisco. Repositório `j3grave/BDF`; o branch que contém tudo é `integracao-queries-luis` (HEAD `cbd7cb1`).

&#91;embedded content: pipeline do projeto · fase 1 local e fase 2 cloud\]

O Parquet gerado no passo 2 alimenta tudo o resto: os quatro passos de análise locais e a preparação para a cloud.

## Estrutura do repositório e como correr

Um único comando corre os 5 passos do pipeline local: `python run_pipeline.py --dataset small` (ou `1m`, `32m`). Cada passo corre num processo separado, pára o pipeline se falhar e regista o tempo em `results/pipeline_runs.csv`.

| # | Passo (`--steps`) | Script | Input principal | Output principal |
| --- | --- | --- | --- | --- |
| 1 | `ingest` | `scripts/01_ingest.py` | zip do GroupLens | `data/<ds>/csv/*.csv` |
| 2 | `parquet` | `scripts/02_to_parquet.py` | `data/<ds>/csv/` | `data/<ds>/parquet/`, `results/sizes.csv` |
| 3 | `benchmark` | `scripts/03_benchmark.py` | `sql/*.sql` + Parquet | `results/benchmarks.csv` |
| 4 | `eda` | `scripts/04_eda.py` | Parquet (ou CSV) | `results/<ds>/eda/` |
| 5 | `analises` | `scripts/05_analises.py` | `sql/analise/*.sql` + Parquet | `results/<ds>/analises/` |

Correm à mão, fora do pipeline: `06_coordenacao.py` (coordenação entre contas), `prepare_cloud.py`, `athena_setup.py` e `athena_benchmark.py` (fase cloud).

Pastas principais:

- `scripts/`: os passos numerados e os módulos partilhados `common.py` (datasets, esquemas, caminhos, `config.yaml`) e `athena_common.py` (opções AWS, cliente boto3).
- `sql/`: as 5 queries do benchmark; `sql/analise/` com as 16 análises em DuckDB; `sql/athena/` com as versões Trino (`queries/`, `analise/`) e o DDL (`ddl/`); `sql/cloud/` com a query de partition pruning.
- `results/`: CSV de tamanhos, tempos e benchmarks, e uma pasta por dataset com EDA, análises e coordenação. Os resultados leves estão versionados; os dados não.
- `data/<ds>/{raw,csv,parquet}`: não versionado; no Mac é um symlink para `~/Desktop/Nova IMS 2 Semestre/BDF/data/`.
- `reports/`: manifestos da preparação cloud. `docs/validacao_queries_colega.md`: relatório de validação das queries do Luís.
- Três notebooks do lab na raiz, não alterados pelo pipeline.

`config.yaml` define o dataset por omissão (`small`), as pastas `data/` e `results/` e a secção `aws` (região `us-east-1`, workgroup `primary`, buckets ainda a `null`). Requer Python ≥ 3.10 (testado em 3.13) e um venv com o `requirements.txt`.

## Fase 1 — Ingestão e conversão para Parquet

Os passos 1 e 2 põem os três datasets no mesmo esquema e convertem-nos para Parquet: no 32M, o `ratings` passa de 877 MB em CSV para 218 MB em Parquet (−75%).

### Passo 1 — `01_ingest.py`

- **O que faz:** descarrega o zip do GroupLens (só se ainda não existir) e normaliza todas as tabelas para CSV UTF-8 com cabeçalho e o esquema comum: `ratings(userId, movieId, rating, timestamp)`, `movies(movieId, title, genres)`, `tags`, `links`. O small e o 32M só são extraídos; o 1M (`.dat`, separador `::`, sem cabeçalho, `movies.dat` em latin-1) é convertido com o DuckDB.
- **Input:** URL do GroupLens → `data/<ds>/raw/<pasta>.zip`.
- **Output:** `data/<ds>/csv/ratings.csv`, `movies.csv`, e `tags.csv` e `links.csv` (small e 32M); imprime o n.º de linhas de cada CSV. No 32M, os 32 000 204 ratings batem com a contagem oficial.
- **Comando:** `python scripts/01_ingest.py --dataset small`

### Passo 2 — `02_to_parquet.py`

- **O que faz:** converte cada CSV em Parquet com `COPY` do DuckDB (em streaming, sem pandas, compressão snappy) e cria uma segunda versão de `ratings` particionada por ano (`PARTITION_BY year`, com o ano em UTC derivado do `timestamp`). Regista tamanhos e tempos.
- **Input:** `data/<ds>/csv/*.csv`.
- **Output:** `data/<ds>/parquet/<tabela>.parquet`, `data/<ds>/parquet/ratings_by_year/year=AAAA/` e uma linha por tabela em `results/sizes.csv`.
- **Comando:** `python scripts/02_to_parquet.py --dataset small`

A lógica do passo 2, em SQL DuckDB (simplificada):

```sql
COPY (SELECT * FROM read_csv_auto('data/<ds>/csv/ratings.csv'))
  TO 'data/<ds>/parquet/ratings.parquet' (FORMAT PARQUET, COMPRESSION SNAPPY);

COPY (SELECT *, year(epoch_ms(timestamp * 1000)) AS year
      FROM read_csv_auto('data/<ds>/csv/ratings.csv'))
  TO 'data/<ds>/parquet/ratings_by_year' (FORMAT PARQUET, PARTITION_BY (year));
```

**Resultados (tamanhos em MB do `ratings`):**

| Dataset | CSV | Parquet | Parquet por ano | Partições | Conversão |
| --- | --: | --: | --: | --: | --- |
| small | 2,48 | 0,69 | 0,77 | 23 | 0,02 s |
| 1M | 23,59 | 5,21 | 5,25 | 4 | 0,05 s |
| 32M | 877,08 | 217,68 | 214,04 | 29 | não registado |

O 32M foi ingerido e convertido noutra cópia do repositório, por isso não tem linhas no `sizes.csv`; os tamanhos vêm de `reports/cloud_manifest_32m.md`. No small e no 1M o Parquet particionado é ligeiramente maior do que o único, porque cada partição repete os metadados do ficheiro.

## Fase 1 — Queries SQL e benchmark

No 32M, a partição por ano reduz a query temporal de 0,074 s para 0,013 s (5,7× mais rápida); nas queries que leem todos os anos não faz diferença.

### Passo 3 — `03_benchmark.py`

- **O que faz:** corre cada `sql/0X_*.sql` 3 vezes sobre o Parquet sem partição e sobre o particionado por ano e guarda a mediana do tempo e o n.º de linhas. Os marcadores `${ratings}` e `${movies}` são substituídos pela leitura do Parquet. Não guarda o resultado das queries.
- **Input:** `sql/*.sql` e `data/<ds>/parquet/`.
- **Output:** linhas em `results/benchmarks.csv` (dataset, query, formato, mediana em segundos, n.º de linhas).
- **Comando:** `python scripts/03_benchmark.py --dataset small`

As 4 primeiras queries vêm da secção 7 do notebook do lab; a 05 foi acrescentada para testar as partições. O `sql/10_flag_bots.sql` é só um esqueleto comentado e é ignorado (as regras reais estão em `sql/analise/`).

**01\_generos.sql** — que géneros existem? Só lê a coluna `genres` (projection pushdown).

```sql
SELECT DISTINCT genre
FROM (SELECT unnest(string_split(genres, '|')) AS genre FROM ${movies})
ORDER BY genre;
```

**02\_filmes\_por\_genero.sql** — quantos filmes por género, e em que percentagem do catálogo? Um filme pode ter vários géneros.

```sql
WITH movie_genre AS (
    SELECT movieId, unnest(string_split(genres, '|')) AS genre
    FROM ${movies}
)
SELECT genre,
       COUNT(*)                                                      AS num_movies,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ${movies}), 1) AS pct_movies
FROM movie_genre
GROUP BY genre
ORDER BY num_movies DESC, genre;
```

**03\_avaliacoes\_por\_utilizador.sql** — distribuição das avaliações por utilizador (n.º, média, desvio, mínimo, mediana, máximo).

```sql
SELECT userId,
       COUNT(*)                      AS num_ratings,
       ROUND(AVG(rating), 3)         AS mean,
       ROUND(STDDEV_SAMP(rating), 3) AS std,
       MIN(rating)                   AS min,
       MEDIAN(rating)                AS median,
       MAX(rating)                   AS max
FROM ${ratings}
GROUP BY userId
ORDER BY userId;
```

**04\_top\_filmes.sql** — top 10 filmes por média, com pelo menos 100 avaliações (`HAVING` filtra depois de agregar); empate desfeito pelo `movieId`.

```sql
SELECT m.title, ROUND(AVG(r.rating), 2) AS avg_rating, COUNT(*) AS num_ratings
FROM ${ratings} r
JOIN ${movies} m USING (movieId)
GROUP BY m.movieId, m.title
HAVING COUNT(*) >= 100
ORDER BY AVG(r.rating) DESC, m.movieId
LIMIT 10;
```

**05\_ratings\_por\_ano.sql** — n.º de avaliações e média por ano. No Parquet particionado o `year` vem do nome da pasta e o `timestamp` nem é lido.

```sql
SELECT year,
       COUNT(*)              AS num_ratings,
       ROUND(AVG(rating), 3) AS avg_rating
FROM ${ratings}
GROUP BY year
ORDER BY year;
```

**Resultados (mediana de 3 corridas, em segundos; Parquet sem partição / particionado por ano):**

| Query | Linhas (small · 1M · 32M) | small | 1M | 32M |
| --- | --- | --- | --- | --- |
| 01\_generos | 20 · 18 · 20 | 0,0009 / 0,0008 | 0,0006 / 0,0006 | 0,0026 / 0,0025 |
| 02\_filmes\_por\_genero | 20 · 18 · 20 | 0,0012 / 0,0010 | 0,0009 / 0,0008 | 0,0027 / 0,0027 |
| 03\_avaliacoes\_por\_utilizador | 610 · 6 040 · 200 948 | 0,0068 / 0,0025 | 0,0094 / 0,0101 | 0,2524 / 0,2545 |
| 04\_top\_filmes | 10 · 10 · 10 | 0,0064 / 0,0045 | 0,0066 / 0,0060 | 0,1253 / 0,1259 |
| 05\_ratings\_por\_ano | 23 · 4 · 29 | 0,0023 / 0,0014 | 0,0052 / 0,0010 | 0,0735 / 0,0130 |

Corridas de 1/11/2026 (small e 1M às 17h46, 32M às 21h17); uma segunda corrida do small a 5/11 deu valores equivalentes.

## Fase 1 — Análise exploratória (EDA)

A atividade está muito concentrada: no 32M, 10% dos utilizadores fazem 47% das avaliações e 10% dos filmes recebem 96% (Gini 0,95). A matriz utilizador × filme está 99,8% vazia.

### Passo 4 — `04_eda.py`

- **O que faz:** calcula indicadores-chave (volume, esparsidade, distribuição das notas, concentração e Gini, anos, géneros, tags), um resumo de qualidade por tabela e 10 figuras com a paleta NOVA IMS. Todas as agregações são feitas no DuckDB e só os resultados agregados passam para Python, por isso corre no 32M sem carregar os dados em memória.
- **Input:** `data/<ds>/parquet/<tabela>.parquet` (ou os CSV, com `--fonte csv`).
- **Output:** `results/<ds>/eda/`: figuras `01_…png` a `10_…png`, `eda_indicadores.csv`, `eda_resumo_tabelas.csv` (linhas, nulos e distintos por coluna) e `eda_relatorio.md`. O 1M não tem a figura 09 (não tem tags); são 29 PNG no total.
- **Comando:** `python scripts/04_eda.py --dataset 32m --fonte parquet`

**Queries principais do EDA (DuckDB):**

```sql
-- Fig. 01: distribuição das notas e estatísticas
SELECT rating, COUNT(*) AS n FROM ratings GROUP BY rating ORDER BY rating;
SELECT AVG(rating), MEDIAN(rating), STDDEV(rating), MODE(rating) FROM ratings;

-- Fig. 02-04: atividade por utilizador e por filme (base do Gini e da cauda longa)
SELECT userId,  COUNT(*) AS n FROM ratings GROUP BY userId;
SELECT movieId, COUNT(*) AS n FROM ratings GROUP BY movieId ORDER BY n DESC;

-- Fig. 05: evolução temporal
SELECT year(to_timestamp(timestamp)) AS ano, COUNT(*) AS n,
       AVG(rating) AS media, COUNT(DISTINCT userId) AS utilizadores
FROM ratings GROUP BY ano ORDER BY ano;

-- Fig. 06: filmes, avaliações e média por género
WITH g AS (SELECT movieId, unnest(string_split(genres, '|')) AS genero FROM movies),
     r AS (SELECT movieId, COUNT(*) AS n, AVG(rating) AS media FROM ratings GROUP BY movieId)
SELECT genero, COUNT(DISTINCT g.movieId) AS filmes,
       SUM(r.n) AS avaliacoes, SUM(r.media * r.n) / SUM(r.n) AS media
FROM g LEFT JOIN r USING (movieId)
GROUP BY genero ORDER BY filmes;

-- Fig. 07: ano de lançamento extraído do título
SELECT TRY_CAST(regexp_extract(trim(title), '\((\d{4})\)\s*$', 1) AS INTEGER) AS ano,
       COUNT(*) AS n
FROM movies GROUP BY ano ORDER BY ano;

-- Fig. 08: heatmap média por género x ano
WITH g AS (SELECT movieId, unnest(string_split(genres, '|')) AS genero FROM movies)
SELECT genero, year(to_timestamp(r.timestamp)) AS ano, AVG(r.rating) AS media
FROM ratings r JOIN g USING (movieId)
WHERE genero <> '(no genres listed)'
GROUP BY genero, ano;

-- Fig. 09: top 20 tags
SELECT lower(trim(tag)) AS tag, COUNT(*) AS n, COUNT(DISTINCT userId) AS users
FROM tags GROUP BY 1 ORDER BY n DESC LIMIT 20;
```

O Gini e os percentis são calculados em Python sobre as contagens agregadas. A figura 10 é um painel-resumo em formato de slide.

**Indicadores-chave (`eda_indicadores.csv`):**

| Indicador | small | 1M | 32M |
| --- | --: | --: | --: |
| Filmes avaliados / no catálogo | 9 724 / 9 742 | 3 706 / 3 883 | 84 432 / 87 585 |
| Esparsidade da matriz | 98,3% | 95,5% | 99,8% |
| Média / mediana / moda das notas | 3,50 / 3,5 / 4,0 | 3,58 / 4,0 / 4,0 | 3,54 / 3,5 / 4,0 |
| Desvio-padrão das notas | 1,04 | 1,12 | 1,06 |
| Avaliações por utilizador: mediana / máx. | 70,5 / 2 698 | 96 / 2 314 | 73 / 33 332 |
| Gini dos utilizadores | 0,60 | 0,53 | 0,59 |
| % avaliações do top 10% utilizadores | 47,7% | 38,1% | 47,2% |
| Avaliações por filme: mediana / máx. | 3 / 329 | 123,5 / 3 428 | 5 / 102 929 |
| Gini dos filmes | 0,72 | 0,63 | 0,95 |
| % avaliações do top 10% filmes | 60,0% | 44,4% | 95,7% |
| Filmes sem ano no título | 13 | 0 | 617 |
| Tags: total / utilizadores / filmes | 3 683 / 58 / 1 572 | — | 2 000 072 / 15 848 / 51 323 |

Todos os utilizadores têm pelo menos 20 avaliações (critério de seleção do GroupLens). O 1M é atípico: só cobre 2000–2003 e só usa estrelas inteiras.

## Fase 3 — Análises do Luís (passo 5)

As 16 queries do notebook do Luís foram revistas, corrigidas e passadas para ficheiros `.sql` em DuckDB e em Athena; correm sem erros no small e no 1M e as duas versões dão o mesmo n.º de linhas.

### Passo 5 — `05_analises.py`

- **O que faz:** corre as queries de `sql/analise/` (vindas das células 108, 109 e 112 do notebook `_v1_3`) e grava cada resultado em CSV com `COPY`. Corre primeiro `10_flag_bots.sql` e guarda-a como tabela temporária `${flag_bots}`, usada por outras queries. Faz o pipeline falhar se houver nulos, notas fora da escala, filmes sem metadados, contagens diferentes das do EDA, soma anual diferente do total ou se os utilizadores de referência dos bots não forem classificados como esperado.
- **Input:** `sql/analise/*.sql`, `data/<ds>/parquet/`, `results/<ds>/eda/eda_indicadores.csv`; com `--emular-athena`, também `sql/athena/analise/*.sql`.
- **Output:** `results/<ds>/analises/<query>.csv`, `analises_resumo.csv`, `analises_relatorio.md`; com `--emular-athena`, `athena_emulado/<query>.csv` e `athena_emulado/comparacao.csv`.
- **Comando:** `python scripts/05_analises.py --dataset small --emular-athena`

| Query (`sql/analise/`) | Pergunta | Linhas small · 1M | Resultado em destaque |
| --- | --- | --- | --- |
| `qualidade` | Nulos, notas fora da escala, pares repetidos? | 1 · 1 | 0 nulos, 0 fora da escala, 0 repetidos; 30 398 meias estrelas no small, 0 no 1M |
| `integridade` | IDs repetidos em movies, ratings sem filme? | 1 · 1 | Tudo a 0 nos dois |
| `anual` | Avaliações, média e utilizadores por ano | 23 · 4 | 1M: 904 757 das avaliações (90%) em 2000 |
| `mensal` | Avaliações e média por mês | 267 · 35 | Picos e lacunas mês a mês |
| `valores_ano` | Avaliações de cada nota em cada ano | 195 · 20 | Mostra quando surgem as meias estrelas |
| `distribuicao` | Quantos utilizadores usam cada nota e com que peso | 10 · 5 | 1M: a nota 4 é 34,9% das avaliações |
| `perfis_ativos` | Utilizadores ativos só com inteiros, só x,5 ou mistos | 28 · 4 | 1M: todos "só inteiros" |
| `perfis_cumulativos` | O mesmo, com o histórico acumulado | 39 · 4 | — |
| `grupos_atividade` | Os mais ativos dão notas diferentes? | 108 · 20 | 1M, 2000: média 3,77 (20–49 aval.) vs 3,36 (≥ 1000) |
| `ponderado` | Top 10 com média bayesiana (m = 100) | 10 · 10 | Shawshank Redemption em 1.º nos dois |
| `evolucao_filmes` | Que filmes mudaram mais de média (5 anos vs 5 anos)? | 366 · 0 | small: Starship Troopers +0,89 |
| `filmes_ano` | Média anual do filme que mais subiu e do que mais desceu | 39 · 0 | small: Grease (maior descida) |
| `filtros_eventos` | Quantos pares (filme, dia) passam cada filtro de eventos | 1 · 1 | 1M: 407 251 → 3 884 eventos |
| `eventos` | Dias com notas extremas anómalas num filme e suspeitos envolvidos | 0 · 100 | 1M: quase todos em nov./dez. de 2000 |
| `10_flag_bots` e `_calibracao` | Utilizadores suspeitos (ver secção seguinte) | 610 · 6 040 | 2 suspeitos no small, 6 no 1M |

O 1M dá 0 linhas em `evolucao_filmes` e `filmes_ano` porque só cobre 4 anos; o small dá 0 em `eventos` porque nenhum filme tem 5 utilizadores no mesmo dia.

**SQL das queries simples (DuckDB):**

```sql
-- qualidade.sql
SELECT COUNT(*)                                     AS linhas,
       COUNT(DISTINCT userId)                       AS utilizadores,
       COUNT(DISTINCT movieId)                      AS filmes,
       COUNT(*) - COUNT(DISTINCT (userId, movieId)) AS pares_repetidos,
       COUNT(*) FILTER (WHERE userId IS NULL OR movieId IS NULL OR rating IS NULL
                              OR "timestamp" IS NULL) AS linhas_com_nulos,
       COUNT(*) FILTER (WHERE rating < 0.5 OR rating > 5
                              OR rating * 2 != floor(rating * 2)) AS fora_dominio_comum,
       COUNT(*) FILTER (WHERE rating != floor(rating)) AS nao_inteiros,
       COUNT(*) FILTER (WHERE rating < 1)              AS inferior_a_um
FROM ${ratings};

-- integridade.sql
SELECT (SELECT COUNT(*) - COUNT(DISTINCT movieId) FROM ${movies})              AS ids_filmes_repetidos,
       (SELECT COUNT(*) FROM ${ratings} r
         WHERE NOT EXISTS (SELECT 1 FROM ${movies} m WHERE m.movieId = r.movieId)) AS ratings_sem_filme,
       (SELECT COUNT(DISTINCT r.movieId) FROM ${ratings} r
         WHERE NOT EXISTS (SELECT 1 FROM ${movies} m WHERE m.movieId = r.movieId)) AS filmes_sem_metadados,
       (SELECT COUNT(*) FROM ${movies} WHERE title IS NULL OR genres IS NULL)      AS filmes_com_nulos;

-- anual.sql
SELECT year AS ano, COUNT(*) AS num_ratings, AVG(rating) AS media,
       COUNT(DISTINCT userId) AS utilizadores
FROM ${ratings} GROUP BY year ORDER BY year;

-- mensal.sql
SELECT strftime(epoch_ms(timestamp * 1000), '%Y-%m') AS mes,
       COUNT(*) AS num_ratings, AVG(rating) AS media
FROM ${ratings} GROUP BY 1 ORDER BY 1;

-- valores_ano.sql
SELECT year AS ano, rating, COUNT(*) AS num_ratings
FROM ${ratings} GROUP BY year, rating ORDER BY year, rating;

-- distribuicao.sql
WITH d AS (SELECT userId, rating, COUNT(*) AS n FROM ${ratings} GROUP BY userId, rating),
     t AS (SELECT userId, SUM(n) AS total FROM d GROUP BY userId),
     g AS (SELECT COUNT(*) AS utilizadores, SUM(total) AS avaliacoes FROM t)
SELECT d.rating,
       COUNT(*)                                  AS utilizadores_que_usam,
       100.0 * COUNT(*) / g.utilizadores         AS pct_utilizadores,
       SUM(d.n)                                  AS num_ratings,
       100.0 * SUM(d.n) / g.avaliacoes           AS pct_ratings,
       SUM(d.n * 1.0 / t.total) / g.utilizadores AS prop_media_utilizador
FROM d JOIN t ON d.userId = t.userId CROSS JOIN g
GROUP BY d.rating, g.utilizadores, g.avaliacoes
ORDER BY d.rating;

-- ponderado.sql  (weighted = v/(v+m)*R + m/(v+m)*C, m = 100)
WITH s AS (SELECT movieId, AVG(rating) AS media_filme, COUNT(*) AS v
           FROM ${ratings} GROUP BY movieId),
     p AS (SELECT AVG(rating) AS media_global FROM ${ratings})
SELECT s.movieId, m.title, s.media_filme AS avg_rating, s.v AS num_ratings,
       s.v / (s.v + 100.0) * s.media_filme + 100.0 / (s.v + 100.0) * p.media_global AS weighted,
       p.media_global
FROM s CROSS JOIN p JOIN ${movies} m ON s.movieId = m.movieId
ORDER BY weighted DESC, s.movieId
LIMIT 10;

-- grupos_atividade.sql
WITH totais AS (SELECT userId, COUNT(*) AS total FROM ${ratings} GROUP BY userId),
     u AS (SELECT userId, year AS ano, AVG(rating) AS media_utilizador, COUNT(*) AS n
           FROM ${ratings} GROUP BY userId, year),
     g AS (SELECT u.ano, u.media_utilizador, u.n,
                  CASE WHEN t.total < 50 THEN 20 WHEN t.total < 100 THEN 50 WHEN t.total < 250 THEN 100
                       WHEN t.total < 1000 THEN 250 ELSE 1000 END AS faixa_min
           FROM u JOIN totais t ON u.userId = t.userId)
SELECT ano, faixa_min,
       CASE faixa_min WHEN 20 THEN '20–49' WHEN 50 THEN '50–99' WHEN 100 THEN '100–249'
                      WHEN 250 THEN '250–999' ELSE '1000 ou mais' END AS grupo,
       AVG(media_utilizador) AS media, COUNT(*) AS utilizadores, SUM(n) AS avaliacoes
FROM g GROUP BY ano, faixa_min ORDER BY ano, faixa_min;

-- perfis_ativos.sql
WITH y AS (SELECT userId, year AS ano, COUNT(*) AS n,
                  count_if(rating = floor(rating))  AS inteiros,
                  count_if(rating != floor(rating)) AS nao_inteiros
           FROM ${ratings} GROUP BY userId, year),
     c AS (SELECT ano,
                  SUM(n)            OVER w AS total,
                  SUM(inteiros)     OVER w AS i,
                  SUM(nao_inteiros) OVER w AS ni
           FROM y
           WINDOW w AS (PARTITION BY userId ORDER BY ano
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW))
SELECT ano,
       CASE WHEN ni = 0 THEN 'Só inteiros' WHEN i = 0 THEN 'Só não inteiros' ELSE 'Misto' END AS perfil,
       COUNT(*) AS utilizadores
FROM c WHERE total >= 2
GROUP BY 1, 2 ORDER BY 1, 2;
```

No repositório, `perfis_ativos.sql` repete a janela em cada `SUM … OVER (…)`; aqui usa-se `WINDOW w` só para encurtar. O SQL completo das queries longas (`eventos`, `filtros_eventos`, `evolucao_filmes`, `filmes_ano`, `perfis_cumulativos`) está no anexo no fim do documento.

## Fase 4 — Deteção de bots e coordenação entre contas

A nova regra sinaliza 2 utilizadores no small (0,33%) e 6 no 1M (0,10%), contra 34,4% e 46,8% da regra original do notebook. Não há evidência de contas coordenadas no 1M nem no 32M. Tudo isto está ainda a validar com o Luís.

### Regras de bots — `sql/analise/10_flag_bots.sql`

A regra original do notebook (`utilizadores_sinalizados`, célula 112) sinalizava sobretudo o pico normal de avaliações no dia do registo. A nova regra sinaliza só o que não é fisicamente plausível para um humano, e nunca diz "bot confirmado".

1. **Eventos de submissão:** as avaliações com o mesmo `(userId, timestamp)` formam um evento, porque o `timestamp` regista a gravação e não o clique. Todos os ritmos são medidos em eventos.
2. **Submissão em lote** (categoria à parte, não é bot): pelo menos um evento com ≥ 10 avaliações no mesmo segundo, típico do formulário dos anos 90.
3. **Regra A — ritmo sustentado fora do registo:** ignora as primeiras 24 h; conta eventos numa janela deslizante de 10 min (`RANGE BETWEEN CURRENT ROW AND 599 FOLLOWING`); sinaliza quem atinge o quantil p99,9 desse máximo, calculado na própria query para cada dataset.
4. **Regra B — registo extremo:** nas primeiras 24 h, ≥ 100 eventos **e** intervalo mediano ≤ 2 s.
5. **Sinais complementares** (0 a 3, não classificam sozinhos): desvio-padrão das notas no 1% mais baixo, % da nota modal no 1% mais alto, % de eventos em lote no 1% mais alto.

- **Input:** `${ratings}` (Parquet). **Output:** `results/<ds>/analises/10_flag_bots.csv`, uma linha por utilizador com métricas, regras e `classificacao`. A `10_flag_bots_calibracao.sql` lê esse resultado e mostra quantos ficariam sinalizados com o limiar no p99, p99,5 e p99,9.

|  | small | 1M |
| --- | --: | --: |
| Utilizadores / com atividade depois do registo | 610 / 248 | 6 040 / 2 239 |
| Máx. de eventos em 10 min: p99 / p99,9 / máx. | 90,8 / 114,8 / 119 | 35 / 40 / 45 |
| Regra A no p99 / p99,5 / p99,9 | 3 / 2 / 1 | 25 / 13 / 6 |
| Regra B | 1 | 0 |
| **Suspeitos (A ou B, p99,9)** | **2 (0,33%)**: 89 (B), 610 (A) | **6 (0,10%)**: 1077, 1117, 1875, 2880, 5522, 5536 (A) |
| Submissão em lote | 13 (2,1%) | 339 (5,6%) |
| Regra original do notebook | 210 (34,4%) | 2 829 (46,8%) |

Os 5 utilizadores de referência do small são testados em cada corrida e dão todos o esperado: o 610 (566 avaliações numa hora, 6 meses depois do registo) cai na regra A; o 89 (518 avaliações em 23 min no registo) na regra B; o 534 (até 128 avaliações no mesmo segundo, 2016) fica como submissão em lote; o 257 e o 7 ficam sem sinais. O 32M ainda não foi corrido.

### Coordenação entre contas — `scripts/06_coordenacao.py`

- **O que faz:** procura "rajadas": o mesmo filme recebe a mesma nota extrema de ≥ U utilizadores na mesma hora UTC, a ≥ D pontos da média do filme (U ∈ {3, 5, 10, 20}, D ∈ {1,5; 2}). Compara com uma linha de base em que os timestamps são baralhados dentro de cada filme (valor-p empírico, z, correção de Bonferroni) e caracteriza as 10 rajadas mais fortes conta a conta.
- **Input:** `data/<ds>/parquet/ratings.parquet`, `movies.parquet` e, se existir, `results/<ds>/analises/10_flag_bots.csv`.
- **Output:** `results/<ds>/bots_coordenacao/`: `rajadas.csv`, `linha_base.csv`, `teste.csv`, `rajadas_por_ano.csv`, `verificacao_permutacao.csv`, `top10_rajadas.csv`, `top10_contas.csv`, `coordenacao_relatorio.md`.
- **Comando:** `python scripts/06_coordenacao.py --dataset 32m --repeticoes 200 --memoria 12GB`

|  | 1M | 32M |
| --- | --- | --- |
| Permutações / tempo | 20 / \~2 s | 200 / 597 s (\~6,3 GB de memória) |
| Rajadas reais vs média das permutações (U ≥ 3, D ≥ 1,5) | 87 vs 73,1 (p = 0,095) | 2 200 vs 931 (z = 47,4, p = 0,005) |
| Passa Bonferroni? | Nenhuma das 24 comparações | Nenhuma das 40 (seriam precisas ≥ 800 permutações) |
| Explicação | 70 das 87 rajadas em 20–21/11/2000, contas no dia do registo | Excesso todo antes de 2003, coincide com a mudança para meias estrelas (18/02/2003) |
| Conclusão | Sem evidência de coordenação | Sem evidência de coordenação; a linha de base não respeita a mudança de escala |

No 32M fica um caso por explicar: 22/05/1998 (Body Snatchers, Money Talks), com contas antigas e nenhuma no registo. A proposta, ainda não implementada, é permutar dentro de (filme, era antes/depois de 18/02/2003) com ≥ 800 permutações. O SQL completo de `10_flag_bots.sql` e da calibração está no anexo.

## Fase 2 — Preparação cloud (S3 → Glue → Athena)

A cadeia S3 → Glue → Athena correu a 8/11/2026 no small e no 32M, com todas as contagens validadas. No 32M, o Parquet particionado reduz os dados lidos pelo Athena até 186 vezes face ao CSV; o benchmark completo custou 0,06 USD.

### `prepare_cloud.py` — espelho local do S3

- **O que faz:** sem chamar a AWS, cria em `data/cloud/<pasta>/` exatamente o que vai para o S3: uma pasta por tabela, Parquet com compressão zstd, `ratings` sem partição e particionado por ano (o `year` só no nome da pasta) e uma cópia do `ratings.csv`. Verifica contagens, soma das partições, tipos e compressão antes de escrever o manifesto.
- **Input:** `data/<ds>/parquet/` e `data/<ds>/csv/ratings.csv`.
- **Output:** `data/cloud/<pasta>/{ratings, ratings_part/year=AAAA, ratings_csv, movies, tags, links}/` e `reports/cloud_manifest_<ds>.md`. No 32M, o `ratings` passa de 217,7 MB (snappy) para 158,9 MB (zstd).
- **Comando:** `python scripts/prepare_cloud.py --dataset 32m`

### `athena_setup.py` — catálogo no Glue

- **O que faz:** corre o DDL de `sql/athena/ddl/` (00 a 07) para criar a base `movielens_<ds>` e as tabelas EXTERNAL `ratings`, `ratings_part`, `ratings_csv`, `movies`, `tags`, `links`; regista as partições com `MSCK REPAIR TABLE` e confirma as contagens no Athena. Antes, compara o DDL com os ficheiros locais.
- **Input:** `sql/athena/ddl/*.sql`, `data/cloud/<pasta>/`, `config.yaml` (buckets `bdf26-g1-movielens-dados-tvf` e `bdf26-g1-athena-resultados-tvf`, região `us-east-1`). **Output:** bases `movielens_small` e `movielens_32m` no Glue Data Catalog.
- **Comando:** `python scripts/athena_setup.py --dataset 32m --recriar`
- **Resultado:** 6 tabelas em cada base; no 32M, 32 000 204 ratings nas três versões e 29 partições; no small, 100 836 ratings e 23 partições. As contagens no Athena batem com os ficheiros locais.
- **Lição:** o `MSCK REPAIR TABLE` só regista as partições que já estão no S3. Corrido antes do upload, a `ratings_part` fica com 0 linhas sem dar erro; foi preciso recriar depois do `aws s3 sync`.

Exemplo de DDL (tabela particionada):

```sql
CREATE EXTERNAL TABLE IF NOT EXISTS ratings_part (
    userid      int,
    movieid     int,
    rating      double,
    `timestamp` bigint
)
PARTITIONED BY (year int)
STORED AS PARQUET
LOCATION 's3://${bucket}/${pasta}/ratings_part/';

MSCK REPAIR TABLE ratings_part;
```

### Queries em Athena (Trino) — `sql/athena/`

As 5 queries do benchmark e as 16 análises foram traduzidas para Trino. As diferenças principais: `UNNEST` com `CROSS JOIN` em vez de `unnest(string_split(…))`, `approx_percentile` em vez de `MEDIAN`, `from_unixtime` em vez de `to_timestamp`/`epoch_ms`, nomes de colunas em minúsculas e divisões inteiras explícitas. Exemplo:

```sql
-- sql/athena/queries/02_filmes_por_genero.sql
WITH movie_genre AS (
    SELECT m.movieid, t.genre
    FROM ${movies} AS m
    CROSS JOIN UNNEST(split(m.genres, '|')) AS t(genre)
)
SELECT genre,
       COUNT(*)                                                      AS num_movies,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ${movies}), 1) AS pct_movies
FROM movie_genre
GROUP BY genre
ORDER BY num_movies DESC, genre;

-- sql/athena/queries/06_ratings_desde_2015.sql (partition pruning)
SELECT r.year, COUNT(*) AS num_ratings, ROUND(AVG(r.rating), 3) AS avg_rating
FROM ${ratings} AS r
WHERE r.year >= 2015
GROUP BY r.year
ORDER BY r.year;
```

As 16 análises em Trino foram testadas por emulação no DuckDB (`05_analises.py --emular-athena`) no small e no 1M: dão o mesmo n.º de linhas que as versões DuckDB.

### `athena_benchmark.py` — DuckDB vs Athena

- **O que faz:** corre as mesmas perguntas no DuckDB (sobre `data/cloud/`) e no Athena (sobre o S3), com `ratings` em CSV, Parquet e Parquet particionado; 3 corridas, mediana. No Athena regista também o tempo no motor e os MB lidos, e avisa se o n.º de linhas difere do DuckDB.
- **Input:** `sql/athena/queries/*.sql`, `sql/0X_*.sql`, `sql/cloud/*.sql`, `data/cloud/<pasta>/`. **Output:** `results/cloud_benchmarks.csv`.
- **Comando:** `python scripts/athena_benchmark.py --dataset 32m`
- **Resultado:** as duas engines devolvem o mesmo n.º de linhas em todas as queries, no small e no 32M.

Resultados da corrida de 8/11/2026 no 32M, após a validação das 6 tabelas.

**MB lidos pelo Athena no 32M** (o que o Athena cobra, a 5 USD/TB):

| Query | CSV | Parquet | Parquet por ano | Redução face ao CSV |
| --- | --: | --: | --: | --: |
| 03\_avaliacoes\_por\_utilizador | 877,10 | 12,60 | 13,71 | 70× |
| 04\_top\_filmes | 878,39 | 71,15 | 66,50 | 13× |
| 05\_ratings\_por\_ano | 877,10 | 94,38 | 11,23 | 78× |
| 06\_ratings\_desde\_2015 | 877,10 | 94,38 | 4,71 | 186× |

O CSV obriga a ler sempre o ficheiro inteiro. O Parquet lê só as colunas usadas: 12,6 MB na 03, que só precisa de `userId` e `rating`. A partição corta ainda mais quando a query usa o ano: na 05 o ano vem do nome da pasta e o `timestamp` não é lido; na 06 o filtro `year >= 2015` abre só 9 das 29 pastas. As queries 01 e 02 só usam `movies` e leem 0,11 MB.

**Tempo no 32M** (mediana de 3 corridas, em segundos; DuckDB local / Athena):

| Query | CSV | Parquet | Parquet por ano |
| --- | --- | --- | --- |
| 03\_avaliacoes\_por\_utilizador | 0,47 / 2,97 | 0,20 / 3,07 | 0,21 / 3,16 |
| 04\_top\_filmes | 0,30 / 2,37 | 0,13 / 3,88 | 0,69 / 3,17 |
| 05\_ratings\_por\_ano | 0,48 / 2,08 | 0,25 / 1,59 | 0,019 / 1,43 |
| 06\_ratings\_desde\_2015 | 0,51 / 1,57 | 0,30 / 2,21 | 0,008 / 1,13 |

Com 1 GB de dados, o DuckDB num portátil é mais rápido do que o Athena em todas as queries. O Athena tem um custo fixo de cerca de 0,6 s por query (fila, planeamento, escrita do resultado no S3), e na 03 tem ainda de escrever 200 948 linhas de resultado, o que dá cerca de 3 s em qualquer formato. A vantagem do Athena não é a velocidade a esta escala: é não precisar de infraestrutura, escalar para volumes que não cabem num portátil e cobrar só pelos dados lidos.

**Custo.** O benchmark do 32M (42 queries no Athena) custou 11,71 GB faturados, 0,059 USD. Cerca de 90% desse valor vem das 12 corridas sobre o CSV (877 MB cada, 0,0044 USD por query). A mesma query 06 sobre o Parquet particionado é faturada pelo mínimo de 10 MB, 0,00005 USD, quase 90 vezes menos.

**No small**, todas as queries no Athena demoram 0,7 a 1,5 s e o custo fixo domina. O Parquet particionado é até mais lento (1,2 s contra 0,7 s na 05), porque são 23 ficheiros minúsculos e o Athena faz um pedido ao S3 por cada um (o "small files problem"). Os 0,42 GB faturados (0,002 USD) são quase todos o mínimo de 10 MB por query.

### Consultas manuais na consola do Athena

Para explorar os dados ou fazer uma demonstração, as queries fazem-se no query editor do Athena (`us-east-1`), com **Data source** `AwsDataCatalog` e **Database** `movielens_small` ou `movielens_32m`; os resultados vão para `s3://bdf26-g1-athena-resultados-tvf/`. Por baixo de cada resultado, o Athena mostra o tempo e os dados lidos: a mesma pergunta lê 4,7 MB em `ratings_part` e 877 MB em `ratings_csv`. Os nomes das colunas estão em minúsculas (`movieid`, `userid`).

```sql
SELECT r.year, COUNT(*) AS num_ratings, ROUND(AVG(r.rating), 3) AS avg_rating
FROM ratings_part r
WHERE r.year >= 2015
GROUP BY r.year
ORDER BY r.year;
```

O "Query with S3 Select" da consola do S3 não serve para isto: por omissão trata o ficheiro como CSV e, num Parquet, dá o erro "UTF-8 encoding is required … near byte 8,192". O ficheiro está correto (o Athena lê-o sem problemas), por isso a sugestão automática de o recodificar e reenviar deve ser ignorada.

### Lições da primeira execução

- **`data/cloud` não existia neste repositório**, porque o `prepare_cloud.py` tinha corrido noutra cópia. O small foi gerado de novo (verificações OK); o `ml-32m` já estava cá.
- **O 32M não chegou a ser enviado na primeira tentativa** e o Athena devolveu 0 linhas em todas as tabelas, sem erro. Confirmar sempre o upload com `aws s3 ls … --summarize` (no 32M: 34 objetos, 1,1 GiB).
- **O `MSCK REPAIR TABLE` só regista partições que já estão no S3.** Corrido antes do upload, a `ratings_part` fica com 0 linhas; foi preciso `athena_setup.py --recriar` depois do `sync`.
- **O benchmark gravou corridas inválidas** (0 linhas no Athena) quando a validação tinha falhado. Essas linhas foram removidas do `results/cloud_benchmarks.csv`; ficaram só as corridas validadas.
- **Credenciais:** em cada sessão do Learner Lab, copiar o bloco de AWS Details → AWS CLI e gravar com `pbpaste > ~/.aws/credentials`. A sugestão `aws login` da CLI não se aplica ao Learner Lab.

### Reprodutibilidade pelos colegas (próximo passo)

A fase cloud ainda depende de passos manuais na conta do Tiago. Cada aluno tem a sua conta do Learner Lab, com credenciais próprias, por isso cada colega tem de conseguir correr tudo na sua conta com um comando. O prompt para o Claude Code está preparado, mas ainda não foi executado:

- um passo `cloud` opcional no `run_pipeline.py` (`--steps cloud`), fora dos passos por omissão, que faz por ordem: verificar as credenciais → `prepare_cloud` → criar os buckets → upload com boto3 só do que mudou → `athena_setup --recriar` → `athena_benchmark` só se a validação passar;
- nomes dos buckets derivados do ID da conta (`bdf26-g1-dados-<id>`), sem configuração manual e sem o ID escrito no repositório; o `config.yaml` volta a ter os buckets a `null`;
- o benchmark deixa de gravar corridas em que o n.º de linhas no Athena difere do DuckDB;
- uma secção do README para o Learner Lab (credenciais, comando único, custos, erros comuns).

Vai ser feito no branch `fase2-cloud-pipeline` e testado só com o small. Os buckets `-tvf` atuais e os resultados de hoje continuam válidos.

## Estado do git e pendentes

Nenhum dos três branches de trabalho está no `main`: o `integracao-queries-luis` contém tudo (30 commits à frente de `origin/main`, 0 atrás) e está sincronizado com o GitHub.

| Branch | Último commit | Conteúdo | Integrado no `main`? |
| --- | --- | --- | --- |
| `integracao-queries-luis` | `cbd7cb1` | Tudo: fases 1 e 2, notebook do Luís, blocos 1–6 | Não |
| `fase2-cloud-prep` | `2b54c11` | Fase 1 + preparação cloud | Não (contido no anterior) |
| `fase1-pipeline` | `604c14a` | Pipeline local, EDA, revisão didática | Não (contido nos anteriores) |
| `origin/main` | `e51d050` | Notebook inicial com novas questões (Luís) | — |

O `main` local está divergente do `origin/main` (4 commits antigos só locais, 6 só no remoto) e precisa de ser alinhado antes de qualquer merge.

**Validação pelo Luís**

- [ ] Regras A e B, quantil p99,9, limites da regra B (≥ 100 eventos, ≤ 2 s), limite de lote (10) e sinais complementares
- [ ] Um só conjunto de limites para os eventos; faixas de `grupos_atividade`; opção "só anos completos" de `evolucao_filmes`
- [ ] Qual notebook fica como oficial
- [ ] Coordenação: linha de base estratificada por era, ≥ 800 permutações e o caso de 22/05/1998

**Execução no 32M**

- [ ] Registar o `ingest` e o `parquet` do 32M neste repositório (`run_pipeline.py --dataset 32m --steps ingest parquet`): correram noutra cópia e faltam no `sizes.csv`
- [ ] `python scripts/05_analises.py --dataset 32m --emular-athena`, depois de decidir onde gravar o `10_flag_bots.csv` (200 948 linhas)
- [ ] Calibrar a regra A no 32M (p99, p99,5, p99,9)

**Execução real no Athena**

- [x] Criar os buckets e fazer o upload de `data/cloud/` (small e 32M)
- [x] Correr `athena_setup.py` e `athena_benchmark.py` para medir tempos, MB lidos e custo (small e 32M)
- [ ] Commit do `results/cloud_benchmarks.csv` e dos manifestos, sem o `config.yaml` (os nomes dos buckets são pessoais)
- [ ] Passo `cloud` no `run_pipeline.py`, buckets derivados da conta e README do Learner Lab (branch `fase2-cloud-pipeline`, teste só no small)
- [ ] Criar `scripts/athena_analises.py` para correr `sql/athena/analise/` e comparar com os resultados locais
- [ ] Confirmar no Athena a janela `RANGE … 599 FOLLOWING`, `approx_percentile` e o CTAS do `flag_bots`

**Outros**

- [ ] Alinhar o `main` local e abrir o Pull Request de `integracao-queries-luis` para `main`
- [ ] Atualizar o README (passo `analises`, `06_coordenacao.py`, estrutura do repositório)
- [ ] Decidir se `sql/athena/queries/04_top_filmes.sql` acompanha o desempate por `movieId`
- [ ] Figuras para o `05_analises.py` (implica mover o estilo NOVA para um módulo partilhado)
- [ ] Acrescentar `dados/` e `lab_resultados.zip` ao `.gitignore`

## Anexo — SQL completo das queries longas (DuckDB)

Versões de `sql/analise/`, sem os comentários. `${ratings}` e `${movies}` são o Parquet; `${flag_bots}` é o resultado de `10_flag_bots.sql`. As versões Athena estão em `sql/athena/analise/` com o mesmo nome.

**10\_flag\_bots.sql** — utilizadores suspeitos (regras A e B), submissão em lote e sinais complementares.

```sql
WITH lim AS (SELECT 86400 AS registo_s,
                    100   AS regra_b_min_eventos,
                    2     AS regra_b_max_mediana_s,
                    10    AS lote_min_avaliacoes),
     ev AS (SELECT userId, timestamp AS ts, COUNT(*) AS k
            FROM ${ratings}
            GROUP BY userId, timestamp),
     fase AS (SELECT ev.*,
                     ts - MIN(ts) OVER (PARTITION BY userId) < l.registo_s AS no_registo
              FROM ev CROSS JOIN lim l),
     ritmo AS (SELECT fase.*,
                      ts - LAG(ts) OVER (PARTITION BY userId, no_registo ORDER BY ts) AS intervalo,
                      COUNT(*) OVER (PARTITION BY userId, no_registo ORDER BY ts
                                     RANGE BETWEEN CURRENT ROW AND 599 FOLLOWING)  AS eventos_10min
               FROM fase),
     por_eventos AS (SELECT userId,
                            COUNT(*)                                          AS eventos,
                            MAX(k)                                            AS max_avaliacoes_mesmo_segundo,
                            100.0 * count_if(k >= 2) / COUNT(*)               AS pct_eventos_lote,
                            count_if(no_registo)                              AS eventos_registo,
                            MEDIAN(intervalo) FILTER (WHERE no_registo)       AS mediana_intervalo_registo_s,
                            MAX(eventos_10min) FILTER (WHERE no_registo)      AS max_eventos_10min_registo,
                            count_if(NOT no_registo)                          AS eventos_apos_registo,
                            MEDIAN(intervalo) FILTER (WHERE NOT no_registo)   AS mediana_intervalo_apos_s,
                            MAX(eventos_10min) FILTER (WHERE NOT no_registo)  AS max_eventos_10min_apos,
                            MIN(ts)                                           AS primeiro_ts,
                            MAX(ts)                                           AS ultimo_ts
                     FROM ritmo
                     GROUP BY userId),
     notas AS (SELECT userId, COUNT(*) AS avaliacoes, STDDEV_SAMP(rating) AS desvio_notas
               FROM ${ratings} GROUP BY userId),
     por_nota AS (SELECT userId, rating, COUNT(*) AS n FROM ${ratings} GROUP BY userId, rating),
     modal AS (SELECT userId, MAX(n) AS n_nota_modal FROM por_nota GROUP BY userId),
     base AS (SELECT e.*, n.avaliacoes, n.desvio_notas,
                     100.0 * m.n_nota_modal / n.avaliacoes AS pct_nota_modal
              FROM por_eventos e
              JOIN notas n ON e.userId = n.userId
              JOIN modal m ON e.userId = m.userId),
     limiar_a AS (SELECT quantile_cont(max_eventos_10min_apos, 0.999) AS limiar_regra_a
                  FROM base WHERE eventos_apos_registo > 0),
     limiares_c AS (SELECT quantile_cont(desvio_notas, 0.01)     AS limiar_desvio_baixo,
                           quantile_cont(pct_nota_modal, 0.99)   AS limiar_modal_alto,
                           quantile_cont(pct_eventos_lote, 0.99) AS limiar_lote_alto
                    FROM base),
     f AS (SELECT b.*, a.limiar_regra_a,
                  COALESCE(b.eventos_apos_registo > 0 AND b.max_eventos_10min_apos >= a.limiar_regra_a, false) AS regra_a,
                  COALESCE(b.eventos_registo >= l.regra_b_min_eventos
                           AND b.mediana_intervalo_registo_s <= l.regra_b_max_mediana_s, false)               AS regra_b,
                  b.max_avaliacoes_mesmo_segundo >= l.lote_min_avaliacoes                                     AS submissao_lote,
                  CASE WHEN b.desvio_notas <= c.limiar_desvio_baixo THEN 1 ELSE 0 END
                    + CASE WHEN b.pct_nota_modal >= c.limiar_modal_alto THEN 1 ELSE 0 END
                    + CASE WHEN b.pct_eventos_lote >= c.limiar_lote_alto THEN 1 ELSE 0 END                    AS sinais_complementares
           FROM base b CROSS JOIN limiar_a a CROSS JOIN limiares_c c CROSS JOIN lim l)
SELECT userId, avaliacoes, eventos,
       strftime(epoch_ms(primeiro_ts * 1000), '%Y-%m-%d') AS primeiro_dia,
       strftime(epoch_ms(ultimo_ts * 1000), '%Y-%m-%d')   AS ultimo_dia,
       eventos_registo, mediana_intervalo_registo_s, max_eventos_10min_registo,
       eventos_apos_registo, mediana_intervalo_apos_s, max_eventos_10min_apos, limiar_regra_a,
       max_avaliacoes_mesmo_segundo, pct_eventos_lote, desvio_notas, pct_nota_modal,
       regra_a, regra_b, submissao_lote, sinais_complementares,
       CASE WHEN regra_a AND regra_b THEN 'suspeito (regras A e B)'
            WHEN regra_a THEN 'suspeito (regra A)'
            WHEN regra_b THEN 'suspeito (regra B)'
            WHEN submissao_lote THEN 'submissão em lote'
            ELSE 'sem sinais' END AS classificacao
FROM f
ORDER BY userId;
```

**10\_flag\_bots\_calibracao.sql** — distribuição do ritmo depois do registo e sinalizados com o limiar no p99, p99,5 e p99,9.

```sql
WITH a AS (SELECT max_eventos_10min_apos AS x, mediana_intervalo_apos_s AS mediana
           FROM ${flag_bots} WHERE eventos_apos_registo > 0),
     q AS (SELECT COUNT(*)               AS utilizadores_com_atividade_apos_registo,
                  quantile_cont(x, 0.5)   AS p50,
                  quantile_cont(x, 0.9)   AS p90,
                  quantile_cont(x, 0.95)  AS p95,
                  quantile_cont(x, 0.99)  AS p99,
                  quantile_cont(x, 0.995) AS p99_5,
                  quantile_cont(x, 0.999) AS p99_9,
                  MAX(x)                  AS maximo
           FROM a),
     s AS (SELECT q.utilizadores_com_atividade_apos_registo, q.p50, q.p90, q.p95, q.p99, q.p99_5, q.p99_9, q.maximo,
                  count_if(a.x >= q.p99)   AS sinalizados_a_p99,
                  count_if(a.x >= q.p99_5) AS sinalizados_a_p99_5,
                  count_if(a.x >= q.p99_9) AS sinalizados_a_p99_9
           FROM a CROSS JOIN q
           GROUP BY q.utilizadores_com_atividade_apos_registo, q.p50, q.p90, q.p95, q.p99, q.p99_5, q.p99_9, q.maximo),
     t AS (SELECT COUNT(*)                                     AS utilizadores,
                  count_if(regra_a)                            AS regra_a,
                  count_if(regra_b)                            AS regra_b,
                  count_if(regra_a OR regra_b)                 AS suspeitos,
                  count_if(submissao_lote)                     AS submissao_lote,
                  count_if(submissao_lote AND NOT (regra_a OR regra_b)) AS so_submissao_lote,
                  100.0 * count_if(regra_a OR regra_b) / COUNT(*) AS pct_suspeitos
           FROM ${flag_bots})
SELECT s.*, t.* FROM s CROSS JOIN t;
```

**eventos.sql** — pares (filme, dia) com muitas notas extremas no mesmo sentido e média afastada do histórico anterior; quantos participantes são suspeitos. Top 100.

```sql
WITH lim AS (SELECT 5 AS min_anterior, 5 AS min_utilizadores, 2.0 AS nota_baixa, 4.0 AS nota_alta,
                    0.51 AS min_frac_extremas, 0.5 AS min_variacao),
     d AS (SELECT r.movieId, r.timestamp // 86400 AS dia, COUNT(*) AS n,
                  COUNT(DISTINCT r.userId) AS utilizadores, SUM(r.rating) AS soma, AVG(r.rating) AS media,
                  count_if(r.rating <= l.nota_baixa) * 1.0 / COUNT(*) AS frac_baixas,
                  count_if(r.rating >= l.nota_alta)  * 1.0 / COUNT(*) AS frac_altas
           FROM ${ratings} r CROSS JOIN lim l
           GROUP BY r.movieId, r.timestamp // 86400),
     h AS (SELECT d.*,
                  SUM(n)    OVER (PARTITION BY movieId ORDER BY dia ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - n    AS n_anterior,
                  SUM(soma) OVER (PARTITION BY movieId ORDER BY dia ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - soma AS soma_anterior
           FROM d),
     v AS (SELECT h.*, soma_anterior / NULLIF(n_anterior, 0) AS media_anterior,
                  media - soma_anterior / NULLIF(n_anterior, 0) AS variacao
           FROM h),
     ev AS (SELECT v.movieId, v.dia, v.utilizadores, v.n_anterior, v.media_anterior, v.media, v.variacao,
                   CASE WHEN v.frac_baixas >= l.min_frac_extremas AND v.variacao <= -l.min_variacao THEN 'Avaliações baixas'
                        WHEN v.frac_altas  >= l.min_frac_extremas AND v.variacao >=  l.min_variacao THEN 'Avaliações altas'
                   END AS tipo
            FROM v CROSS JOIN lim l
            WHERE v.n_anterior >= l.min_anterior AND v.utilizadores >= l.min_utilizadores),
     e AS (SELECT * FROM ev WHERE tipo IS NOT NULL),
     p AS (SELECT r.movieId, r.timestamp // 86400 AS dia,
                  COUNT(DISTINCT r.userId)                                                  AS participantes,
                  COUNT(DISTINCT CASE WHEN f.regra_a OR f.regra_b THEN r.userId END)        AS suspeitos,
                  COUNT(DISTINCT CASE WHEN f.submissao_lote THEN r.userId END)              AS em_lote
           FROM ${ratings} r
           JOIN e ON r.movieId = e.movieId AND r.timestamp // 86400 = e.dia
           LEFT JOIN ${flag_bots} f ON r.userId = f.userId
           GROUP BY r.movieId, r.timestamp // 86400),
     x AS (SELECT e.*, p.participantes, p.suspeitos, p.em_lote,
                  100.0 * p.suspeitos / p.participantes AS pct_suspeitos,
                  ROW_NUMBER() OVER (ORDER BY p.suspeitos DESC, e.utilizadores DESC, e.movieId, e.dia) AS posicao,
                  COUNT(*) OVER () AS total_eventos
           FROM e JOIN p ON e.movieId = p.movieId AND e.dia = p.dia)
SELECT x.posicao, x.movieId, m.title, CAST(epoch_ms(x.dia * 86400 * 1000) AS DATE) AS dia, x.tipo,
       x.utilizadores, x.n_anterior, x.media_anterior, x.media, x.variacao,
       x.suspeitos, x.em_lote, x.pct_suspeitos, x.total_eventos
FROM x JOIN ${movies} m ON x.movieId = m.movieId
WHERE x.posicao <= 100
ORDER BY x.posicao;
```

**filtros\_eventos.sql** — quantos pares (filme, dia) sobrevivem a cada filtro de `eventos`, por ordem.

```sql
WITH lim AS (SELECT 5 AS min_anterior, 5 AS min_utilizadores, 2.0 AS nota_baixa, 4.0 AS nota_alta,
                    0.51 AS min_frac_extremas, 0.5 AS min_variacao),
     d AS (SELECT r.movieId, r.timestamp // 86400 AS dia, COUNT(*) AS n,
                  COUNT(DISTINCT r.userId) AS utilizadores, SUM(r.rating) AS soma, AVG(r.rating) AS media,
                  count_if(r.rating <= l.nota_baixa) * 1.0 / COUNT(*) AS frac_baixas,
                  count_if(r.rating >= l.nota_alta)  * 1.0 / COUNT(*) AS frac_altas
           FROM ${ratings} r CROSS JOIN lim l
           GROUP BY r.movieId, r.timestamp // 86400),
     h AS (SELECT d.*,
                  SUM(n)    OVER (PARTITION BY movieId ORDER BY dia ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - n    AS n_anterior,
                  SUM(soma) OVER (PARTITION BY movieId ORDER BY dia ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - soma AS soma_anterior
           FROM d),
     v AS (SELECT h.*, media - soma_anterior / NULLIF(n_anterior, 0) AS variacao FROM h)
SELECT COUNT(*) AS todos_filme_dia,
       count_if(n_anterior >= l.min_anterior) AS com_historico,
       count_if(n_anterior >= l.min_anterior AND utilizadores >= l.min_utilizadores) AS com_utilizadores,
       count_if(n_anterior >= l.min_anterior AND utilizadores >= l.min_utilizadores
                AND (frac_baixas >= l.min_frac_extremas OR frac_altas >= l.min_frac_extremas)) AS com_extremos,
       count_if(n_anterior >= l.min_anterior AND utilizadores >= l.min_utilizadores
                AND ((frac_baixas >= l.min_frac_extremas AND variacao <= -l.min_variacao)
                  OR (frac_altas  >= l.min_frac_extremas AND variacao >=  l.min_variacao))) AS eventos,
       l.min_anterior, l.min_utilizadores, l.nota_baixa, l.nota_alta, l.min_frac_extremas, l.min_variacao
FROM v CROSS JOIN lim l
GROUP BY l.min_anterior, l.min_utilizadores, l.nota_baixa, l.nota_alta, l.min_frac_extremas, l.min_variacao;
```

**evolucao\_filmes.sql** — variação da média entre os 5 anos anteriores e os 5 mais recentes (só anos completos; ≥ 10 avaliações em cada período).

```sql
WITH limites AS (SELECT MAX(year) AS ano_max, MAX(timestamp) AS ts_max FROM ${ratings}),
     fim AS (SELECT CASE WHEN month(epoch_ms(ts_max * 1000)) = 12 AND day(epoch_ms(ts_max * 1000)) = 31
                         THEN ano_max ELSE ano_max - 1 END AS ano,
                    ano_max,
                    strftime(epoch_ms(ts_max * 1000), '%Y-%m-%d') AS ultimo_dia
             FROM limites),
     s AS (SELECT r.movieId,
                  COUNT(*)      FILTER (WHERE r.year BETWEEN f.ano - 9 AND f.ano - 5) AS n_anterior,
                  COUNT(*)      FILTER (WHERE r.year BETWEEN f.ano - 4 AND f.ano)     AS n_recente,
                  AVG(r.rating) FILTER (WHERE r.year BETWEEN f.ano - 9 AND f.ano - 5) AS media_anterior,
                  AVG(r.rating) FILTER (WHERE r.year BETWEEN f.ano - 4 AND f.ano)     AS media_recente
           FROM ${ratings} r CROSS JOIN fim f
           WHERE r.year BETWEEN f.ano - 9 AND f.ano
           GROUP BY r.movieId),
     e AS (SELECT s.*, media_recente - media_anterior AS variacao,
                  RANK() OVER (ORDER BY media_anterior DESC) AS posicao_anterior,
                  RANK() OVER (ORDER BY media_recente DESC)  AS posicao_recente
           FROM s
           WHERE n_anterior >= 10 AND n_recente >= 10)
SELECT e.movieId, m.title, e.n_anterior, e.n_recente, e.media_anterior, e.media_recente,
       e.variacao, e.posicao_anterior, e.posicao_recente,
       CAST(f.ano - 9 AS VARCHAR) || '–' || CAST(f.ano - 5 AS VARCHAR) AS periodo_anterior,
       CAST(f.ano - 4 AS VARCHAR) || '–' || CAST(f.ano AS VARCHAR)     AS periodo_recente,
       CASE WHEN f.ano < f.ano_max
            THEN 'só anos completos: exclui ' || CAST(f.ano_max AS VARCHAR) || ' (parcial, último rating ' || f.ultimo_dia || ')'
            ELSE 'só anos completos: o último ano está completo' END AS criterio
FROM e CROSS JOIN fim f
JOIN ${movies} m ON e.movieId = m.movieId
ORDER BY e.variacao DESC, e.movieId;
```

**filmes\_ano.sql** — média ano a ano do filme com a maior subida (≥ 0,5) e da maior descida (≤ −0,5). Repete as CTE `limites`, `fim`, `s` e `e` de `evolucao_filmes.sql` e acrescenta:

```sql
     sobe AS (SELECT movieId, ROW_NUMBER() OVER (ORDER BY variacao DESC, movieId) AS k FROM e WHERE variacao >= 0.5),
     desce AS (SELECT movieId, ROW_NUMBER() OVER (ORDER BY variacao, movieId) AS k FROM e WHERE variacao <= -0.5),
     escolhidos AS (SELECT movieId, 'Maior subida' AS tipo FROM sobe WHERE k = 1
                    UNION ALL
                    SELECT movieId, 'Maior descida' AS tipo FROM desce WHERE k = 1)
SELECT r.movieId, m.title, x.tipo, r.year AS ano, COUNT(*) AS avaliacoes, AVG(r.rating) AS media
FROM ${ratings} r
JOIN escolhidos x ON r.movieId = x.movieId
JOIN ${movies} m ON r.movieId = m.movieId
GROUP BY r.movieId, m.title, x.tipo, r.year
ORDER BY r.movieId, ano;
```

**perfis\_cumulativos.sql** — como `perfis_ativos`, mas cada utilizador conta em todos os anos desde que entrou.

```sql
WITH limites AS (SELECT MIN(year) AS a, MAX(year) AS b FROM ${ratings}),
     anos AS (SELECT unnest(range(a, b + 1)) AS ano FROM limites),
     y AS (SELECT userId, year AS ano,
                  count_if(rating = floor(rating))  AS i,
                  count_if(rating != floor(rating)) AS ni
           FROM ${ratings}
           GROUP BY userId, year),
     grelha AS (SELECT u.userId, a.ano, COALESCE(y.i, 0) AS i, COALESCE(y.ni, 0) AS ni
                FROM (SELECT DISTINCT userId FROM ${ratings}) u
                CROSS JOIN anos a
                LEFT JOIN y ON u.userId = y.userId AND a.ano = y.ano),
     c AS (SELECT ano,
                  SUM(i)  OVER (PARTITION BY userId ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS i,
                  SUM(ni) OVER (PARTITION BY userId ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ni
           FROM grelha)
SELECT ano,
       CASE WHEN ni = 0 THEN 'Só inteiros' WHEN i = 0 THEN 'Só não inteiros' ELSE 'Misto' END AS perfil,
       COUNT(*) AS utilizadores
FROM c
WHERE i + ni >= 2
GROUP BY 1, 2
ORDER BY 1, 2;
```

Fonte: inventário do repositório gerado pelo Claude Code em 07/11/2026 (branch `integracao-queries-luis`, `cbd7cb1`), só por leitura de ficheiros.
