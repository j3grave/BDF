# Big Data Foundations: pipeline MovieLens

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/j3grave/BDF/blob/main/Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1.ipynb)

Trabalho de grupo da unidade curricular Big Data Foundations, da Pós-Graduação em Enterprise Data
Science & Analytics da NOVA IMS (2026).

O projeto tem duas partes:

1. Um notebook de laboratório que usa Parquet, DuckDB, Polars e Arrow sobre o MovieLens.
2. Um pipeline em scripts que leva o MovieLens do download até ao Amazon Athena e mede, em cada
   etapa, o efeito do formato e da escala (100 mil, 1 milhão e 32 milhões de avaliações).

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

Os dados não estão no repositório. O notebook e o pipeline descarregam-nos na primeira execução.
Depois de descarregado e normalizado, o 32M ocupa cerca de 1,2 GB, mais o Parquet.

## Estrutura do repositório

```
BDF/
├── Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1.ipynb   # notebook do lab
├── Lab_..._v1_3.ipynb, Lab_..._v2.ipynb                    # notebooks do Luís (análises e bots)
├── run_pipeline.py              # ponto de entrada do pipeline
├── config.yaml                  # dataset por omissão e secção aws
├── requirements.txt
├── scripts/
│   ├── common.py                # configuração, caminhos e escrita dos CSV de resultados
│   ├── 01_ingest.py             # passo ingest
│   ├── 02_to_parquet.py         # passo parquet
│   ├── 03_benchmark.py          # passo benchmark
│   ├── 04_eda.py                # passo eda
│   ├── 05_analises.py           # passo analises (queries do Luís e deteção de bots)
│   ├── 06_coordenacao.py        # coordenação entre contas (corre à mão)
│   ├── cloud_pipeline.py        # passo cloud: upload, catálogo e benchmark
│   ├── prepare_cloud.py         # ficheiros para o S3, em data/cloud/
│   ├── athena_common.py         # opções AWS e cliente do Athena
│   ├── athena_setup.py          # DDL no Glue Data Catalog e validação
│   └── athena_benchmark.py      # benchmark DuckDB vs Athena
├── sql/
│   ├── 01_...sql a 05_...sql    # perguntas do benchmark (DuckDB); 10_flag_bots.sql é só um esqueleto
│   ├── analise/                 # as 16 queries do passo analises (DuckDB)
│   ├── cloud/                   # query 06 do benchmark cloud, versão DuckDB
│   └── athena/
│       ├── ddl/                 # CREATE TABLE do Athena
│       ├── queries/             # queries 01 a 06 em Trino
│       └── analise/             # as 16 queries de sql/analise/ em Trino
├── docs/revisao_fase2.md        # revisão do código antes do merge da fase 2
├── reports/                     # manifestos da preparação para a cloud
├── results/                     # resultados leves (CSV, PNG e relatórios .md)
└── data/                        # não versionado: downloads, CSV, Parquet e data/cloud/
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
| `<dataset>/bots_coordenacao/` | Resultados do `06_coordenacao.py` |

## Ambiente

É preciso Python 3.10 ou superior, por causa do `polars>=1.37`. A versão testada é a 3.13: num
clone limpo, a 15/11/2026, o `python run_pipeline.py --dataset small` correu os cinco passos sem
erros.

```bash
git clone https://github.com/j3grave/BDF.git
cd BDF
python3.13 -m venv .venv          # ou python3.12
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

No macOS, o `python3` do sistema (`/usr/bin/python3`) é o 3.9 e não serve. Instala outra versão
(`brew install python@3.13` ou o instalador de python.org) e cria o ambiente com ela. Se já
tiveres um `.venv` feito com o 3.9, apaga-o e cria-o de novo. Com conda:
`conda create -n bdf python=3.13`, `conda activate bdf` e `pip install -r requirements.txt`.

## Pipeline local

```bash
python run_pipeline.py --dataset small                 # os cinco passos
python run_pipeline.py --dataset 1m --steps benchmark  # só um passo
```

Sem `--dataset`, usa o valor do `config.yaml`. Cada script também corre sozinho, por exemplo
`python scripts/02_to_parquet.py --dataset 1m`. Se um passo falhar, o pipeline pára.

| Passo | Script | O que faz |
|---|---|---|
| `ingest` | `01_ingest.py` | Descarrega o zip (só se ainda não existir) e grava CSV com o mesmo esquema nos três datasets. Converte os `.dat` do 1M (separador `::`, sem cabeçalho, latin-1). |
| `parquet` | `02_to_parquet.py` | Converte para Parquet com o `COPY` do DuckDB: uma versão sem partição e o `ratings` particionado por ano (em UTC). Regista os tamanhos. |
| `benchmark` | `03_benchmark.py` | Corre 3 vezes cada query de `sql/` nos dois Parquet e regista a mediana e o n.º de linhas. |
| `eda` | `04_eda.py` | Análise exploratória com as agregações no DuckDB: indicadores, qualidade das tabelas, 10 figuras e relatório. |
| `analises` | `05_analises.py` | Corre as 16 queries de `sql/analise/` e grava um CSV por query. Verifica a qualidade e a integridade dos dados e compara os totais com o `04_eda.py`. Se uma verificação falhar, o pipeline pára. |

