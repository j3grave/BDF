[README.md](https://github.com/user-attachments/files/33067044/README.md)
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
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter lab                      # ou abrir o notebook no VS Code
```

## Estrutura do repositório

```
BDF/
├── Lab_Parquet_DuckDB_Polars_Arrow_EDA.ipynb   # notebook principal
├── requirements.txt                            # dependências Python
├── .gitignore                                  # exclui dados e ficheiros gerados
└── README.md
```

Ao executar o notebook são criadas as pastas `ml-latest-small/` (CSV), `parquet/` e `output/`
(base de dados `movielens.duckdb`), que não são versionadas.

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
