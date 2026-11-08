# Big Data Foundations — Lab: Parquet, DuckDB, Polars e Arrow

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/j3grave/BDF/blob/main/Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1.ipynb)

Trabalho desenvolvido no âmbito da unidade curricular **Big Data Foundations** da Pós-Graduação em
**Enterprise Data Science & Analytics** da **NOVA IMS** (2026).

O projeto explora ferramentas modernas de análise de dados local — formato **Parquet**, motor SQL
**DuckDB**, DataFrames **Polars** e formato em memória **Apache Arrow** — aplicadas ao dataset
**MovieLens**, e responde a um conjunto de perguntas de análise em **Python** e em **SQL**.

## Objetivos

1. Converter ficheiros CSV para **Parquet** com DuckDB e comparar tamanhos.
2. Consultar os ficheiros Parquet diretamente com **DuckDB SQL**, sem importação nem servidor.
3. Transformar dados com **Polars** e consultá-los a partir do DuckDB através de **Arrow** (sem cópia).
4. Ler Parquet de forma **lazy** com Polars e analisar o plano de execução (*projection* e *filter pushdown*).
5. Guardar tabelas numa **base de dados DuckDB** persistente e reabri-la.
6. **Análise exploratória (EDA)**: estrutura, tipos, estatísticas descritivas, valores em falta,
   classificação das variáveis e gráficos de distribuição.
7. Responder a quatro perguntas de análise, cada uma em **Polars** e em **SQL**, com verificação
   de que ambas as abordagens dão o mesmo resultado.

## Perguntas de análise

- Quais são os géneros de filmes no dataset?
- Qual é o número de filmes por género?
- Qual é a distribuição das avaliações por utilizador?
- Quais são os filmes com a média de avaliação mais alta?

## Dados

**MovieLens `ml-latest-small`** — 100 836 avaliações de 610 utilizadores sobre 9 742 filmes.

| Ficheiro | Conteúdo |
|---|---|
| `ratings.csv` | Avaliações (`userId`, `movieId`, `rating` de 0.5 a 5.0, `timestamp`) |
| `movies.csv` | Filmes (`movieId`, `title` com ano, `genres` separados por `\|`) |
| `tags.csv` | Etiquetas livres atribuídas pelos utilizadores |
| `links.csv` | Identificadores IMDb e TMDb de cada filme |