Nas queries de `sql/`, `${ratings}` e `${movies}` são substituídos pela leitura do Parquet.

A pasta `data/<dataset>` pode ser um symlink para outra cópia onde os dados já existem, para não
repetir o `ingest` e o `parquet`:

```bash
mkdir -p data
ln -s "/caminho/para/outra/copia/BDF/data/32m" data/32m
```

## Análises e deteção de bots

> Provisório: as regras de deteção de bots e o teste de coordenação ainda estão a ser validados
> pelo Luís. Os números abaixo não são resultados finais.

### Passo `analises`

As queries vêm do notebook do Luís (células 108, 109 e 112). Foram passadas para `sql/analise/` e
corrigidas onde foi preciso: fuso horário, faixas de atividade e último ano incompleto. O relatório
dessa validação está arquivado no branch `arquivo/main-com-imdb`
(`git show arquivo/main-com-imdb:docs/validacao_queries_colega.md`). Cada query tem uma versão
Athena com o mesmo nome em `sql/athena/analise/`.

```bash
python scripts/05_analises.py --dataset small                  # o mesmo que o passo analises
python scripts/05_analises.py --dataset 1m --fonte csv         # lê os CSV em vez do Parquet
python scripts/05_analises.py --dataset small --emular-athena  # testa também as versões Athena
```

Com `--emular-athena`, as versões Athena correm no DuckDB, com macros que imitam as funções do
Trino, e cada resultado é comparado com o da versão DuckDB. Isto confirma a lógica, mas não a
sintaxe do Trino, que só se confirma no Athena.

A regra original de bots sinalizava sobretudo utilizadores acabados de registar: 34% de suspeitos
no small e 47% no 1M. O `sql/analise/10_flag_bots.sql` usa duas regras novas:

- regra A: ritmo sustentado depois das primeiras 24 horas, acima do quantil p99,9;
- regra B: registo extremo, com pelo menos 100 eventos e um intervalo mediano de 2 segundos ou menos.

Com elas, os suspeitos descem para 0,33% no small e 0,10% no 1M. As submissões em lote (10 ou mais
avaliações no mesmo segundo) são contadas à parte e não entram como bots.

### Coordenação entre contas (`06_coordenacao.py`)

Corre à mão, fora do `run_pipeline.py`, porque demora no 32M. Procura rajadas: várias contas a dar
a mesma nota extrema ao mesmo filme na mesma hora, longe da média do filme. Compara o número de
rajadas com uma linha de base em que os timestamps são baralhados dentro de cada filme.

```bash
python scripts/06_coordenacao.py --dataset 1m
python scripts/06_coordenacao.py --dataset 32m --repeticoes 200 --memoria 12GB
```

Os resultados ficam em `results/<dataset>/bots_coordenacao/`. Conclusão atual, ainda por validar:

- 1M: não há mais rajadas do que na linha de base. As mais fortes são de contas novas, no pico de
  registos de 20 e 21/11/2000.
- 32M: há mais rajadas do que na linha de base, mas o excesso fica todo antes da escala de meias
  estrelas (fevereiro de 2003) e explica-se pela mudança de escala. Com 200 permutações, nenhuma
  comparação passa a correção de Bonferroni.

## Fase cloud (AWS Academy Learner Lab)

Leva o dataset para o S3, regista as tabelas no Glue Data Catalog e compara o Athena com o DuckDB.
Cada colega corre-a na sua conta, com um só comando. Não é preciso configurar buckets nem
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

O passo `cloud` não corre por omissão. O `scripts/cloud_pipeline.py` faz, por ordem:

1. Confirma as credenciais. Se faltarem ou tiverem expirado, explica como as renovar.
2. Corre o `prepare_cloud.py` se `data/cloud/<pasta>/` não existir ou for mais antiga do que o Parquet.
3. Cria os buckets em `us-east-1`, se não existirem: `bdf26-g1-dados-<ID da conta>` e
   `bdf26-g1-resultados-<ID da conta>`. O ID da conta só aparece no ecrã e nunca é gravado. Para
   usar outros nomes, passa `--bucket-dados` e `--bucket-resultados` ou escreve-os no `config.yaml`.
4. Envia `data/cloud/<pasta>/` para o S3 com o `boto3`. Só envia ficheiros novos ou com outro
   tamanho e não apaga nada no S3.
5. Corre o `athena_setup.py --recriar`: base de dados `movielens_<dataset>`, quatro tabelas,
   partições (`MSCK REPAIR TABLE`, depois do upload) e comparação das contagens com os ficheiros locais.
