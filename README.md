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
│   ├── 04_analise.py              # bloco 3, análise dos dados: EDA e análises
│   ├── 05_prepare_cloud.py        # bloco 4, cloud: ficheiros para o S3, em data/cloud/
│   ├── 06_upload_s3.py            # bloco 4: buckets e upload
│   ├── 07_athena_setup.py         # bloco 4: catálogo no Glue e validação das contagens
│   ├── 08_athena_benchmark.py     # bloco 4: benchmark DuckDB vs Athena
│   └── athena_common.py           # partilhado pelo bloco 4: configuração AWS e cliente do Athena
├── sql/
│   ├── 01_...sql a 05_...sql      # perguntas do benchmark (DuckDB)
│   ├── analise/                   # as 17 queries da análise (DuckDB)
│   ├── cloud/                     # query 06 do benchmark cloud, versão DuckDB
│   └── athena/
│       ├── ddl/                   # CREATE TABLE do Athena
│       └── queries/               # queries 01 a 06 em Trino
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
| `<dataset>/analises/` | Um CSV por query e `analises_relatorio.md` |

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
python run_pipeline.py
```

O pipeline corre só com este comando e faz as perguntas no terminal (escreve o número da opção, ou
Enter para a opção marcada):

1. o dataset: `small`, `1m` ou `32m` (o Enter escolhe o do `config.yaml`);
2. o que correr: só o pipeline local (blocos 1 a 3), o local e a cloud, ou só a cloud;
3. se atualiza os resultados do repositório. Por omissão não atualiza: grava em `results_local/`,
   que não está no git, e uma corrida de teste não deixa alterações para commit. Para atualizar
   `results/` (por exemplo, antes de uma entrega), responde "sim".

Se escolheres a cloud, o pipeline confirma logo as credenciais AWS e só as pede se faltarem ou
tiverem expirado (ver [Credenciais](#credenciais)). Se um script falhar, o pipeline pára.

Os passos que já foram feitos não se repetem: o download só acontece se o zip não existir, a
conversão para Parquet só se o Parquet não existir (ou se o CSV for mais recente) e a pasta
`data/cloud/` só é preparada de novo se estiver desatualizada ou não passar as verificações.

| Bloco | Passo | Scripts |
|---|---|---|
| 1. Preparação dos dados | `ingest`, `parquet` | `01_ingest.py`, `02_to_parquet.py` |
| 2. Desempenho local | `benchmark` | `03_benchmark.py` |
| 3. Análise dos dados | `analise` | `04_analise.py` |
| 4. Cloud | `cloud` (só quando se escolhe no menu) | `05_prepare_cloud.py` a `08_athena_benchmark.py` |

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
| `02_to_parquet.py` | Converte para Parquet com o `COPY` do DuckDB: uma versão sem partição e o `ratings` particionado por ano (em UTC). Regista os tamanhos. Uma tabela que já tenha o Parquet, mais recente do que o CSV, não é convertida de novo. |

## Bloco 2: desempenho local

O `03_benchmark.py` corre cada query de `sql/` nos dois Parquet e regista a mediana do tempo e o
n.º de linhas. Nas queries, `${ratings}` e `${movies}` são substituídos pela leitura do Parquet.

**N.º de corridas (`RUNS`).** Cada query corre `RUNS` vezes por formato e guarda-se a mediana, que
é menos sensível a uma corrida invulgarmente lenta do que a média. A variável está no início de
dois scripts, ambos com 3:

| Script | O que conta | Efeito de aumentar |
|---|---|---|
| `scripts/03_benchmark.py` | corridas de cada query em cada Parquet (bloco 2) | mais tempo de execução |
| `scripts/08_athena_benchmark.py` | corridas de cada query em cada formato, no DuckDB e no Athena (bloco 4) | mais tempo e mais custo: cada corrida no Athena é cobrada (mínimo de 10 MB por query) |

Para mudar, altera o valor no script (por exemplo, `RUNS = 5`). As linhas dos CSV de resultados
têm a coluna `runs` no benchmark cloud, por isso corridas com valores diferentes continuam a
distinguir-se.

## Bloco 3: análise dos dados

O `04_analise.py` tem duas partes:

1. **Análise exploratória (EDA):** indicadores, qualidade das tabelas, 10 figuras e relatório.
2. **Análises:** as 17 queries de `sql/analise/` (qualidade, integridade, evolução no tempo,
   filmes, uso da escala, registo e utilizadores suspeitos), um CSV por query. Verifica a qualidade
   e a integridade dos dados e compara os totais com a EDA. Se uma verificação falhar, o pipeline pára.

**As primeiras 24 horas** (`sql/analise/registo_24h.sql`). Ao criar a conta, o MovieLens pedia
avaliações para começar a recomendar, e o GroupLens só inclui utilizadores com 20 ou mais. Por isso
o registo tem sempre um pico de atividade:

| Indicador | small | 1M |
|---|---:|---:|
| Utilizadores com 20 ou mais avaliações nas primeiras 24 h | 94,1% | 93,8% |
| Chegam à 20.ª avaliação em menos de 10 min | 64,9% | 60,6% |
| Chegam à 20.ª avaliação em menos de 1 h | 88,5% | 90,2% |
| Tempo mediano até à 20.ª avaliação | 6,3 min | 8,2 min |
| Utilizadores com toda a atividade nas primeiras 24 h | 59,3% | 62,9% |

Um pico no registo é o uso normal e não distingue um bot de uma pessoa, por isso a deteção de
bots ignora as primeiras 24 horas. O custo dessa escolha está na última linha: os utilizadores que
só avaliaram no registo (cerca de 60%) não podem ser sinalizados.

**Utilizadores suspeitos** (`sql/analise/10_flag_bots.sql`). Uma regra simples, baseada em muita
atividade, sinalizava 34% dos utilizadores do small e 47% do 1M, quase todos por causa do registo.
A query usa agora uma só regra, com um limiar fixo:

- regra A: 100 ou mais eventos numa janela de 10 minutos, depois das primeiras 24 horas (um evento
  a cada 6 segundos, durante 10 minutos seguidos).

Um evento é o conjunto das avaliações gravadas no mesmo segundo pelo mesmo utilizador. Com esta
regra, os suspeitos são 2 no small (0,33%: os utilizadores 380 e 610) e nenhum no 1M, onde o
máximo é 45 eventos em 10 minutos. O `10_flag_bots_calibracao.sql` mostra quantos ficariam
sinalizados com 50, 60 e 100 eventos. As submissões em lote (10 ou mais avaliações no mesmo
segundo) são contadas à parte e não entram como bots.

## Bloco 4: cloud (AWS Academy Learner Lab)

Leva o dataset para o S3, regista as tabelas no Glue Data Catalog e compara o Athena com o DuckDB.
Cada colega corre-o na sua conta, escolhendo a cloud no menu do `run_pipeline.py`. Não é preciso
configurar buckets nem instalar a AWS CLI.

### Antes de começar

- O ambiente da secção [Ambiente](#ambiente) (o `boto3` está no `requirements.txt`).
- Os passos `ingest` e `parquet` já corridos para o dataset.
- Uma sessão do Learner Lab ativa (indicador verde).

### Credenciais

As credenciais do Learner Lab mudam a cada "Start Lab" e expiram ao fim de cerca de 4 horas. Não
é preciso preparar nada antes: quando se escolhe a cloud, o `run_pipeline.py` confirma as
credenciais e, se não existirem ou tiverem expirado, pede-as uma a uma:

1. No Learner Lab, "Start Lab" e esperar pelo indicador verde.
2. "AWS Details" > "AWS CLI: Show".
3. Copiar e colar no terminal, quando o pipeline pedir, o valor de `aws_access_key_id`, depois o de
   `aws_secret_access_key` e por fim o de `aws_session_token` (só o que está depois do `=`), com Enter
   depois de cada um. O pipeline mostra quantos caracteres recebeu: o token tem centenas.

O pipeline grava-as em `.aws/credentials`, dentro da pasta do projeto, só com permissão de leitura
para o próprio utilizador, e confirma-as de novo. A pasta `.aws/` está no `.gitignore`: as
credenciais nunca vão para o git nem para o `config.yaml`, e o `~/.aws/` pessoal não é alterado.

### O que acontece

O passo `cloud` corre quatro scripts, por ordem, e pára se algum falhar:

1. **`05_prepare_cloud.py`** grava em `data/cloud/<pasta>/` uma cópia exata do que vai para o S3 e
   verifica-a. Se a pasta já existir, for mais recente do que o Parquet e passar as verificações,
   não faz nada. Não contacta a AWS.
2. **`06_upload_s3.py`** cria os buckets em `us-east-1` se não existirem
   (`bdf26-g1-dados-<ID da conta>` e `bdf26-g1-resultados-<ID da conta>`) e envia os ficheiros novos
   ou alterados (outro tamanho ou data mais recente). Não apaga nada no S3. O ID da conta só aparece
   no ecrã e nunca é gravado. Para usar outros nomes, escreve-os no `config.yaml`.
3. **`07_athena_setup.py`** cria a base de dados `movielens_<dataset>` e as quatro tabelas (apaga-as
   antes, se existirem), carrega as partições (`MSCK REPAIR TABLE`, depois do upload) e compara as
   contagens (total e por ano) com os ficheiros locais. Antes de enviar o DDL, confirma que as
   colunas e os tipos coincidem com `data/cloud/`.
4. **`08_athena_benchmark.py`** corre as queries de `sql/athena/queries/` no Athena e as mesmas
   perguntas no DuckDB sobre `data/cloud/`, em CSV, Parquet e Parquet particionado. Uma query só é
   gravada em `results/cloud_benchmarks.csv` se devolver o mesmo n.º de linhas nos dois motores.

Os scripts 07 e 08 guardam cada query em **Saved queries** do Athena, com nomes como
`movielens_32m - ddl 01_ratings` ou `movielens_32m - 06_ratings_desde_2015 [parquet_part]`. Se o
nome já existir, a query é atualizada em vez de duplicada. No histórico (**Recent queries**), as
SELECT começam por um comentário com o mesmo nome, para se saber qual é cada execução. Se a conta
não deixar guardar queries, o script avisa e continua.

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
- O `ratings.csv` vai de propósito: é a base de comparação que mostra quanto o Athena lê (e cobra)
  em CSV face ao Parquet. No 32M são 877 MB, contra cerca de 159 MB em Parquet.
- Parquet com compressão zstd e os mesmos tipos do bloco 1.
- O `05_prepare_cloud.py` compara as contagens com a origem, a soma das partições com o `ratings`
  e as contagens por ano com o bloco 1, e confirma os tipos e a compressão.

O DDL é escrito à mão, em vez de usar um crawler do Glue, para os tipos ficarem iguais aos dos
ficheiros. As diferenças entre o Trino e o DuckDB (`CROSS JOIN UNNEST` nos géneros,
`approx_percentile` em vez de `MEDIAN`, `"timestamp"` entre aspas) estão no cabeçalho de cada
query. A query `06_ratings_desde_2015` mostra o partition pruning. A versão DuckDB está em
`sql/cloud/`, para não alterar o benchmark do bloco 2.

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
| `ExpiredToken`, `InvalidClientTokenId` ou "as credenciais AWS não existem, expiraram ou são inválidas" | A sessão terminou ou o `.aws/credentials` do projeto é de uma sessão anterior. | Voltar a correr `python run_pipeline.py` e colar as chaves novas quando as pedir. |
| As chaves novas são pedidas outra vez, em ciclo | Há `AWS_ACCESS_KEY_ID` nas variáveis de ambiente, que têm prioridade sobre o ficheiro. | Fechar o terminal ou correr `unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN`. |
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
