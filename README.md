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

Requer Python 3.10 ou superior. Na primeira vez, na pasta do repositório, cria-se um ambiente virtual
e instalam-se as dependências:

```bash
python3 -m venv .venv
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

Os passos são `ingest`, `parquet` e `benchmark`. Sem `--dataset` usa-se o valor de `config.yaml`.
Cada script em `scripts/` também corre isolado, por exemplo `python scripts/02_to_parquet.py --dataset 1m`.

| Passo | Script | O que faz |
|---|---|---|
| `ingest` | `scripts/01_ingest.py` | Descarrega o zip do GroupLens, só se ainda não existir, e normaliza para CSV com o esquema comum (`ratings`: userId, movieId, rating, timestamp; `movies`: movieId, title, genres). Converte os `.dat` do 1M (separador `::`, sem cabeçalho, latin-1). |
| `parquet` | `scripts/02_to_parquet.py` | `COPY` do DuckDB para Parquet sem partição e `ratings` particionado por ano (`PARTITION_BY year`, ano em UTC). Regista os tamanhos do CSV e do Parquet. |
| `benchmark` | `scripts/03_benchmark.py` | Corre cada query de `sql/` 3 vezes sobre os dois formatos de Parquet e regista a mediana do tempo e o n.º de linhas. |

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
│   └── 03_benchmark.py
├── sql/                        # 01–05: perguntas de análise e query temporal; 10: bots
├── data/<dataset>/             # não versionado
│   ├── raw/                    # zip e ficheiros originais
│   ├── csv/                    # CSV normalizados
│   └── parquet/                # <tabela>.parquet e ratings_by_year/year=AAAA/
└── results/                    # não versionado
    ├── sizes.csv               # tamanhos CSV vs Parquet vs Parquet por ano, e tempo de cada conversão
    ├── pipeline_runs.csv       # tempo de cada passo
    └── benchmarks.csv          # dataset, query, formato, mediana do tempo, n.º de linhas
```

O dataset 32M ocupa cerca de 1.2 GB depois de descarregado e normalizado (zip, CSV), mais o Parquet.

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