6. Corre o `athena_benchmark.py`, se a validação passar. Uma query só é gravada em
   `results/cloud_benchmarks.csv` se devolver o mesmo n.º de linhas nos dois motores.

Pode voltar a correr-se: os buckets e os ficheiros que já existem são reaproveitados.

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

### Preparação dos ficheiros (`prepare_cloud.py`)

O passo `cloud` corre-o quando é preciso, mas também pode correr sozinho. Não contacta a AWS: só
grava em `data/cloud/<pasta>/` uma cópia exata do que vai para o S3.

```bash
python scripts/prepare_cloud.py --dataset small
```

```
data/cloud/ml-32m/                    # ml-latest-small no small, ml-1m no 1M
├── ratings/ratings.parquet           # sem partição
├── ratings_part/year=AAAA/*.parquet  # particionado por ano
├── ratings_csv/ratings.csv           # CSV, para comparar os bytes lidos no Athena
└── movies/movies.parquet
```

- Uma pasta por tabela, porque o Glue e o Athena tratam cada pasta como uma tabela. Só vão o
  `ratings` (em três versões) e o `movies`: o `tags` e o `links` não são usados por nenhuma query do Athena.
- Parquet com compressão zstd e os mesmos tipos da fase 1.
- Apaga e recria a pasta em cada execução.
- No fim, compara as contagens com a origem, a soma das partições com o `ratings` e as contagens
  por ano com a fase 1, e confirma os tipos e a compressão. Se alguma verificação falhar, termina
  com erro. Se passarem todas, grava `reports/cloud_manifest_<dataset>.md`.

### Catálogo e benchmark do Athena

| Script | O que faz |
|---|---|
| `athena_setup.py` | Corre o DDL de `sql/athena/ddl/`, carrega as partições e confirma que o n.º de linhas (total e por ano) é igual ao dos ficheiros locais. Antes de enviar o DDL, confirma, sem AWS, que as colunas e os tipos coincidem com `data/cloud/`. |
| `athena_benchmark.py` | Corre as queries de `sql/athena/queries/` no Athena e as mesmas perguntas no DuckDB sobre `data/cloud/`, em CSV, Parquet e Parquet particionado. Grava a mediana do tempo, o tempo no motor, os MB lidos e o n.º de linhas. |

O DDL é escrito à mão, em vez de usar um crawler do Glue, para os tipos ficarem iguais aos do
manifesto. As diferenças entre o Trino e o DuckDB (`CROSS JOIN UNNEST` nos géneros,
`approx_percentile` em vez de `MEDIAN`, `"timestamp"` entre aspas) estão no cabeçalho de cada
query. A query `06_ratings_desde_2015` mostra o partition pruning. A versão DuckDB está em
`sql/cloud/`, para não alterar o benchmark da fase 1.

```bash
# Sem AWS: verificar o DDL, ver o SQL e correr só a parte DuckDB
python scripts/athena_setup.py --dry-run
python scripts/athena_benchmark.py --dry-run
python scripts/athena_benchmark.py --engines duckdb

# Com AWS (normalmente basta o passo cloud)
python scripts/athena_setup.py --dataset small --recriar
python scripts/athena_benchmark.py --dataset small
```

## Notebook do lab

O notebook `Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1.ipynb` usa o `ml-latest-small`. Converte
os CSV para Parquet e compara os tamanhos, consulta o Parquet com DuckDB, transforma os dados com
Polars e passa-os ao DuckDB através do Arrow, sem cópia. Mostra também a leitura lazy do Polars
(projection e filter pushdown), guarda uma base de dados DuckDB e faz a análise exploratória.

Responde a quatro perguntas, cada uma em Polars e em SQL, e confirma que as duas dão o mesmo
resultado:

- Que géneros de filmes existem?
- Quantos filmes há por género?
- Como se distribuem as avaliações por utilizador?
- Que filmes têm a média de avaliação mais alta?

Para o correr no Colab, carrega no botão no topo desta página e faz "Runtime > Run all". A última
célula descarrega um `.zip` com o Parquet e a base de dados. Localmente, com o ambiente ativo,
corre `jupyter lab`. O notebook cria as pastas `ml-latest-small/`, `parquet/` e `output/`, que não
são versionadas.

## Tecnologias

| Ferramenta | Para quê |
|---|---|
| [DuckDB](https://duckdb.org/) | SQL analítico embebido: conversão para Parquet, queries e base de dados |
| [Apache Parquet](https://parquet.apache.org/) | Formato colunar comprimido em disco |
| [Polars](https://pola.rs/) | DataFrames no notebook, em modo eager e lazy |
| [Apache Arrow](https://arrow.apache.org/) | Formato colunar em memória, partilhado entre o Polars e o DuckDB |
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
- Documentação: [DuckDB](https://duckdb.org/docs/), [Polars](https://docs.pola.rs/),
  [Apache Arrow](https://arrow.apache.org/docs/).