Os dados **não estão incluídos no repositório**: o notebook descarrega-os automaticamente de
[GroupLens](https://grouplens.org/datasets/movielens/) na primeira execução.

## Como executar

### Google Colab (recomendado)

1. Clicar no botão **Open in Colab** no topo desta página.
2. Executar todas as células por ordem (*Runtime → Run all*).
3. A célula final descarrega um `.zip` com os ficheiros Parquet e a base de dados DuckDB gerados.

### Localmente

Requer Python 3.10 ou superior.

```bash
git clone https://github.com/j3grave/BDF.git
cd BDF
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter lab                      # ou abrir o notebook no VS Code
```

## Estrutura do repositório

```
BDF/
├── Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1.ipynb   # notebook principal
├── requirements.txt                                       # dependências Python
├── .gitignore                                             # exclui dados e ficheiros gerados
└── README.md
```

Ao executar o notebook são criadas as pastas `ml-latest-small/` (CSV), `parquet/` e `output/`
(base de dados `movielens.duckdb`), que não são versionadas.

## Pipeline local

Pipeline reprodutível que descarrega o MovieLens, converte-o para Parquet com DuckDB e mede o tempo
das queries. Funciona com três tamanhos do dataset: `small` (100 mil ratings), `1m` (1 milhão)
e `32m` (32 milhões).

### Ambiente

Requer **Python 3.10 ou superior** (recomenda-se 3.12). O limite vem do `polars>=1.37`, que não
instala em Python 3.9; o DuckDB e o PyYAML aceitam versões mais antigas. Com 3.10 ou 3.11 a instalação
funciona, mas o pip escolhe versões um pouco mais antigas de numpy, pandas, matplotlib e pyarrow,
porque as mais recentes já exigem 3.11 ou 3.12.

Versão testada: **Python 3.13** (3.13.18, Homebrew, macOS). Num ambiente limpo, o
`pip install -r requirements.txt` instalou duckdb 2.0.0, polars 2.1.0, pandas 3.1.0, numpy 2.5.4,
matplotlib 3.11.2 e pyarrow 26.0.0, e `python run_pipeline.py --dataset small` correu os quatro
passos sem erros.

Antes de criar o ambiente, confirma a versão:

```bash
python3 --version
```

Atenção: no macOS, o `python3` que vem com o sistema (`/usr/bin/python3`) é o 3.9, que não serve.
Nesse caso instala uma versão mais recente (por exemplo `brew install python@3.12` ou o instalador
de python.org) e usa-a explicitamente para criar o ambiente, com uma destas opções:

```bash
# Opção A: venv com uma versão específica do Python
python3.12 -m venv .venv

# Opção B: ambiente conda (Anaconda/Miniconda)
conda create -n bdf python=3.12
conda activate bdf
```

O ambiente fica com a versão de Python usada para o criar. Se já existir um `.venv` feito com o 3.9,
apaga-o (`rm -rf .venv`) e cria-o de novo.

Na primeira vez, na pasta do repositório, cria-se um ambiente virtual e instalam-se as dependências
(com conda, salta as duas primeiras linhas e corre só o `pip install`):

```bash
python3 -m venv .venv            # ou python3.12 -m venv .venv (ver acima)
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Nas sessões seguintes basta ativar o ambiente (`source .venv/bin/activate`). Com o ambiente ativo,
`python` é o do `.venv`, que já tem o DuckDB e o PyYAML instalados. Para confirmar:

```bash
python -c "import duckdb, yaml; print('duckdb', duckdb.__version__)"
```

### Como correr

Com o ambiente ativo:

```bash
python run_pipeline.py --dataset small                 # todos os passos
python run_pipeline.py --dataset 1m --steps benchmark  # só um passo
```

Os passos são `ingest`, `parquet`, `benchmark`, `eda` e `analises`. Sem `--dataset` usa-se o valor de `config.yaml`.
Há ainda o passo `cloud` (fase 2, usa a AWS), que só corre quando é pedido: ver
[Fase cloud](#fase-cloud-aws-academy-learner-lab).
Cada script em `scripts/` também corre isolado, por exemplo `python scripts/02_to_parquet.py --dataset 1m`.

| Passo | Script | O que faz |
|---|---|---|
| `ingest` | `scripts/01_ingest.py` | Descarrega o zip do GroupLens, só se ainda não existir, e normaliza para CSV com o esquema comum (`ratings`: userId, movieId, rating, timestamp; `movies`: movieId, title, genres). Converte os `.dat` do 1M (separador `::`, sem cabeçalho, latin-1). |
| `parquet` | `scripts/02_to_parquet.py` | `COPY` do DuckDB para Parquet sem partição e `ratings` particionado por ano (`PARTITION_BY year`, ano em UTC). Regista os tamanhos do CSV e do Parquet. |
| `benchmark` | `scripts/03_benchmark.py` | Corre cada query de `sql/` 3 vezes sobre os dois formatos de Parquet e regista a mediana do tempo e o n.º de linhas. |
| `eda` | `scripts/04_eda.py` | Análise exploratória com agregações no DuckDB: indicadores, qualidade das tabelas, 10 figuras (paleta NOVA IMS) e relatório em Markdown. |

Nas queries de `sql/`, `${ratings}` e `${movies}` são substituídos pela leitura do Parquet. Os dois
formatos têm as mesmas colunas, incluindo `year`. `10_flag_bots.sql` é um esqueleto e é ignorado
enquanto só tiver comentários.

### Estrutura de pastas

```
BDF/
├── config.yaml                 # dataset (small | 1m | 32m), data_dir, results_dir
├── run_pipeline.py             # ponto de entrada
├── scripts/
│   ├── common.py               # configuração, caminhos e registo de resultados
│   ├── 01_ingest.py
│   ├── 02_to_parquet.py
│   ├── 03_benchmark.py
│   ├── 04_eda.py
│   ├── cloud_pipeline.py       # fase 2: passo cloud (upload, catálogo e benchmark num só comando)
│   ├── prepare_cloud.py        # fase 2: ficheiros para o S3 (ver "Preparação para a cloud")
│   ├── athena_common.py        # fase 2: opções AWS e cliente mínimo do Athena
│   ├── athena_setup.py         # fase 2: DDL no Glue Data Catalog e validação
│   └── athena_benchmark.py     # fase 2: benchmark DuckDB vs Athena
├── sql/                        # 01–05: perguntas de análise e query temporal; 10: bots
│   ├── athena/ddl/             # fase 2: CREATE TABLE para o Athena
│   ├── athena/queries/         # fase 2: queries 01–06 no dialeto do Athena (Trino)
│   └── cloud/                  # fase 2: queries extra no dialeto DuckDB (06)
├── data/<dataset>/             # não versionado; pode ser um symlink (ver abaixo)
│   ├── raw/                    # zip e ficheiros originais
│   ├── csv/                    # CSV normalizados
│   └── parquet/                # <tabela>.parquet e ratings_by_year/year=AAAA/
├── data/cloud/<pasta>/         # não versionado: espelho do que vai para o S3
├── reports/                    # versionado: cloud_manifest_<dataset>.md
└── results/                    # versionado (resultados leves: CSV, PNG, .md)
    ├── sizes.csv               # tamanhos CSV vs Parquet vs Parquet por ano, e tempo de cada conversão
    ├── pipeline_runs.csv       # tempo de cada passo
    ├── benchmarks.csv          # dataset, query, formato, mediana do tempo, n.º de linhas
    ├── cloud_benchmarks.csv    # fase 2: DuckDB vs Athena (tempo, MB lidos, n.º de linhas)
    └── <dataset>/eda/          # figuras PNG, eda_indicadores.csv, eda_resumo_tabelas.csv, eda_relatorio.md
```

O dataset 32M ocupa cerca de 1.2 GB depois de descarregado e normalizado (zip, CSV), mais o Parquet.

`data/<dataset>` pode ser um symlink para outra localização, por exemplo outra cópia do repositório
onde os dados já foram descarregados e convertidos. Assim não é preciso repetir o `ingest` e o
`parquet`. Como `data/` está no `.gitignore`, o symlink não é versionado:

```bash
mkdir -p data
ln -s "/caminho/para/outra/copia/BDF/data/32m" data/32m
```

## Fase cloud (AWS Academy Learner Lab)

Leva o dataset para a AWS (S3 → Glue Data Catalog → Athena) e compara o Athena com o DuckDB, na
conta AWS de cada um, com um único comando. Não é preciso configurar buckets nem instalar a AWS CLI.

### Pré-requisitos

- O ambiente da secção [Ambiente](#ambiente), com o `requirements.txt` instalado (inclui o `boto3`).
  Não é preciso a AWS CLI: o upload é feito pelo próprio pipeline.
- Os passos `ingest` e `parquet` do dataset já corridos, por exemplo
  `python run_pipeline.py --dataset small --steps ingest parquet`.
- Uma sessão do Learner Lab ativa (indicador verde).

### Credenciais (em cada sessão do lab)

As credenciais do Learner Lab são temporárias: mudam a cada "Start Lab" e expiram ao fim de
cerca de 4 horas. Em cada sessão:

1. "Start Lab" e esperar que o indicador fique verde.
2. "AWS Details" > "AWS CLI: Show" e copiar o bloco `[default]` (as três linhas, incluindo `aws_session_token`).
3. Escrever o bloco em `~/.aws/credentials`, substituindo o anterior:

   ```bash
   mkdir -p ~/.aws && pbpaste > ~/.aws/credentials     # macOS: escreve o que está copiado
   ```

   No Windows e no Linux, colar à mão num editor (`%UserProfile%\.aws\credentials` no Windows).

O ficheiro fica fora do repositório. As credenciais nunca vão para o `config.yaml` nem para o git.

### Comando único

```bash
python run_pipeline.py --dataset small --steps cloud
```

O passo `cloud` não faz parte dos passos por omissão: só corre quando é pedido com `--steps cloud`.
O script é o `scripts/cloud_pipeline.py` e faz, por ordem:

1. **Credenciais.** Se faltarem ou tiverem expirado, termina e explica como as renovar.
2. **`data/cloud/<pasta>/`.** Corre o `prepare_cloud.py` se a pasta não existir ou for mais antiga
   do que o Parquet da fase 1 (ver [Preparação para a cloud](#preparação-para-a-cloud)).
3. **Buckets.** Cria-os em `us-east-1`, se ainda não existirem. Os nomes vêm do ID da conta:
   `bdf26-g1-dados-<ID da conta>` e `bdf26-g1-resultados-<ID da conta>`. Para usar outros, passa
   `--bucket-dados` e `--bucket-resultados` ou escreve-os na secção `aws` do `config.yaml`.
   O ID da conta só aparece no ecrã e nunca é escrito em ficheiros do repositório.
4. **Upload** de `data/cloud/<pasta>/` para `s3://<bucket-dados>/<pasta>/`, com o `boto3`. Só envia
   os ficheiros novos ou com tamanho diferente, como o `aws s3 sync`, e mostra a percentagem nos
   ficheiros grandes. Não apaga nada no S3.
5. **Catálogo.** `athena_setup.py --recriar`: base de dados `movielens_<dataset>`, seis tabelas,
   partições (`MSCK REPAIR TABLE`) e validação das contagens contra os ficheiros locais. Corre depois
   do upload, para o `MSCK REPAIR TABLE` ver as partições no S3.
6. **Benchmark.** `athena_benchmark.py`, só se a validação do passo 5 passar. As linhas só são
   escritas em `results/cloud_benchmarks.csv` se cada query devolver o mesmo n.º de linhas no DuckDB
   e no Athena.

Se algum passo falhar, o pipeline pára com erro. Pode voltar a correr-se: os buckets já existentes e os
ficheiros já enviados são reaproveitados.

### Custos esperados

O Athena cobra 5 USD por TB lido, com um mínimo de 10 MB por query. O S3, para estes tamanhos, custa
cêntimos por mês.

| Dataset | Dados lidos no Athena (setup + benchmark) | Custo aproximado |
|---|---|---|
| `small` | poucos MB (conta o mínimo de 10 MB por query) | < 0,01 USD |
| `32m` | cerca de 12 GB, quase tudo nas corridas sobre o CSV | ≈ 0,06 USD por benchmark |

O Learner Lab tem um orçamento limitado: testa sempre primeiro com o `small`.

### Erros comuns

| Sintoma | Causa | O que fazer |
|---|---|---|
| `ExpiredToken`, `InvalidClientTokenId` ou "as credenciais AWS não existem, expiraram ou são inválidas" | A sessão do lab terminou ou o `~/.aws/credentials` tem credenciais de uma sessão anterior. | "Start Lab" e copiar de novo o bloco de "AWS Details" (ver acima). |
| O Athena devolve 0 linhas no `ratings_part`, ou a validação diz "contagens por ano diferentes" | As partições não estão registadas no catálogo: o `MSCK REPAIR TABLE` correu antes do upload ou não correu. | Voltar a correr `python run_pipeline.py --dataset small --steps cloud`. O setup recria as tabelas e corre o `MSCK REPAIR TABLE` depois do upload. |
| Os buckets ou as tabelas desapareceram | O "Reset" do Learner Lab apaga todos os recursos da conta (buckets, objetos e o catálogo do Glue). Um simples "End Lab" não os apaga. | Voltar a correr o comando único: os buckets são recriados e os dados reenviados. |
| "o bucket ... existe mas pertence a outra conta" | Os nomes de buckets são únicos em toda a AWS. Só acontece se escreveres à mão um nome já usado por outra pessoa. | Repor `null` no `config.yaml` ou escolher outro nome. |

## Preparação para a cloud

O passo `cloud` corre este script automaticamente quando é preciso; também pode correr-se sozinho.
O script `scripts/prepare_cloud.py` só prepara os ficheiros localmente, sem chamadas à AWS. Gera em
`data/cloud/<pasta>/` um espelho exato do que vai para o S3. Precisa dos resultados dos passos
`ingest` e `parquet` do dataset.

```bash
python scripts/prepare_cloud.py --dataset small   # teste rápido
python scripts/prepare_cloud.py                   # por omissão: o dataset do config.yaml
```

Estrutura gerada (para o 32M, `<pasta>` = `ml-32m`; para o small, `ml-latest-small`; para o 1M, `ml-1m`):

```
data/cloud/ml-32m/
├── ratings/ratings.parquet           # ratings, sem partição
├── ratings_part/year=AAAA/*.parquet  # ratings particionado por ano (year só no nome da pasta)
├── ratings_csv/ratings.csv           # cópia do CSV, para comparar bytes lidos no Athena
├── movies/movies.parquet
├── tags/tags.parquet
└── links/links.parquet
```

- Uma pasta por tabela, e cada pasta só tem ficheiros dessa tabela. O Glue e o Athena tratam cada
  pasta como uma tabela, por isso não há ficheiros soltos na raiz.
- Parquet com compressão zstd (a fase 1 usa snappy) e os mesmos tipos da fase 1, sem casts.
- O ano é `year(to_timestamp("timestamp"))` em UTC, igual à fase 1.
- O script é idempotente: apaga e recria `data/cloud/<pasta>/` em cada execução.
- No fim, verifica:
  - as contagens de linhas contra a origem;
  - a soma das partições contra `ratings`;
  - as contagens por ano contra o `ratings_by_year` da fase 1;
  - os tipos, a compressão e a estrutura das pastas.
- Se alguma verificação falhar, termina com erro e não gera o manifesto. Se tudo passar, escreve
  `reports/cloud_manifest_<dataset>.md` com, por tabela, o caminho, o n.º de ficheiros, o tamanho, o
  n.º de linhas, o schema e os tipos para o DDL do Athena, mais a lista de anos do `ratings_part`.
- O benchmark DuckDB vs Athena deve ler os ficheiros de `data/cloud/`, que são os mesmos que vão para o S3.

O upload para o S3 é feito pelo passo `cloud` (ver [Fase cloud](#fase-cloud-aws-academy-learner-lab)).

As credenciais AWS (`.aws/`, `*.env`, ficheiros de chaves) estão no `.gitignore` e nunca devem ser versionadas.

## Athena: catálogo e benchmark

Depois do upload, dois scripts tratam do resto. O passo `cloud` corre-os pela ordem certa; também
podem correr-se sozinhos. Ambos usam o `boto3`, que está no `requirements.txt`.

| Script | O que faz |
|---|---|
| `scripts/athena_setup.py` | Corre o DDL de `sql/athena/ddl/` para criar no Glue Data Catalog a base de dados `movielens_<dataset>` e as seis tabelas. Carrega as partições de `ratings_part` com `MSCK REPAIR TABLE` e confirma que o n.º de linhas (total e por ano) é igual ao dos ficheiros locais. Antes de enviar o DDL, verifica, sem AWS, que as colunas e os tipos coincidem com `data/cloud/`. |
| `scripts/athena_benchmark.py` | Corre as queries de `sql/athena/queries/` no Athena e as mesmas perguntas no DuckDB, sobre `data/cloud/`. As queries com ratings correm em CSV, Parquet e Parquet particionado. Regista a mediana do tempo, o tempo no motor, os MB lidos (o que o Athena cobra) e o n.º de linhas em `results/cloud_benchmarks.csv`. |

Usamos DDL escrito à mão em vez de um crawler do Glue para os tipos ficarem exatamente os do manifesto.
As queries do Athena estão no dialeto Trino. As diferenças para o DuckDB estão explicadas no
cabeçalho de cada ficheiro:

- `CROSS JOIN UNNEST` para os géneros;
- `approx_percentile` em vez de `MEDIAN`;
- `"timestamp"` entre aspas.

A query `06_ratings_desde_2015` (`WHERE year >= 2015`) é nova na fase 2. Mostra o partition pruning
e, para não alterar o benchmark da fase 1, a versão DuckDB está em `sql/cloud/`.

As credenciais e os buckets são os da [Fase cloud](#fase-cloud-aws-academy-learner-lab). Sem
`--dataset`, os scripts usam o dataset do `config.yaml`, como os outros passos. Sem
`--bucket-dados`/`--bucket-resultados`, usam os do `config.yaml` ou, se aí estiverem a `null`, os
derivados do ID da conta.

```bash
# Sem AWS: verificar o DDL, ver o SQL que seria enviado e correr só a parte DuckDB
python scripts/athena_setup.py --dry-run
python scripts/athena_benchmark.py --dry-run
python scripts/athena_benchmark.py --engines duckdb

# Com AWS (depois do upload; normalmente basta o passo cloud)
python scripts/athena_setup.py --dataset small --recriar
python scripts/athena_benchmark.py --dataset small
```

O benchmark completo do 32M lê cerca de 12 GB no Athena. Quase tudo vem das 12 corridas sobre o
CSV, que leem 877 MB cada. A 5 USD por TB, custa cerca de 0,06 USD.

## Tecnologias

| Ferramenta | Função no projeto |
|---|---|
| [DuckDB](https://duckdb.org/) | Motor SQL analítico embebido: conversão para Parquet, consultas e base de dados persistente |
| [Polars](https://pola.rs/) | DataFrames em Python, modos *eager* e *lazy* |
| [Apache Parquet](https://parquet.apache.org/) | Formato colunar comprimido em disco |
| [Apache Arrow](https://arrow.apache.org/) | Formato colunar em memória, partilhado sem cópia entre Polars e DuckDB |
| [Matplotlib](https://matplotlib.org/) | Visualização |

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
- Documentação oficial: [DuckDB](https://duckdb.org/docs/), [Polars](https://docs.pola.rs/),
  [Apache Arrow](https://arrow.apache.org/docs/).
