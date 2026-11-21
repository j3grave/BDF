# Big Data Foundations: pipeline MovieLens

Trabalho de grupo da unidade curricular Big Data Foundations, da Pós-Graduação em Enterprise Data
Science & Analytics da NOVA IMS (2026).

O projeto é um pipeline em scripts que leva o MovieLens do download até ao Amazon Athena e mede,
em cada etapa, o efeito do formato e da escala (100 mil, 1 milhão e 32 milhões de avaliações).
Está organizado em quatro blocos: preparação dos dados, desempenho local, análise dos dados e
cloud.

Os notebooks do lab (Parquet, DuckDB, Polars e Arrow) e os documentos de trabalho do grupo
(resumo do projeto, próximos passos e revisão da fase 2) estão arquivados no branch
`arquivo/docs-projeto`.

## Dados

O MovieLens, do [GroupLens](https://grouplens.org/datasets/movielens/), em três tamanhos:

| Dataset | Avaliações | Formato original | Tabelas |
|---|---:|---|---|
| `small` (`ml-latest-small`) | 100 836 | CSV | ratings, movies, tags, links |
| `1m` (`ml-1m`) | 1 000 209 | `.dat` | ratings, movies |
| `32m` (`ml-32m`) | cerca de 32 milhões | CSV | ratings, movies, tags, links |

| Tabela | Conteúdo |
|---|---|
| `ratings` | `userId`, `movieId`, `rating` (0,5 a 5,0) e `timestamp` |
| `movies` | `movieId`, `title` (com o ano) e `genres` (separados por `\|`) |
| `tags` | Etiquetas livres dos utilizadores |
| `links` | Identificadores IMDb e TMDb de cada filme |

Os dados não estão no repositório. O pipeline descarrega-os na primeira execução.
Depois de descarregado e normalizado, o 32M ocupa cerca de 1,2 GB, mais o Parquet.

## Estrutura do repositório

Os scripts estão numerados pela ordem em que correm e organizados em quatro blocos.

```
BDF/
├── run_pipeline.py                # ponto de entrada do pipeline
├── config.yaml                    # dataset por omissão e secção aws
├── requirements.txt
├── scripts/
│   ├── common.py                  # partilhado: configuração, caminhos e CSV de resultados
│   ├── 01_ingest.py               # bloco 1, preparação dos dados: download e CSV
│   ├── 02_to_parquet.py           # bloco 1: Parquet e Parquet por ano
│   ├── 03_benchmark.py            # bloco 2, desempenho local: tempos das queries
│   ├── 04_analise.py              # bloco 3, análise dos dados: EDA, análises e coordenação
│   ├── 05_prepare_cloud.py        # bloco 4, cloud: ficheiros para o S3, em data/cloud/
│   ├── 06_upload_s3.py            # bloco 4: credenciais, buckets e upload
│   ├── 07_athena_setup.py         # bloco 4: catálogo no Glue e validação das contagens
│   ├── 08_athena_benchmark.py     # bloco 4: benchmark DuckDB vs Athena
│   └── athena_common.py           # partilhado pelo bloco 4: opções AWS e cliente do Athena
├── sql/
│   ├── 01_...sql a 05_...sql      # perguntas do benchmark (DuckDB)
│   ├── analise/                   # as 16 queries da análise (DuckDB)
│   ├── cloud/                     # query 06 do benchmark cloud, versão DuckDB
│   └── athena/
│       ├── ddl/                   # CREATE TABLE do Athena
│       ├── queries/               # queries 01 a 06 em Trino
│       └── analise/               # as 16 queries de sql/analise/ em Trino
├── reports/                       # manifestos da preparação para a cloud
├── results/                       # resultados leves (CSV, PNG e relatórios .md)
└── data/                          # não versionado: downloads, CSV, Parquet e data/cloud/
```

Dentro de `results/`:

| Ficheiro ou pasta | Conteúdo |
|---|---|
| `sizes.csv` | Tamanho do CSV, do Parquet e do Parquet por ano, e tempo de cada conversão |
| `pipeline_runs.csv` | Tempo de cada passo |
| `benchmarks.csv` | Mediana do tempo e n.º de linhas de cada query, por formato |
| `cloud_benchmarks.csv` | DuckDB vs Athena: tempo, MB lidos e n.º de linhas |
| `<dataset>/eda/` | Figuras, indicadores e `eda_relatorio.md` |
| `<dataset>/analises/` | Um CSV por query, `analises_relatorio.md` e `athena_emulado/` |
| `<dataset>/bots_coordenacao/` | Resultados do teste de coordenação |

## Ambiente

É preciso Python 3.9 ou superior. O pipeline foi testado com o 3.9 e o 3.13, com os mesmos
resultados.

```bash
git clone https://github.com/j3grave/BDF.git
cd BDF
python3.13 -m venv .venv          # ou python3.12
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Com conda: `conda create -n bdf python=3.13`, `conda activate bdf` e
`pip install -r requirements.txt`.

## Como correr

```bash
python run_pipeline.py --dataset small                 # blocos 1 a 3
python run_pipeline.py --dataset 1m --coordenacao      # o mesmo, com o teste de coordenação
python run_pipeline.py --dataset 1m --steps benchmark  # só um passo
python run_pipeline.py --dataset small --steps cloud   # bloco 4 (usa a AWS)
```

Sem `--dataset`, usa o valor do `config.yaml`. Cada script também corre sozinho, por exemplo
`python scripts/02_to_parquet.py --dataset 1m`. Se um script falhar, o pipeline pára.

| Bloco | Passo | Scripts |
|---|---|---|
| 1. Preparação dos dados | `ingest`, `parquet` | `01_ingest.py`, `02_to_parquet.py` |
| 2. Desempenho local | `benchmark` | `03_benchmark.py` |
| 3. Análise dos dados | `analise` | `04_analise.py` |
| 4. Cloud | `cloud` (só a pedido) | `05_prepare_cloud.py` a `08_athena_benchmark.py` |

A pasta `data/<dataset>` pode ser um symlink para outra cópia onde os dados já existem, para não
repetir o `ingest` e o `parquet`:

```bash
mkdir -p data
ln -s "/caminho/para/outra/copia/BDF/data/32m" data/32m
```

## Bloco 1: preparação dos dados

| Script | O que faz |
|---|---|
| `01_ingest.py` | Descarrega o zip (só se ainda não existir) e grava CSV com o mesmo esquema nos três datasets. Converte os `.dat` do 1M (separador `::`, sem cabeçalho, latin-1). |
| `02_to_parquet.py` | Converte para Parquet com o `COPY` do DuckDB: uma versão sem partição e o `ratings` particionado por ano (em UTC). Regista os tamanhos. |

## Bloco 2: desempenho local

O `03_benchmark.py` corre 3 vezes cada query de `sql/` nos dois Parquet e regista a mediana e o
n.º de linhas. Nas queries, `${ratings}` e `${movies}` são substituídos pela leitura do Parquet.

## Bloco 3: análise dos dados

O `04_analise.py` tem três partes:

1. **Análise exploratória (EDA):** indicadores, qualidade das tabelas, 10 figuras e relatório.
2. **Análises:** as 16 queries de `sql/analise/` (qualidade, integridade, evolução no tempo,
   filmes, uso da escala e utilizadores suspeitos), um CSV por query. Verifica a qualidade e a
   integridade dos dados e compara os totais com a EDA. Se uma verificação falhar, o pipeline pára.
3. **Coordenação entre contas** (só com `--coordenacao`, porque demora cerca de 10 minutos no
   32M): procura rajadas, em que várias contas dão a mesma nota extrema ao mesmo filme na mesma
   hora, longe da média do filme, e compara-as com uma linha de base em que os timestamps são
   baralhados dentro de cada filme.

```bash
python scripts/04_analise.py --dataset small                  # o mesmo que o passo analise
python scripts/04_analise.py --dataset 1m --fonte csv         # lê os CSV em vez do Parquet
python scripts/04_analise.py --dataset small --emular-athena  # testa também as versões Athena
python scripts/04_analise.py --dataset 32m --coordenacao --repeticoes 200 --memoria 12GB
```

Cada query de `sql/analise/` tem uma versão Athena com o mesmo nome em `sql/athena/analise/`. Com
`--emular-athena`, essas versões correm no DuckDB, com macros que imitam as funções do Trino, e
cada resultado é comparado com o da versão DuckDB. Isto confirma a lógica, mas não a sintaxe do
Trino, que só se confirma no Athena.

**Utilizadores suspeitos** (`sql/analise/10_flag_bots.sql`). Uma regra simples, baseada em muita
atividade, sinalizava 34% dos utilizadores do small e 47% do 1M, quase todos por causa do registo
inicial. A query usa duas regras:

- regra A: ritmo sustentado depois das primeiras 24 horas, acima do quantil p99,9;
- regra B: registo extremo, com pelo menos 100 eventos e um intervalo mediano de 2 segundos ou menos.

Com elas, os suspeitos são 0,33% no small e 0,10% no 1M. As submissões em lote (10 ou mais
avaliações no mesmo segundo) são contadas à parte e não entram como bots.

**Coordenação entre contas.** Os resultados ficam em `results/<dataset>/bots_coordenacao/`:

- 1M: não há mais rajadas do que na linha de base. As mais fortes são de contas novas, no pico de
  registos de 20 e 21/11/2000.
- 32M: há mais rajadas do que na linha de base, mas o excesso fica todo antes da escala de meias
  estrelas (fevereiro de 2003) e explica-se pela mudança de escala, não por coordenação. Com 200
  permutações, nenhuma comparação passa a correção de Bonferroni.

## Bloco 4: cloud (AWS Academy Learner Lab)

Leva o dataset para o S3, regista as tabelas no Glue Data Catalog e compara o Athena com o DuckDB.
Cada colega corre-o na sua conta, com um só comando. Não é preciso configurar buckets nem
instalar a AWS CLI.

### Antes de começar

- O ambiente da secção [Ambiente](#ambiente) (o `boto3` está no `requirements.txt`).
- Os passos `ingest` e `parquet` já corridos para o dataset.
- Uma sessão do Learner Lab ativa (indicador verde).

### Credenciais

As credenciais do Learner Lab mudam a cada "Start Lab" e expiram ao fim de cerca de 4 horas. Em
cada sessão:

1. "Start Lab" e esperar pelo indicador verde.
2. "AWS Details" > "AWS CLI: Show" e copiar o bloco `[default]`, com as três linhas.
3. Gravar o bloco em `~/.aws/credentials`:

   ```bash
   mkdir -p ~/.aws && pbpaste > ~/.aws/credentials     # macOS
   ```

   No Windows e no Linux, colar à mão num editor (`%UserProfile%\.aws\credentials` no Windows).

As credenciais ficam fora do repositório. Nunca vão para o `config.yaml` nem para o git.

### Comando

```bash
python run_pipeline.py --dataset small --steps cloud
```

O passo `cloud` não corre por omissão. Corre quatro scripts, por ordem, e pára se algum falhar:

1. **`05_prepare_cloud.py`** grava em `data/cloud/<pasta>/` uma cópia exata do que vai para o S3.
   Se a pasta já estiver atualizada (manifesto mais recente do que o Parquet), não faz nada;
   `--forcar` prepara de novo. Não contacta a AWS.
2. **`06_upload_s3.py`** confirma as credenciais (se faltarem ou tiverem expirado, explica como as
   renovar), cria os buckets em `us-east-1` se não existirem (`bdf26-g1-dados-<ID da conta>` e
   `bdf26-g1-resultados-<ID da conta>`) e envia os ficheiros novos ou com outro tamanho. Não apaga
   nada no S3. O ID da conta só aparece no ecrã e nunca é gravado. Para usar outros nomes, passa
   `--bucket-dados` e `--bucket-resultados` ou escreve-os no `config.yaml`.
3. **`07_athena_setup.py --recriar`** cria a base de dados `movielens_<dataset>` e as quatro
   tabelas, carrega as partições (`MSCK REPAIR TABLE`, depois do upload) e compara as contagens
   (total e por ano) com os ficheiros locais. Antes de enviar o DDL, confirma, sem AWS, que as
   colunas e os tipos coincidem com `data/cloud/`.
4. **`08_athena_benchmark.py`** corre as queries de `sql/athena/queries/` no Athena e as mesmas
   perguntas no DuckDB sobre `data/cloud/`, em CSV, Parquet e Parquet particionado. Uma query só é
   gravada em `results/cloud_benchmarks.csv` se devolver o mesmo n.º de linhas nos dois motores.

Pode voltar a correr-se: os buckets e os ficheiros que já existem são reaproveitados.

```
data/cloud/ml-32m/                    # ml-latest-small no small, ml-1m no 1M
├── ratings/ratings.parquet           # sem partição
├── ratings_part/year=AAAA/*.parquet  # particionado por ano
├── ratings_csv/ratings.csv           # CSV, para comparar os bytes lidos no Athena
└── movies/movies.parquet
```

- Uma pasta por tabela, porque o Glue e o Athena tratam cada pasta como uma tabela. Só vão o
  `ratings` (em três versões) e o `movies`: o `tags` e o `links` não são usados por nenhuma query
  do Athena.
- Parquet com compressão zstd e os mesmos tipos do bloco 1.
- O `05_prepare_cloud.py` compara as contagens com a origem, a soma das partições com o `ratings`
  e as contagens por ano com o bloco 1, e confirma os tipos e a compressão. Se tudo passar, grava
  `reports/cloud_manifest_<dataset>.md`.

O DDL é escrito à mão, em vez de usar um crawler do Glue, para os tipos ficarem iguais aos do
manifesto. As diferenças entre o Trino e o DuckDB (`CROSS JOIN UNNEST` nos géneros,
`approx_percentile` em vez de `MEDIAN`, `"timestamp"` entre aspas) estão no cabeçalho de cada
query. A query `06_ratings_desde_2015` mostra o partition pruning. A versão DuckDB está em
`sql/cloud/`, para não alterar o benchmark do bloco 2.

```bash
# Sem AWS: preparar os ficheiros, verificar o DDL, ver o SQL e correr só a parte DuckDB
python scripts/05_prepare_cloud.py --dataset small
python scripts/07_athena_setup.py --dry-run
python scripts/08_athena_benchmark.py --dry-run
python scripts/08_athena_benchmark.py --engines duckdb
```

### Custos

O Athena cobra 5 USD por TB lido, com um mínimo de 10 MB por query. O S3 custa cêntimos por mês
para estes tamanhos.

| Dataset | Lido no Athena (setup e benchmark) | Custo |
|---|---|---|
| `small` | poucos MB (conta o mínimo de 10 MB por query) | menos de 0,01 USD |
| `32m` | cerca de 12 GB, quase todos nas corridas sobre o CSV | cerca de 0,06 USD |

O orçamento do Learner Lab é limitado: testa sempre primeiro com o `small`.

### Erros comuns

| Sintoma | Causa | O que fazer |
|---|---|---|
| `ExpiredToken`, `InvalidClientTokenId` ou "as credenciais AWS não existem, expiraram ou são inválidas" | A sessão terminou ou o `~/.aws/credentials` é de uma sessão anterior. | "Start Lab" e copiar de novo o bloco de "AWS Details". |
| 0 linhas no `ratings_part` ou "contagens por ano diferentes" | As partições não foram registadas no catálogo. | Voltar a correr o passo `cloud`, que recria as tabelas e corre o `MSCK REPAIR TABLE` depois do upload. |
| Os buckets ou as tabelas desapareceram | O "Reset" do Learner Lab apaga buckets, objetos e catálogo. O "End Lab" não apaga. | Voltar a correr o passo `cloud`. |
| "o bucket ... existe mas pertence a outra conta" | Alguém já usa esse nome de bucket (os nomes são únicos em toda a AWS). | Repor `null` no `config.yaml` ou escolher outro nome. |

## Tecnologias

| Ferramenta | Para quê |
|---|---|
| [DuckDB](https://duckdb.org/) | SQL analítico embebido: conversão para Parquet e queries |
| [Apache Parquet](https://parquet.apache.org/) | Formato colunar comprimido em disco |
| [pandas](https://pandas.pydata.org/) e [Matplotlib](https://matplotlib.org/) | Tabelas já agregadas pelo DuckDB, relatórios e figuras |
| [Amazon S3](https://aws.amazon.com/s3/) | Ficheiros na cloud |
| [AWS Glue Data Catalog](https://aws.amazon.com/glue/) | Catálogo das tabelas |
| [Amazon Athena](https://aws.amazon.com/athena/) | SQL serverless (Trino) sobre o S3 |
| [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) | Upload, catálogo e queries a partir do Python |

## Equipa

| Nome | N.º de aluno |
|---|---|
| Tiago Felgueira | 20242047 |
| João Grave | 20251843 |
| Luis Pousada | 20250979 |
| Francisco Monteiro | 20251694 |

## Referências

- F. Maxwell Harper and Joseph A. Konstan. 2015. *The MovieLens Datasets: History and Context.*
  ACM Transactions on Interactive Intelligent Systems (TiiS) 5, 4: 19:1–19:19.
  https://doi.org/10.1145/2827872
- Raasveldt, M., & Mühleisen, H. (2019). *DuckDB: an Embeddable Analytical Database.* SIGMOD.
- Documentação do [DuckDB](https://duckdb.org/docs/).
