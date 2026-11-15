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

Na fase 3 junta-se o **IMDb** (`title.ratings` e `title.basics`), como dataset complementar:
ver [Fase 3: IMDb](#fase-3-imdb-como-dataset-complementar).

O pipeline em scripts funciona também com o **MovieLens 1M** (1 000 209 avaliações, formato
`.dat`) e o **MovieLens 32M** (32 milhões de avaliações): ver [Pipeline local](#pipeline-local).

Os dados **não estão incluídos no repositório**: o notebook e o pipeline descarregam-nos
automaticamente de [GroupLens](https://grouplens.org/datasets/movielens/) na primeira execução.

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

O repositório tem duas partes: os notebooks do lab e um pipeline em scripts, que leva o MovieLens
do download até ao Athena na AWS.

```
BDF/
├── Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1.ipynb   # notebook principal do lab
├── Lab_..._v1_3.ipynb, Lab_..._v2.ipynb                    # notebook do Luís (análises e bots)
├── run_pipeline.py                                        # ponto de entrada do pipeline
├── config.yaml                                            # dataset por omissão e secção aws
├── scripts/                                               # um script por passo (ver "Pipeline local")
├── sql/                                                   # queries DuckDB e Athena
├── docs/                                                  # validação das queries do Luís e revisão
├── reports/                                               # manifestos da preparação para a cloud
├── results/                                               # resultados leves (CSV, PNG, .md)
├── requirements.txt                                       # dependências Python
├── .gitignore                                             # exclui dados, credenciais e ficheiros gerados
└── README.md
```

A estrutura detalhada do pipeline está em [Estrutura de pastas](#estrutura-de-pastas).

Ao executar o notebook são criadas as pastas `ml-latest-small/` (CSV), `parquet/` e `output/`
(base de dados `movielens.duckdb`), que não são versionadas.

## Pipeline local

Pipeline reprodutível que descarrega o MovieLens, converte-o para Parquet com DuckDB e mede o tempo
das queries. Funciona com três tamanhos do dataset: `small` (100 mil ratings), `1m` (1 milhão)
e `32m` (32 milhões).

### Ambiente

Requer **Python 3.10 ou superior** (recomenda-se 3.12 ou 3.13). O limite vem do `polars>=1.37`, que não
instala em Python 3.9; o DuckDB e o PyYAML aceitam versões mais antigas. Com 3.10 ou 3.11 a instalação
funciona, mas o pip escolhe versões um pouco mais antigas de numpy, pandas, matplotlib e pyarrow,
porque as mais recentes já exigem 3.11 ou 3.12.

Versão testada: **Python 3.13** (3.13.18, Homebrew, macOS). Num ambiente limpo, o
`pip install -r requirements.txt` instalou duckdb 2.0.0, polars 2.1.0, pandas 3.1.1, numpy 2.5.4,
matplotlib 3.11.2, pyarrow 26.0.1 e boto3 1.44.3, e `python run_pipeline.py --dataset small` correu
os cinco passos sem erros (teste de 15/11/2026, num clone limpo).

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
Há ainda dois passos que só correm quando são pedidos: `cloud` (fase 2, usa a AWS; ver
[Fase cloud](#fase-cloud-aws-academy-learner-lab)) e `imdb` (fase 3; ver
[Fase 3: IMDb](#fase-3-imdb-como-dataset-complementar)).
Cada script em `scripts/` também corre isolado, por exemplo `python scripts/02_to_parquet.py --dataset 1m`.

| Passo | Script | O que faz |
|---|---|---|
| `ingest` | `scripts/01_ingest.py` | Descarrega o zip do GroupLens, só se ainda não existir, e normaliza para CSV com o esquema comum (`ratings`: userId, movieId, rating, timestamp; `movies`: movieId, title, genres). Converte os `.dat` do 1M (separador `::`, sem cabeçalho, latin-1). |
| `parquet` | `scripts/02_to_parquet.py` | `COPY` do DuckDB para Parquet sem partição e `ratings` particionado por ano (`PARTITION_BY year`, ano em UTC). Regista os tamanhos do CSV e do Parquet. |
| `benchmark` | `scripts/03_benchmark.py` | Corre cada query de `sql/` 3 vezes sobre os dois formatos de Parquet e regista a mediana do tempo e o n.º de linhas. |
| `eda` | `scripts/04_eda.py` | Análise exploratória com agregações no DuckDB: indicadores, qualidade das tabelas, 10 figuras (paleta NOVA IMS) e relatório em Markdown. |
| `analises` | `scripts/05_analises.py` | Corre as 16 queries de `sql/analise/` (queries do notebook do Luís, revistas, e a deteção de bots) e grava um CSV por query em `results/<dataset>/analises/`. Verifica a qualidade e a integridade dos dados e compara os totais com o `04_eda.py`; se alguma verificação falhar, o pipeline pára. Ver [Análises e deteção de bots](#análises-e-deteção-de-bots). |

Nas queries de `sql/`, `${ratings}` e `${movies}` são substituídos pela leitura do Parquet. Os dois
formatos têm as mesmas colunas, incluindo `year`. `sql/10_flag_bots.sql` é só um esqueleto e é
ignorado pelo benchmark; a deteção de bots está em `sql/analise/10_flag_bots.sql`.

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
│   ├── 05_analises.py          # análises do Luís e deteção de bots (passo analises)
│   ├── 06_coordenacao.py       # coordenação entre contas (corre à mão, fora do pipeline)
│   ├── 07_imdb.py              # fase 3: IMDb vs MovieLens (passo imdb, só a pedido)
│   ├── prepare_cloud_imdb.py   # fase 3: IMDb para o S3 (data/cloud/imdb/)
│   ├── cloud_pipeline.py       # fase 2: passo cloud (upload, catálogo e benchmark num só comando)
│   ├── prepare_cloud.py        # fase 2: ficheiros para o S3 (ver "Preparação para a cloud")
│   ├── athena_common.py        # fase 2: opções AWS e cliente mínimo do Athena
│   ├── athena_setup.py         # fase 2: DDL no Glue Data Catalog e validação
│   └── athena_benchmark.py     # fase 2: benchmark DuckDB vs Athena
├── sql/                        # 01–05: perguntas de análise e query temporal; 10: esqueleto
│   ├── analise/                # 16 queries do passo analises (DuckDB), incluindo 10_flag_bots
│   ├── athena/ddl/             # fase 2: CREATE TABLE para o Athena
│   ├── athena/queries/         # fase 2: queries 01–06 no dialeto do Athena (Trino)
│   ├── athena/analise/         # as 16 queries de sql/analise/ no dialeto do Athena
│   ├── imdb/                   # fase 3: queries do IMDb (DuckDB)
│   ├── athena/imdb/            # fase 3: as mesmas queries no dialeto do Athena
│   └── cloud/                  # fase 2 e 3: queries extra do benchmark no dialeto DuckDB (06 e 07)
├── docs/                       # validação das queries do Luís e revisão da fase 2
├── data/<dataset>/             # não versionado; pode ser um symlink (ver abaixo)
│   ├── raw/                    # zip e ficheiros originais
│   ├── csv/                    # CSV normalizados
│   └── parquet/                # <tabela>.parquet e ratings_by_year/year=AAAA/
├── data/imdb/{raw,parquet}/   # não versionado: IMDb (fase 3), o mesmo para todos os datasets
├── data/cloud/<pasta>/         # não versionado: espelho do que vai para o S3
├── data/cloud/imdb/           # não versionado: IMDb para o S3 (fase 3)
├── reports/                    # versionado: cloud_manifest_<dataset>.md
└── results/                    # versionado (resultados leves: CSV, PNG, .md)
    ├── sizes.csv               # tamanhos CSV vs Parquet vs Parquet por ano, e tempo de cada conversão
    ├── pipeline_runs.csv       # tempo de cada passo
    ├── benchmarks.csv          # dataset, query, formato, mediana do tempo, n.º de linhas
    ├── cloud_benchmarks.csv    # fase 2: DuckDB vs Athena (tempo, MB lidos, n.º de linhas)
    ├── <dataset>/eda/          # figuras PNG, eda_indicadores.csv, eda_resumo_tabelas.csv, eda_relatorio.md
    ├── <dataset>/analises/     # um CSV por query, analises_relatorio.md e athena_emulado/
    ├── <dataset>/bots_coordenacao/   # resultados do 06_coordenacao.py
    └── <dataset>/imdb/         # fase 3: CSV, figuras e imdb_relatorio.md
```

O dataset 32M ocupa cerca de 1.2 GB depois de descarregado e normalizado (zip, CSV), mais o Parquet.

`data/<dataset>` pode ser um symlink para outra localização, por exemplo outra cópia do repositório
onde os dados já foram descarregados e convertidos. Assim não é preciso repetir o `ingest` e o
`parquet`. Como `data/` está no `.gitignore`, o symlink não é versionado:

```bash
mkdir -p data
ln -s "/caminho/para/outra/copia/BDF/data/32m" data/32m
```

## Análises e deteção de bots

> **Provisório:** as regras de deteção de bots e o teste de coordenação ainda estão a ser
> validados pelo Luís. Os números abaixo não são resultados finais.

### Passo `analises` (`scripts/05_analises.py`)

As queries vêm do notebook do Luís (células 108, 109 e 112). Foram extraídas para `sql/analise/` e,
quando foi preciso, corrigidas: fuso horário, faixas de atividade e o último ano incompleto. O
relatório completo está em [`docs/validacao_queries_colega.md`](docs/validacao_queries_colega.md).
Cada query tem uma versão Athena com o mesmo nome em `sql/athena/analise/`.

```bash
python scripts/05_analises.py --dataset small                  # o mesmo que o passo analises
python scripts/05_analises.py --dataset 1m --fonte csv         # ler os CSV em vez do Parquet
python scripts/05_analises.py --dataset small --emular-athena  # testar também as versões Athena
```

Com `--emular-athena`, as versões Athena correm no DuckDB, com macros que imitam as funções do
Trino, e o resultado de cada uma é comparado com o da versão DuckDB. Isto valida a lógica, mas
não a sintaxe do Trino: essa só se confirma no Athena.

**Deteção de bots** (`sql/analise/10_flag_bots.sql`). A regra original sinalizava sobretudo o
registo de utilizadores novos: 34% de suspeitos no small e 47% no 1M. Foi substituída por duas regras:

- **regra A:** ritmo sustentado depois das primeiras 24 h, acima do quantil p99,9;
- **regra B:** registo extremo, com pelo menos 100 eventos e um intervalo mediano de 2 s ou menos.

Com estas regras, os suspeitos são 0,33% no small e 0,10% no 1M. As submissões em lote (10 ou mais
avaliações no mesmo segundo) são contadas à parte e não contam como bots.

### Coordenação entre contas (`scripts/06_coordenacao.py`)

Corre à mão, fora do `run_pipeline.py`, porque é demorado no 32M. Procura rajadas: várias contas a
dar a mesma nota extrema ao mesmo filme na mesma hora, longe da média do filme. Compara o n.º real
de rajadas com uma linha de base em que os timestamps são baralhados dentro de cada filme.

```bash
python scripts/06_coordenacao.py --dataset 1m
python scripts/06_coordenacao.py --dataset 32m --repeticoes 200 --memoria 12GB
```

Escreve em `results/<dataset>/bots_coordenacao/` as rajadas, a linha de base, o teste (valor-p
empírico com Bonferroni), as 10 rajadas mais fortes conta a conta e o `coordenacao_relatorio.md`.
Conclusão atual, a validar:

- **1M:** não há mais rajadas do que na linha de base. As mais fortes são de contas novas, no pico
  de registos de 20 e 21/11/2000.
- **32M:** há mais rajadas do que na linha de base, mas o excesso está todo antes da escala de
  meias estrelas (fevereiro de 2003) e explica-se pela mudança de escala, não por coordenação.
  Com 200 permutações, nenhuma comparação pode passar a correção de Bonferroni.

## Fase 3: IMDb como dataset complementar

Mostra que o pipeline se adapta a um dataset complementar e responde a duas perguntas:

- **P1.** As notas do MovieLens e do IMDb concordam? Onde e quanto divergem?
- **P2.** Que diferenças há entre os tipos de utilizadores?

```bash
python run_pipeline.py --dataset small --steps imdb      # ou: python scripts/07_imdb.py --dataset small
python scripts/07_imdb.py --dataset small --emular-athena  # testar também as versões Athena
```

O passo `imdb` só corre quando é pedido, como o `cloud`. Na primeira vez descarrega cerca de
240 MB do IMDb. Precisa do `links.csv`, que tem o `imdbId` de cada filme, por isso **não corre com
o 1M**: só com o small e o 32M, depois dos passos `ingest` e `parquet`.

**Fontes e licença.** `title.ratings.tsv.gz` (nota média e n.º de votos de cada título) e
`title.basics.tsv.gz` (tipo, ano e géneros), de <https://datasets.imdbws.com/>. Os dados do IMDb
são disponibilizados apenas para **uso pessoal e não comercial**, nas condições descritas em
<https://developer.imdb.com/non-commercial-datasets/>. Não são versionados: ficam em
`data/imdb/raw/` (TSV.gz) e `data/imdb/parquet/` e são os mesmos para os três datasets do MovieLens.

| Etapa | O que faz |
|---|---|
| Download e Parquet | `\N` passa a nulo, tipos numéricos e géneros em lista. Só converte se o Parquet não existir ou for mais antigo. Tamanhos em `results/sizes.csv` (dataset `imdb`, com o TSV descomprimido, o TSV.gz e o Parquet). |
| Ligação | `tconst = 'tt' + imdbId`, com zeros à esquerda até 7 algarismos. O `lpad` só se aplica aos ids com menos de 7 algarismos, porque o `lpad` do DuckDB e do Trino corta os ids de 8 algarismos (7 067 filmes no 32M). |
| Tipo de título | Só entram nas análises os títulos do tipo `movie` (`imdb.tipos_titulo` no `config.yaml`). Séries, episódios, curtas, vídeos e filmes para TV contam na tabela da ligação (categoria 5), mas ficam de fora da P1 e da P2. |
| Escala | Nota do MovieLens × 2 (0,5–5 → 1–10, os extremos do IMDb). É linear: não muda a ordem nem as correlações. Gap = IMDb − MovieLens×2. |
| P1 | Gap médio com IC 95%, Pearson e Spearman; gap por género, por década e por popularidade (quintis de votos); os 10 filmes mais divergentes em cada sentido; sensibilidade aos limiares. |
| P2 | Segmentos de utilizadores do MovieLens (atividade, era de registo, bots) comparados com o IMDb sobre o mesmo conjunto de filmes. |
| Desempenho | Join MovieLens × IMDb em CSV/TSV.gz e em Parquet, mediana de 3 corridas, em `results/benchmarks.csv` (`imdb_join`). |

Os limiares e os tipos de título estão na secção `imdb` do `config.yaml`: pelo menos 50 avaliações no MovieLens e 1000
votos no IMDb. As queries estão em `sql/imdb/` (DuckDB) e `sql/athena/imdb/` (Athena). Os
resultados ficam em `results/<dataset>/imdb/`: um CSV por query, `sensibilidade.csv`,
`imdb_qualidade.csv`, quatro figuras e o `imdb_relatorio.md`.

**Na cloud.** Se o IMDb existir, o passo `cloud` prepara `data/cloud/imdb/`
(`scripts/prepare_cloud_imdb.py`), envia-o para `s3://<bucket-dados>/imdb/`, cria as tabelas
`imdb_title_ratings`, `imdb_title_basics` e as versões `_tsv` (DDL `08` a `11`) e junta ao
benchmark a query `07_imdb_join`, que compara os MB lidos em TSV.gz e em Parquet.

**Limitações.**

- O IMDb só publica agregados por filme, sem dados por utilizador. A P2 não compara utilizadores
  dos dois sites: compara a concordância de cada segmento de utilizadores do MovieLens com a nota
  agregada do IMDb.
- Os votos do IMDb são de outra população e de outra época (o ficheiro é atualizado todos os
  dias), e o IMDb não publica como calcula a nota.
- O segmento de bots é **provisório** (regras ainda a validar pelo Luís) e, no small, tem só
  2 utilizadores sinalizados, poucos demais para haver filmes comuns.

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
| [pandas](https://pandas.pydata.org/) | Tabelas pequenas já agregadas pelo DuckDB (verificações, relatórios e figuras) |
| [Matplotlib](https://matplotlib.org/) | Visualização |
| [Amazon S3](https://aws.amazon.com/s3/) | Armazenamento dos ficheiros na cloud (fase 2) |
| [AWS Glue Data Catalog](https://aws.amazon.com/glue/) | Catálogo das tabelas (fase 2) |
| [Amazon Athena](https://aws.amazon.com/athena/) | Motor SQL serverless (Trino) sobre o S3 (fase 2) |
| [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) | SDK da AWS em Python: upload, catálogo e queries (fase 2) |

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
