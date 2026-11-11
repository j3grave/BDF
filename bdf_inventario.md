# Inventário do projeto BDF (MovieLens) — estado em 2026-11-07

Repositório: `/Users/tiagovacasflgueira/Desktop/Nova IMS 2 Semestre/Enterprise Data Science Bootcamp/edsb-class06-class07/BDF`  
Branch atual: `integracao-queries-luis` (HEAD `cbd7cb1`), working tree limpa.  
Gerado só por leitura de ficheiros e de comandos git; nada foi corrido sobre os dados.

Índice: 1. Git · 2. Estrutura · 3. Scripts · 4. SQL · 5. Resultados quantitativos · 6. Bots e coordenação · 7. Cloud · 8. Pendentes

## 1. Estado do git

### Branches locais e remotos

```
  fase1-pipeline                         604c14a [origin/fase1-pipeline] Rótulos dos tempos do EDA e Python 3.13 como versão testada no README
  fase2-cloud-prep                       2b54c11 [origin/fase2-cloud-prep] README: secção Athena (catálogo, benchmark e credenciais do Learner Lab)
* integracao-queries-luis                cbd7cb1 [origin/integracao-queries-luis] Bloco 6 no 32M: 200 permutações, sensibilidade com notas <= 1,0, U >= 20, Bonferroni e rajadas por ano; relatório 13.8.2
  main                                   f1964cb [origin/main: ahead 4, behind 6] Add files via upload
  remotes/origin/HEAD                    -> origin/main
  remotes/origin/fase1-pipeline          604c14a Rótulos dos tempos do EDA e Python 3.13 como versão testada no README
  remotes/origin/fase2-cloud-prep        2b54c11 README: secção Athena (catálogo, benchmark e credenciais do Learner Lab)
  remotes/origin/integracao-queries-luis cbd7cb1 Bloco 6 no 32M: 200 permutações, sensibilidade com notas <= 1,0, U >= 20, Bonferroni e rajadas por ano; relatório 13.8.2
  remotes/origin/main                    e51d050 Notebook inicial com novas questões e análises
```

### Relação entre branches

- **`origin/main`** (`e51d050`, "Notebook inicial com novas questões e análises", do Luís) só tem o notebook e os ficheiros iniciais. **Nenhum dos três branches de trabalho está integrado no `main`** (nem no local, nem no remoto).
- **`main` local está divergente de `origin/main`**: 4 commits só locais (`f1964cb`, `5bb91ee`, `b699887`, `1ff6fbd`, uploads antigos do GitHub Desktop) e 6 commits só no remoto (`80dc4cb` … `e51d050`). Precisa de `git pull`/reset antes de qualquer merge.
- **`fase1-pipeline`** (`604c14a`): pipeline local (ingest, Parquet, benchmark, EDA). Está contido em `fase2-cloud-prep` e em `integracao-queries-luis`.
- **`fase2-cloud-prep`** (`2b54c11`): fase1 + preparação cloud (`prepare_cloud.py`, DDL Athena, `athena_setup.py`, `athena_benchmark.py`). Está contido em `integracao-queries-luis`.
- **`integracao-queries-luis`** (`cbd7cb1`, atual): fase2-cloud-prep + merge de `origin/main` (`efbf0b2`, traz o notebook do Luís `e51d050`) + blocos 1–6 (queries do Luís revistas, deteção de bots, coordenação). É o branch que contém tudo. Está sincronizado com `origin/integracao-queries-luis`.
- Por integrar no `main`: tudo o que está em `integracao-queries-luis` (30 commits à frente de `origin/main`, 0 atrás). Nenhum PR aberto foi verificado.

Contagens (`git rev-list --left-right --count A...B`):

```
origin/main...integracao-queries-luis : 0	30   (origin/main só | integracao só)
main...integracao-queries-luis        : 4	36
main...origin/main                    : 4	6
```

### `git --no-pager log --oneline --all --graph -40`

```
* cbd7cb1 Bloco 6 no 32M: 200 permutações, sensibilidade com notas <= 1,0, U >= 20, Bonferroni e rajadas por ano; relatório 13.8.2
* e71089f Bloco 6: teste de coordenação entre contas (scripts/06_coordenacao.py) no 1M e resultados no relatório
* 3fbf3b8 Relatório: secção 13 (Fase 2) em docs/validacao_queries_colega.md
* 552eb32 Bloco 3: 10 queries corrigidas (DuckDB e Athena) e resultados no small e no 1M
* 44ff879 Bloco 5: deteção de bots (sql/analise/10_flag_bots*.sql, a validar com o Luís) e verificações no 05_analises.py
* 51aa8a6 Bloco 2: queries ponderado, anual, valores_ano e qualidade (DuckDB e Athena) e scripts/05_analises.py
* 39ef705 Bloco 1: fuso UTC nas ligações DuckDB (03, 04), desempate por movieId em sql/04, passo analises no run_pipeline
*   efbf0b2 Merge remote-tracking branch 'origin/main' into integracao-queries-luis
|\  
| * e51d050 Notebook inicial com novas questões e análises
* | 2b54c11 README: secção Athena (catálogo, benchmark e credenciais do Learner Lab)
* | 01ea619 Fase 2, passo 6: benchmark DuckDB vs Athena (scripts/athena_benchmark.py)
* | e98334a Fase 2, passo 4: DDL do Athena e scripts/athena_setup.py
* | 94a0a42 Manifestos da preparação para a cloud (small, 1m e 32m)
* | ee26271 README: secção Preparação para a cloud e data/<dataset> como symlink
* | 79dd0b7 Fase 2: scripts/prepare_cloud.py prepara localmente os ficheiros para o S3
* | fc5452b gitignore: data/cloud/ e credenciais AWS (.aws/, *.env, chaves)
* | 604c14a Rótulos dos tempos do EDA e Python 3.13 como versão testada no README
* | cce9fb1 Verificação da versão mínima de Python (3.10) e instruções de instalação no README
* | e0e1286 Resultados do benchmark e do EDA para o dataset 32M
* | 5922055 Revisão didática: queries em sql/
* | 3aa2d7f Revisão didática: run_pipeline.py
* | 24844bc Revisão didática: scripts/04_eda.py
* | 79ac8b6 Revisão didática: scripts/03_benchmark.py
* | 31acbad Revisão didática: scripts/02_to_parquet.py
* | b743496 Revisão didática: scripts/01_ingest.py
* | bf4a958 Revisão didática: scripts/common.py
* | 9e648d2 Versionar resultados leves (figuras EDA, benchmarks, relatórios)
* | 6e4ed23 Passo eda: integrar scripts/04_eda.py no pipeline
* | 3e44916 02_to_parquet: registar o tempo de cada conversão em sizes.csv
* | 65eb2cc Reprodutibilidade: venv no README, versões testadas e DuckDB 2.0
* | c5dba07 Fase 1: pipeline local (ingestão, Parquet, queries SQL e benchmark)
|/  
* 34e4e75 Limpeza: .gitignore, remover .DS_Store, corrigir README
* f9e56f3 Add files via upload
* 0de8462 Add files via upload
* 5fe89f4 Create README.md
* 80dc4cb Add files via upload
*   de4ca01 On main: !!GitHub_Desktop<main>
|\  
| * 4d13870 index on main: f1964cb Add files via upload
|/  
* f1964cb Add files via upload
* 5bb91ee Add files via upload
```

## 2. Estrutura do repositório

Árvore sem `data/`, `.venv/`, `.git/` e `__pycache__/`. `data/small`, `data/1m` e `data/32m` são symlinks para `~/Desktop/Nova IMS 2 Semestre/BDF/data/<dataset>`; `data/cloud/` tem `ml-latest-small`, `ml-1m` e `ml-32m` (não versionados).

```
BDF/
├── .gitignore
├── Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1.ipynb
├── Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb
├── Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v2.ipynb
├── README.md
├── config.yaml
├── docs/
    ├── validacao_queries_colega.md
├── reports/
    ├── cloud_manifest_1m.md
    ├── cloud_manifest_32m.md
    ├── cloud_manifest_small.md
├── requirements.txt
├── results/
    ├── 1m/
        ├── analises/
            ├── 10_flag_bots.csv
            ├── 10_flag_bots_calibracao.csv
            ├── analises_relatorio.md
            ├── analises_resumo.csv
            ├── anual.csv
            ├── athena_emulado/
                ├── 10_flag_bots.csv
                ├── 10_flag_bots_calibracao.csv
                ├── anual.csv
                ├── comparacao.csv
                ├── distribuicao.csv
                ├── eventos.csv
                ├── evolucao_filmes.csv
                ├── filmes_ano.csv
                ├── filtros_eventos.csv
                ├── grupos_atividade.csv
                ├── integridade.csv
                ├── mensal.csv
                ├── perfis_ativos.csv
                ├── perfis_cumulativos.csv
                ├── ponderado.csv
                ├── qualidade.csv
                ├── valores_ano.csv
            ├── distribuicao.csv
            ├── eventos.csv
            ├── evolucao_filmes.csv
            ├── filmes_ano.csv
            ├── filtros_eventos.csv
            ├── grupos_atividade.csv
            ├── integridade.csv
            ├── mensal.csv
            ├── perfis_ativos.csv
            ├── perfis_cumulativos.csv
            ├── ponderado.csv
            ├── qualidade.csv
            ├── valores_ano.csv
        ├── bots_coordenacao/
            ├── coordenacao_relatorio.md
            ├── linha_base.csv
            ├── rajadas.csv
            ├── rajadas_por_ano.csv
            ├── teste.csv
            ├── top10_contas.csv
            ├── top10_rajadas.csv
            ├── verificacao_permutacao.csv
        ├── eda/
            ├── 01_distribuicao_ratings.png
            ├── 02_atividade_utilizadores.png
            ├── 03_popularidade_filmes.png
            ├── 04_cauda_longa_filmes.png
            ├── 05_evolucao_temporal.png
            ├── 06_generos.png
            ├── 07_ano_lancamento.png
            ├── 08_heatmap_genero_ano.png
            ├── 10_painel_resumo.png
            ├── eda_indicadores.csv
            ├── eda_relatorio.md
            ├── eda_resumo_tabelas.csv
    ├── 32m/
        ├── bots_coordenacao/
            ├── coordenacao_relatorio.md
            ├── linha_base.csv
            ├── rajadas.csv
            ├── rajadas_por_ano.csv
            ├── teste.csv
            ├── top10_contas.csv
            ├── top10_rajadas.csv
            ├── verificacao_permutacao.csv
        ├── eda/
            ├── 01_distribuicao_ratings.png
            ├── 02_atividade_utilizadores.png
            ├── 03_popularidade_filmes.png
            ├── 04_cauda_longa_filmes.png
            ├── 05_evolucao_temporal.png
            ├── 06_generos.png
            ├── 07_ano_lancamento.png
            ├── 08_heatmap_genero_ano.png
            ├── 09_top_tags.png
            ├── 10_painel_resumo.png
            ├── eda_indicadores.csv
            ├── eda_relatorio.md
            ├── eda_resumo_tabelas.csv
    ├── benchmarks.csv
    ├── cloud_benchmarks.csv
    ├── pipeline_runs.csv
    ├── sizes.csv
    ├── small/
        ├── analises/
            ├── 10_flag_bots.csv
            ├── 10_flag_bots_calibracao.csv
            ├── 10_flag_bots_referencia.csv
            ├── analises_relatorio.md
            ├── analises_resumo.csv
            ├── anual.csv
            ├── athena_emulado/
                ├── 10_flag_bots.csv
                ├── 10_flag_bots_calibracao.csv
                ├── anual.csv
                ├── comparacao.csv
                ├── distribuicao.csv
                ├── eventos.csv
                ├── evolucao_filmes.csv
                ├── filmes_ano.csv
                ├── filtros_eventos.csv
                ├── grupos_atividade.csv
                ├── integridade.csv
                ├── mensal.csv
                ├── perfis_ativos.csv
                ├── perfis_cumulativos.csv
                ├── ponderado.csv
                ├── qualidade.csv
                ├── valores_ano.csv
            ├── distribuicao.csv
            ├── eventos.csv
            ├── evolucao_filmes.csv
            ├── filmes_ano.csv
            ├── filtros_eventos.csv
            ├── grupos_atividade.csv
            ├── integridade.csv
            ├── mensal.csv
            ├── perfis_ativos.csv
            ├── perfis_cumulativos.csv
            ├── ponderado.csv
            ├── qualidade.csv
            ├── valores_ano.csv
        ├── eda/
            ├── 01_distribuicao_ratings.png
            ├── 02_atividade_utilizadores.png
            ├── 03_popularidade_filmes.png
            ├── 04_cauda_longa_filmes.png
            ├── 05_evolucao_temporal.png
            ├── 06_generos.png
            ├── 07_ano_lancamento.png
            ├── 08_heatmap_genero_ano.png
            ├── 09_top_tags.png
            ├── 10_painel_resumo.png
            ├── eda_indicadores.csv
            ├── eda_relatorio.md
            ├── eda_resumo_tabelas.csv
├── run_pipeline.py
├── scripts/
    ├── 01_ingest.py
    ├── 02_to_parquet.py
    ├── 03_benchmark.py
    ├── 04_eda.py
    ├── 05_analises.py
    ├── 06_coordenacao.py
    ├── athena_benchmark.py
    ├── athena_common.py
    ├── athena_setup.py
    ├── common.py
    ├── prepare_cloud.py
├── sql/
    ├── 01_generos.sql
    ├── 02_filmes_por_genero.sql
    ├── 03_avaliacoes_por_utilizador.sql
    ├── 04_top_filmes.sql
    ├── 05_ratings_por_ano.sql
    ├── 10_flag_bots.sql
    ├── analise/
        ├── 10_flag_bots.sql
        ├── 10_flag_bots_calibracao.sql
        ├── anual.sql
        ├── distribuicao.sql
        ├── eventos.sql
        ├── evolucao_filmes.sql
        ├── filmes_ano.sql
        ├── filtros_eventos.sql
        ├── grupos_atividade.sql
        ├── integridade.sql
        ├── mensal.sql
        ├── perfis_ativos.sql
        ├── perfis_cumulativos.sql
        ├── ponderado.sql
        ├── qualidade.sql
        ├── valores_ano.sql
    ├── athena/
        ├── analise/
            ├── 10_flag_bots.sql
            ├── 10_flag_bots_calibracao.sql
            ├── anual.sql
            ├── distribuicao.sql
            ├── eventos.sql
            ├── evolucao_filmes.sql
            ├── filmes_ano.sql
            ├── filtros_eventos.sql
            ├── grupos_atividade.sql
            ├── integridade.sql
            ├── mensal.sql
            ├── perfis_ativos.sql
            ├── perfis_cumulativos.sql
            ├── ponderado.sql
            ├── qualidade.sql
            ├── valores_ano.sql
        ├── ddl/
            ├── 00_database.sql
            ├── 01_ratings.sql
            ├── 02_ratings_part.sql
            ├── 03_ratings_part_particoes.sql
            ├── 04_ratings_csv.sql
            ├── 05_movies.sql
            ├── 06_tags.sql
            ├── 07_links.sql
        ├── queries/
            ├── 01_generos.sql
            ├── 02_filmes_por_genero.sql
            ├── 03_avaliacoes_por_utilizador.sql
            ├── 04_top_filmes.sql
            ├── 05_ratings_por_ano.sql
            ├── 06_ratings_desde_2015.sql
    ├── cloud/
        ├── 06_ratings_desde_2015.sql
```

### `run_pipeline.py`: ordem e parâmetros

Ordem por omissão (dicionário `STEPS`): cada passo corre num processo Python separado com `--dataset <ds>` e o tempo total vai para `results/pipeline_runs.csv`; `check=True` pára o pipeline se um passo falhar.

| # | Passo (`--steps`) | Script |
|---|---|---|
| 1 | `ingest` | `scripts/01_ingest.py` |
| 2 | `parquet` | `scripts/02_to_parquet.py` |
| 3 | `benchmark` | `scripts/03_benchmark.py` |
| 4 | `eda` | `scripts/04_eda.py` |
| 5 | `analises` | `scripts/05_analises.py` |

- **Não** fazem parte do pipeline: `06_coordenacao.py`, `prepare_cloud.py`, `athena_setup.py`, `athena_benchmark.py` (correm à mão).
- `--dataset {small,1m,32m}`: sobrepõe o `dataset` do `config.yaml` (por omissão `small`).
- `--steps <passo ...>`: subconjunto dos passos (por omissão todos, pela ordem acima).
- `--fonte` **não** é opção do `run_pipeline.py` (não é passada aos passos). Existe só nos scripts:
  - `04_eda.py --fonte {auto,parquet,csv}` (omissão `auto`: Parquet se existir, senão CSV);
  - `05_analises.py --fonte {parquet,csv}` (omissão `parquet`).
  No pipeline correm portanto com os valores por omissão.
- Nota: o README ainda diz "os passos são ingest, parquet, benchmark e eda" (não menciona `analises`).
- Python mínimo 3.10 (verificado no arranque); testado em 3.13.

`config.yaml` completo:

```yaml
# Configuração do pipeline local (Fase 1).
# O dataset pode ser alterado na linha de comandos: python run_pipeline.py --dataset 1m

dataset: small          # small | 1m | 32m
data_dir: data          # downloads, CSV normalizados e Parquet: data/<dataset>/...
results_dir: results    # tamanhos, tempos e benchmarks

# Fase 2 (scripts/athena_setup.py e scripts/athena_benchmark.py). Os nomes dos buckets não são
# segredos e podem ficar aqui; as credenciais NUNCA (vão para ~/.aws/credentials).
# O AWS Academy Learner Lab só permite us-east-1 e us-west-2.
aws:
  region: us-east-1
  bucket_dados: null        # bucket com data/cloud/<pasta>/, ex.: bdf26-g1-movielens-dados
  bucket_resultados: null   # resultados das queries do Athena, ex.: bdf26-g1-athena-resultados
  workgroup: primary
```

## 3. Scripts (`scripts/`)

### `scripts/common.py` (152 linhas)

- **O que faz:** Módulo partilhado (não se corre sozinho). Define os datasets (`DATASETS`: small, 1m, 32m, com URL e pasta do GroupLens), os esquemas das tabelas (`SCHEMAS`), lê o `config.yaml` (`load_config`, com `--dataset` a sobrepor), constrói os caminhos `data/<ds>/{raw,csv,parquet}` e `results/`, e escreve linhas em CSV de resultados (`append_row`, que acrescenta e ajusta o cabeçalho).
- **Inputs:** `config.yaml`
- **Outputs:** nenhum (importado pelos outros)
- **Comando:** — (importado)

### `scripts/01_ingest.py` (124 linhas)

- **O que faz:** Passo 1. Descarrega o zip do GroupLens só se não existir e normaliza todas as tabelas para CSV UTF-8 com cabeçalho e o esquema comum. small e 32M são só extraídos; o 1M (`.dat`, separador `::`, sem cabeçalho, latin-1) é convertido com o DuckDB. No fim imprime o n.º de linhas de cada CSV.
- **Inputs:** URL do GroupLens; `data/<ds>/raw/<pasta>.zip`
- **Outputs:** `data/<ds>/raw/` (zip + originais); `data/<ds>/csv/ratings.csv`, `movies.csv`, e `tags.csv`, `links.csv` (small e 32M)
- **Comando:** `python scripts/01_ingest.py --dataset small`

### `scripts/02_to_parquet.py` (112 linhas)

- **O que faz:** Passo 2. Converte cada CSV em Parquet com `COPY` do DuckDB (streaming, snappy) e cria uma segunda versão de `ratings` particionada por ano (`PARTITION_BY year`, ano = `year(epoch_ms(timestamp*1000))`, UTC). Apaga a versão particionada anterior. Regista tamanhos e tempos de conversão.
- **Inputs:** `data/<ds>/csv/*.csv`
- **Outputs:** `data/<ds>/parquet/<tabela>.parquet`; `data/<ds>/parquet/ratings_by_year/year=AAAA/`; linhas em `results/sizes.csv`
- **Comando:** `python scripts/02_to_parquet.py --dataset small`

### `scripts/03_benchmark.py` (106 linhas)

- **O que faz:** Passo 3. Corre cada `sql/*.sql` (marcadores `${ratings}`, `${movies}`) 3 vezes sobre o Parquet sem partição e sobre o particionado por ano, e guarda a mediana do tempo e o n.º de linhas. Ignora ficheiros só com comentários (`sql/10_flag_bots.sql`). Não guarda o resultado das queries, só tempo e linhas.
- **Inputs:** `sql/*.sql`; `data/<ds>/parquet/`
- **Outputs:** linhas em `results/benchmarks.csv`
- **Comando:** `python scripts/03_benchmark.py --dataset small`

### `scripts/04_eda.py` (667 linhas)

- **O que faz:** Passo 4. Análise exploratória com todas as agregações no DuckDB (corre no 32M sem carregar os dados em memória): indicadores-chave (volume, esparsidade, distribuição, Gini, concentração, anos, géneros, tags), resumo de qualidade por tabela, 10 figuras com a paleta NOVA IMS e relatório Markdown. A figura 09 (tags) só existe se houver tags (não no 1M).
- **Inputs:** `data/<ds>/parquet/<tabela>.parquet` (ou `data/<ds>/csv/` com `--fonte csv` ou se não houver Parquet)
- **Outputs:** `results/<ds>/eda/`: `01_…png`–`10_…png`, `eda_indicadores.csv`, `eda_resumo_tabelas.csv`, `eda_relatorio.md`
- **Comando:** `python scripts/04_eda.py --dataset small` · `python scripts/04_eda.py --dataset 32m --fonte parquet`

### `scripts/05_analises.py` (430 linhas)

- **O que faz:** Passo 5. Corre as 16 queries de `sql/analise/` (vindas do notebook do Luís, revistas) e grava cada resultado em CSV com `COPY`. Corre primeiro `10_flag_bots.sql` e guarda-a como tabela temporária `${flag_bots}`. Verificações que fazem falhar: 0 nulos/fora da escala, integridade, contagens e média iguais às do `eda_indicadores.csv`, soma de `anual` = total, e os 5 utilizadores de referência dos bots (small). Com `--emular-athena` corre também as versões `sql/athena/analise/` emuladas no DuckDB e compara.
- **Inputs:** `sql/analise/*.sql`; `data/<ds>/parquet/` (ou `csv/`); `results/<ds>/eda/eda_indicadores.csv`; `sql/athena/analise/*.sql` (com `--emular-athena`)
- **Outputs:** `results/<ds>/analises/`: `<query>.csv`, `analises_resumo.csv`, `analises_relatorio.md`, `10_flag_bots_referencia.csv` (só small); `athena_emulado/<query>.csv` e `athena_emulado/comparacao.csv`
- **Comando:** `python scripts/05_analises.py --dataset small --emular-athena` · opções `--fonte csv`, `--queries anual qualidade`

### `scripts/06_coordenacao.py` (453 linhas)

- **O que faz:** Bloco 6 (fora do pipeline, a validar com o Luís). Procura "rajadas": (filme, nota extrema, hora UTC) com ≥ U utilizadores distintos a dar a mesma nota extrema a ≥ D da média do filme (U ∈ {3,5,10,20}, D ∈ {1,5; 2}). Compara com uma linha de base de R permutações dos timestamps dentro de cada filme (valor-p empírico, z, Bonferroni), verifica a permutação, caracteriza as 10 rajadas mais fortes conta a conta (antiguidade, registo, Jaccard, estreia) e a distribuição por ano.
- **Inputs:** `data/<ds>/parquet/ratings.parquet`, `movies.parquet`; `results/<ds>/analises/10_flag_bots.csv` (opcional)
- **Outputs:** `results/<ds>/bots_coordenacao/`: `rajadas.csv`, `linha_base.csv`, `teste.csv`, `rajadas_por_ano.csv`, `verificacao_permutacao.csv`, `top10_rajadas.csv`, `top10_contas.csv`, `coordenacao_relatorio.md` (temporário: `data/<ds>/duckdb_tmp/`, apagado no fim)
- **Comando:** `python scripts/06_coordenacao.py --dataset 1m` · `python scripts/06_coordenacao.py --dataset 32m --repeticoes 200 --memoria 12GB` (omissão: 20 repetições, 12GB)

### `scripts/prepare_cloud.py` (390 linhas)

- **O que faz:** Fase 2, sem chamadas à AWS. Cria em `data/cloud/<pasta>/` o espelho exato do que vai para o S3: uma pasta por tabela, Parquet zstd sem casts, `ratings` sem partição e particionado por ano (`year` só no nome da pasta) e cópia byte a byte do `ratings.csv`. Idempotente (apaga e recria). Verifica contagens, soma das partições, contagens por ano vs `ratings_by_year`, tipos, compressão e estrutura; só então escreve o manifesto.
- **Inputs:** `data/<ds>/parquet/*.parquet`, `data/<ds>/parquet/ratings_by_year/`, `data/<ds>/csv/ratings.csv`
- **Outputs:** `data/cloud/<pasta>/{ratings,ratings_part/year=AAAA,ratings_csv,movies,tags,links}/`; `reports/cloud_manifest_<ds>.md`
- **Comando:** `python scripts/prepare_cloud.py --dataset small` · `python scripts/prepare_cloud.py` (omissão: 32m)

### `scripts/athena_common.py` (176 linhas)

- **O que faz:** Módulo partilhado da fase 2 (não se corre sozinho). Opções AWS da linha de comandos (`--region`, `--bucket-dados`, `--bucket-resultados`, `--workgroup`, `--dry-run`) com valores do `config.yaml`, leitura dos `.sql` de `sql/athena/`, e uma classe mínima que submete uma query ao Athena via boto3, espera e devolve tempo total, tempo no motor e `DataScannedInBytes`. Termina com erro se faltar bucket (exceto em `--dry-run`).
- **Inputs:** `config.yaml` (secção `aws`); `~/.aws/credentials`
- **Outputs:** nenhum
- **Comando:** — (importado)

### `scripts/athena_setup.py` (198 linhas)

- **O que faz:** Fase 2. Corre o DDL de `sql/athena/ddl/` para criar no Glue Data Catalog a base `movielens_<ds>` e as tabelas (tags e links saltadas no 1M), faz `MSCK REPAIR TABLE` em `ratings_part`. Antes, sem AWS, compara colunas/tipos do DDL com os ficheiros de `data/cloud/`; depois confirma no Athena as contagens totais e por ano. `--recriar` apaga e recria (EXTERNAL: não apaga dados).
- **Inputs:** `sql/athena/ddl/*.sql`; `data/cloud/<pasta>/`; `config.yaml`
- **Outputs:** base e tabelas no Glue Data Catalog; localmente só o resumo no ecrã
- **Comando:** `python scripts/athena_setup.py --dry-run` · `python scripts/athena_setup.py --bucket-dados X --bucket-resultados Y` (omissão: 32m)

### `scripts/athena_benchmark.py` (214 linhas)

- **O que faz:** Fase 2. Corre as mesmas perguntas no DuckDB (sobre `data/cloud/`) e no Athena (sobre a cópia no S3): queries com ratings em CSV, Parquet e Parquet particionado; as de movies só em Parquet. 3 corridas, mediana. No Athena regista também tempo no motor e MB lidos. `--engines duckdb` corre só a parte local; `--dry-run` mostra o SQL do Athena.
- **Inputs:** `sql/athena/queries/*.sql`; `sql/0X_*.sql`; `sql/cloud/*.sql`; `data/cloud/<pasta>/`; tabelas no Athena
- **Outputs:** linhas em `results/cloud_benchmarks.csv`
- **Comando:** `python scripts/athena_benchmark.py --engines duckdb` · `--dry-run` · `--bucket-dados X --bucket-resultados Y` (omissão: 32m, 3 corridas)

Outros ficheiros executáveis: `run_pipeline.py` (secção 2) e três notebooks na raiz (`Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1.ipynb`, `_v1_3.ipynb`, `_v2.ipynb`), não alterados; as queries de `sql/analise/` vêm das células 108, 109 e 112 do `_v1_3`.

## 4. Ficheiros SQL

Convenções: `${ratings}`, `${movies}`, `${flag_bots}`, `${database}`, `${bucket}`, `${pasta}` são substituídos pelos scripts. Onde está "output", são as 5 primeiras linhas (mais o cabeçalho) do CSV de resultados e o n.º de linhas de dados.

- `sql/0X_*.sql`: o `03_benchmark.py` não grava o resultado das queries; só existe o n.º de linhas em `results/benchmarks.csv`.
- `sql/analise/*.sql`: CSV em `results/{small,1m}/analises/<nome>.csv` (não corridas no 32M).
- `sql/athena/analise/*.sql`: **nunca correram no Athena**; o output indicado é a emulação no DuckDB (`results/<ds>/analises/athena_emulado/<nome>.csv`).
- `sql/athena/queries/*.sql` e `sql/athena/ddl/*.sql`: nunca correram no Athena; para as queries, o n.º de linhas vem da parte DuckDB de `results/cloud_benchmarks.csv`.

### 4.1 `sql/` (benchmark da fase 1)

### `sql/01_generos.sql`

- **Dialeto:** DuckDB
- **Pergunta:** quais são os géneros de filmes no dataset?

```sql
-- 01_generos.sql
-- Pergunta 7.1: quais são os géneros de filmes no dataset?
--
-- Como funciona: a coluna genres guarda vários géneros num só texto ("Action|Comedy").
-- string_split parte o texto numa lista e unnest transforma cada elemento da lista
-- numa linha; DISTINCT fica com cada género uma só vez.
--
-- Ligação às aulas:
-- - Formato colunar: o Parquet guarda cada coluna em separado. Esta query só usa
--   genres, por isso o DuckDB lê só essa coluna do ficheiro e ignora movieId e title
--   (projection pushdown).
-- - Partições: não se aplicam; só usa movies, que não está particionado.
--
-- Parâmetros: ${movies} (substituído pela leitura do Parquet em 03_benchmark.py)
SELECT DISTINCT genre
FROM (SELECT unnest(string_split(genres, '|')) AS genre FROM ${movies})
ORDER BY genre;
```

**Output:** sem CSV de resultados (o benchmark só guarda tempo e linhas). N.º de linhas em `results/benchmarks.csv`: small: 20, 1m: 18, 32m: 20.

### `sql/02_filmes_por_genero.sql`

- **Dialeto:** DuckDB
- **Pergunta:** qual é o número de filmes por género?

```sql
-- 02_filmes_por_genero.sql
-- Pergunta 7.2: qual é o número de filmes por género?
--
-- Como funciona: a CTE movie_genre tem uma linha por par (filme, género). Contamos as
-- linhas de cada género e dividimos pelo total de filmes para obter a percentagem.
-- Um filme pode ter vários géneros, por isso a soma de num_movies é maior do que o n.º de filmes.
--
-- Ligação às aulas:
-- - Formato colunar: só são lidas as colunas movieId e genres (projection pushdown).
-- - Metadados do Parquet: o rodapé de cada ficheiro guarda o n.º de linhas, por isso
--   o SELECT COUNT(*) do total pode ser respondido sem ler os dados.
-- - Partições: não se aplicam (só usa movies).
--
-- Parâmetros: ${movies}
WITH movie_genre AS (
    SELECT movieId, unnest(string_split(genres, '|')) AS genre
    FROM ${movies}
)
SELECT genre,
       COUNT(*)                                                         AS num_movies,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ${movies}), 1)    AS pct_movies
FROM movie_genre
GROUP BY genre
ORDER BY num_movies DESC, genre;
```

**Output:** sem CSV de resultados (o benchmark só guarda tempo e linhas). N.º de linhas em `results/benchmarks.csv`: small: 20, 1m: 18, 32m: 20.

### `sql/03_avaliacoes_por_utilizador.sql`

- **Dialeto:** DuckDB
- **Pergunta:** qual é a distribuição das avaliações por utilizador?

```sql
-- 03_avaliacoes_por_utilizador.sql
-- Pergunta 7.3: qual é a distribuição das avaliações por utilizador?
--
-- Como funciona: agrupa os ratings por utilizador e calcula, para cada um, o n.º de
-- avaliações, a média, o desvio-padrão (amostral), o mínimo, a mediana e o máximo.
--
-- Ligação às aulas:
-- - Formato colunar: das 4 colunas de ratings só são lidas userId e rating
--   (projection pushdown); movieId e timestamp nem saem do disco.
-- - Partições: não ajudam. A query usa todos os anos, por isso o DuckDB tem de abrir
--   todas as pastas year=AAAA; com muitos ficheiros pequenos pode até ser mais lenta
--   do que com um ficheiro único. Compare as duas linhas em results/benchmarks.csv.
--
-- Parâmetros: ${ratings}
SELECT userId,
       COUNT(*)                         AS num_ratings,
       ROUND(AVG(rating), 3)            AS mean,
       ROUND(STDDEV_SAMP(rating), 3)    AS std,
       MIN(rating)                      AS min,
       MEDIAN(rating)                   AS median,
       MAX(rating)                      AS max
FROM ${ratings}
GROUP BY userId
ORDER BY userId;
```

**Output:** sem CSV de resultados (o benchmark só guarda tempo e linhas). N.º de linhas em `results/benchmarks.csv`: small: 610, 1m: 6040, 32m: 200948.

### `sql/04_top_filmes.sql`

- **Dialeto:** DuckDB
- **Pergunta:** quais são os filmes com a média de avaliação mais alta?

```sql
-- 04_top_filmes.sql
-- Pergunta 7.4: quais são os filmes com a média de avaliação mais alta?
--
-- Como funciona: junta ratings e movies pelo movieId, calcula a média de cada filme e
-- fica com os 10 melhores. Exige pelo menos 100 avaliações (HAVING), senão o topo
-- ficava cheio de filmes com uma única avaliação de 5 estrelas. Ordena pela média
-- exata e não pela arredondada, para o desempate ser correto. Em caso de empate na
-- média, o movieId decide a ordem, para o resultado ser sempre o mesmo (determinístico).
--
-- Ligação às aulas:
-- - Formato colunar: de ratings só se leem movieId e rating; de movies só movieId e
--   title (projection pushdown). genres e timestamp não são lidos.
-- - HAVING filtra depois de agregar (sobre COUNT(*)); um WHERE filtraria antes.
-- - Partições: não ajudam, porque a query usa todos os anos.
--
-- Parâmetros: ${ratings}, ${movies}
SELECT m.title, ROUND(AVG(r.rating), 2) AS avg_rating, COUNT(*) AS num_ratings
FROM ${ratings} r
JOIN ${movies} m USING (movieId)
GROUP BY m.movieId, m.title
HAVING COUNT(*) >= 100
ORDER BY AVG(r.rating) DESC, m.movieId
LIMIT 10;
```

**Output:** sem CSV de resultados (o benchmark só guarda tempo e linhas). N.º de linhas em `results/benchmarks.csv`: small: 10, 1m: 10, 32m: 10.

### `sql/05_ratings_por_ano.sql`

- **Dialeto:** DuckDB
- **Pergunta:** Query temporal: número de ratings e média por ano.

```sql
-- 05_ratings_por_ano.sql
-- Query temporal: número de ratings e média por ano.
--
-- Como funciona: agrupa os ratings pela coluna year e calcula o n.º e a média em cada ano.
--
-- Ligação às aulas (é a query em que as partições fazem diferença):
-- - Parquet particionado: a coluna year vem do nome das pastas year=AAAA, por isso
--   o DuckDB não precisa de ler nem converter o timestamp; dentro dos ficheiros só lê
--   rating.
-- - Parquet sem partição: year tem de ser calculado linha a linha a partir do
--   timestamp (ver 03_benchmark.py), o que obriga a ler também essa coluna.
-- - Partition pruning: com um filtro como WHERE year >= 2015, o DuckDB nem abriria
--   as pastas dos anos anteriores. É o filter pushdown aplicado às partições.
--
-- Parâmetros: ${ratings}
SELECT year,
       COUNT(*)                 AS num_ratings,
       ROUND(AVG(rating), 3)    AS avg_rating
FROM ${ratings}
GROUP BY year
ORDER BY year;
```

**Output:** sem CSV de resultados (o benchmark só guarda tempo e linhas). N.º de linhas em `results/benchmarks.csv`: small: 23, 1m: 4, 32m: 29.

### `sql/10_flag_bots.sql`

- **Dialeto:** DuckDB
- **Pergunta:** nenhuma ainda (esqueleto só com comentários; as regras estão em sql/analise/10_flag_bots.sql)

```sql
-- 10_flag_bots.sql — ESQUELETO, ainda sem regras.
-- As regras para identificar utilizadores suspeitos (bots) vão ser definidas pelo Luís.
-- Enquanto este ficheiro só tiver comentários, o 03_benchmark.py ignora-o.
--
-- Parâmetros disponíveis: ${ratings}, ${movies}
-- Colunas de ${ratings}: userId, movieId, rating, timestamp, year
--
-- Ligação às aulas (a ter em conta ao escrever as regras):
-- - Formato colunar: usar só as colunas necessárias (evitar SELECT *) para o DuckDB
--   ler menos dados do Parquet.
-- - Partições: se uma regra olhar só para alguns anos, filtrar por year no WHERE
--   permite saltar as pastas dos restantes anos (partition pruning).
--
-- Estrutura sugerida:
--
-- WITH user_activity AS (
--     SELECT userId,
--            COUNT(*)                          AS num_ratings,
--            -- ... métricas por utilizador (ex.: ratings por dia, variância, intervalo entre ratings)
--     FROM ${ratings}
--     GROUP BY userId
-- )
-- SELECT userId,
--        -- ... uma coluna booleana por regra (rule_1, rule_2, ...)
--        -- ... is_bot = combinação das regras
-- FROM user_activity
-- WHERE ...;
```

**Output:** nenhum. Esqueleto só com comentários, ignorado pelo `03_benchmark.py`; as regras reais estão em `sql/analise/10_flag_bots.sql`.

### 4.2 `sql/analise/` (DuckDB, passo `analises`)

### `sql/analise/10_flag_bots.sql`

- **Dialeto:** DuckDB
- **Pergunta:** que utilizadores têm comportamento suspeito (regra A: ritmo sustentado fora do registo; regra B: registo extremo) ou de submissão em lote? Uma linha por utilizador, com classificação e justificação (nunca "bot confirmado").

```sql
-- 10_flag_bots.sql (DuckDB) - utilizadores com comportamento SUSPEITO (nunca "bot confirmado")
--
-- *** A VALIDAR COM O LUÍS ***
-- Substitui a regra de utilizadores_sinalizados do notebook do Luís (célula 112, id
-- "novo-advanced", SQL_AVANCADO["utilizadores_sinalizados"], commit e51d050), que
-- sinalizava 34% dos utilizadores do small, sobretudo pelo pico normal do registo.
-- Está em sql/analise/ (e não em sql/, onde fica o esqueleto 10_flag_bots.sql do benchmark).
--
-- Princípio: sinalizar o que não é fisicamente plausível para um humano, e não "muita
-- atividade". O timestamp regista o momento em que a avaliação foi GRAVADA, não o clique:
-- nos anos 90 o formulário submetia uma página inteira de avaliações com o mesmo segundo.
--
-- Passos:
-- 1. Eventos de submissão: as avaliações com o mesmo (userId, timestamp) formam um evento;
--    k = n.º de avaliações do evento. Todos os ritmos são medidos em eventos, não em avaliações.
-- 2. Submissão em lote (NÃO é bot): utilizador com pelo menos um evento com >= 10 avaliações
--    no mesmo segundo (o limite 10 é o do sinal "mesmo_segundo" do Luís). Casos de referência
--    no small: 191, 429, 99, 163 (anos 90) e 534 (2016).
-- 3. Regra A - ritmo sustentado não humano, fora do registo:
--    - ignora as primeiras 24 h de cada utilizador (registo);
--    - eventos_10min = n.º de eventos na janela [t, t + 599 s] (janela deslizante de 10 min);
--    - regra_a: max_eventos_10min_apos >= limiar_regra_a, em que o limiar é o QUANTIL 99,9%
--      dessa métrica entre os utilizadores com atividade depois do registo (calculado na
--      própria query, por isso adapta-se a cada dataset; não é um valor fixo por minuto).
--      O 10_flag_bots_calibracao.sql mostra a distribuição e os sinalizados no p99, p99,5 e
--      p99,9. O quantil está escrito em limiar_regra_a (abaixo) e é para calibrar no 32M.
--    Referência: o 610 do small (566 avaliações numa hora, ~4 s cada, quase 6 meses depois
--    do registo) tem de ser sinalizado.
-- 4. Regra B - registo extremo (só dentro das primeiras 24 h): volume muito alto E ritmo
--    sustentado: >= 100 eventos ("centenas") com intervalo mediano <= 2 s. Os dois valores vêm
--    da definição pedida, não de calibração. Referência: o 89 (518 avaliações em 23 min, ~2 s
--    cada) é candidato; o 257 (20 em 11 min) e o 7 (uso normal) não podem ser sinalizados.
-- 5. Sinais complementares (não classificam sozinhos; contam-se em sinais_complementares):
--    desvio-padrão das notas no 1% mais baixo, % da nota mais frequente no 1% mais alto e %
--    de eventos em lote (k >= 2) no 1% mais alto, entre todos os utilizadores do dataset.
--
-- Saída: uma linha por utilizador (610 no small, 200 948 no 32M). Localmente vai para CSV;
-- no Athena é um CTAS em Parquet (ver a versão Athena), nunca um resultado para o cliente.
-- O 05_analises.py guarda-a na tabela temporária ${flag_bots}, usada por
-- 10_flag_bots_calibracao.sql e eventos.sql.
--
-- Parâmetros: ${ratings}
WITH lim AS (SELECT 86400 AS registo_s,           -- primeiras 24 h de cada utilizador
                    100   AS regra_b_min_eventos,  -- "centenas de eventos"
                    2     AS regra_b_max_mediana_s,
                    10    AS lote_min_avaliacoes), -- limite do sinal mesmo_segundo do Luís
     -- 1. Eventos de submissão
     ev AS (SELECT userId, timestamp AS ts, COUNT(*) AS k
            FROM ${ratings}
            GROUP BY userId, timestamp),
     fase AS (SELECT ev.*,
                     ts - MIN(ts) OVER (PARTITION BY userId) < l.registo_s AS no_registo
              FROM ev CROSS JOIN lim l),
     -- Intervalo e janela de 10 min calculados dentro de cada fase (registo / depois), para
     -- uma janela não misturar eventos do registo com eventos posteriores.
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
     -- Notas: desvio-padrão e peso da nota mais frequente (% de notas iguais)
     notas AS (SELECT userId, COUNT(*) AS avaliacoes, STDDEV_SAMP(rating) AS desvio_notas
               FROM ${ratings} GROUP BY userId),
     por_nota AS (SELECT userId, rating, COUNT(*) AS n FROM ${ratings} GROUP BY userId, rating),
     modal AS (SELECT userId, MAX(n) AS n_nota_modal FROM por_nota GROUP BY userId),
     base AS (SELECT e.*, n.avaliacoes, n.desvio_notas,
                     100.0 * m.n_nota_modal / n.avaliacoes AS pct_nota_modal
              FROM por_eventos e
              JOIN notas n ON e.userId = n.userId
              JOIN modal m ON e.userId = m.userId),
     -- Limiares calculados a partir da distribuição do próprio dataset
     limiar_a AS (SELECT quantile_cont(max_eventos_10min_apos, 0.999) AS limiar_regra_a   -- QUANTIL DA REGRA A
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

**Output real, small** (`results/small/analises/10_flag_bots.csv`, 610 linhas):

```csv
userId,avaliacoes,eventos,primeiro_dia,ultimo_dia,eventos_registo,mediana_intervalo_registo_s,max_eventos_10min_registo,eventos_apos_registo,mediana_intervalo_apos_s,max_eventos_10min_apos,limiar_regra_a,max_avaliacoes_mesmo_segundo,pct_eventos_lote,desvio_notas,pct_nota_modal,regra_a,regra_b,submissao_lote,sinais_complementares,classificacao
1,232,119,2000-07-30,2000-08-08,118,20.0,26,1,,1,114.80099999999976,7,45.378151260504204,0.8000480467733436,53.44827586206897,false,false,false,0,sem sinais
2,29,29,2015-10-24,2015-10-24,29,9.5,29,0,,,114.80099999999976,1,0.0,0.8056145345791144,31.03448275862069,false,false,false,0,sem sinais
3,39,39,2011-05-27,2011-05-27,39,12.0,27,0,,,114.80099999999976,1,0.0,2.0906417019771424,51.282051282051285,false,false,false,0,sem sinais
4,216,160,1999-12-13,2001-12-05,39,28.5,16,121,38.5,22,114.80099999999976,4,26.25,1.3142038589753633,29.62962962962963,false,false,false,0,sem sinais
5,44,17,1996-11-08,1996-11-08,17,23.0,17,0,,,114.80099999999976,5,82.3529411764706,0.9904405665441197,38.63636363636363,false,false,false,0,sem sinais
```

**Output real, 1m** (`results/1m/analises/10_flag_bots.csv`, 6040 linhas):

```csv
userId,avaliacoes,eventos,primeiro_dia,ultimo_dia,eventos_registo,mediana_intervalo_registo_s,max_eventos_10min_registo,eventos_apos_registo,mediana_intervalo_apos_s,max_eventos_10min_apos,limiar_regra_a,max_avaliacoes_mesmo_segundo,pct_eventos_lote,desvio_notas,pct_nota_modal,regra_a,regra_b,submissao_lote,sinais_complementares,classificacao
1,53,34,2000-12-31,2001-01-06,28,36.0,16,6,39.0,6,40.0,5,35.294117647058826,0.6809666142721429,50.943396226415096,false,false,false,0,sem sinais
2,129,66,2000-12-31,2000-12-31,66,26.0,24,0,,,40.0,6,56.06060606060606,1.001512905945397,33.333333333333336,false,false,false,0,sem sinais
3,51,31,2000-12-31,2000-12-31,31,29.0,15,0,,,40.0,3,48.38709677419355,0.9849853188912879,43.13725490196079,false,false,false,0,sem sinais
4,21,7,2000-12-31,2000-12-31,7,35.5,7,0,,,40.0,5,71.42857142857143,1.077916862241593,47.61904761904762,false,false,false,0,sem sinais
5,198,83,2000-12-31,2000-12-31,83,35.0,22,0,,,40.0,5,71.08433734939759,1.132699316852714,30.80808080808081,false,false,false,0,sem sinais
```

**32M:** não corrido.

### `sql/analise/10_flag_bots_calibracao.sql`

- **Dialeto:** DuckDB
- **Pergunta:** como se distribui o máximo de eventos numa janela de 10 min, depois das primeiras 24 h, e quantos utilizadores ficariam sinalizados com o limiar no p99, no p99,5 e no p99,9? Inclui também os totais de cada regra e categoria, e a taxa de sinalizados.

```sql
-- 10_flag_bots_calibracao.sql (DuckDB) - distribuição do ritmo sustentado e n.º de sinalizados
-- por limiar, para calibrar a regra A de 10_flag_bots.sql
--
-- *** A VALIDAR COM O LUÍS *** (faz parte da deteção que substitui a regra do notebook)
--
-- Pergunta: como se distribui o máximo de eventos numa janela de 10 min, depois das primeiras
-- 24 h, e quantos utilizadores ficariam sinalizados com o limiar no p99, no p99,5 e no p99,9?
-- Inclui também os totais de cada regra e categoria, e a taxa de sinalizados.
--
-- Lê a tabela por utilizador de 10_flag_bots.sql (${flag_bots}); o 05_analises.py corre-a
-- antes. Resultado agregado: uma linha.
--
-- Parâmetros: ${flag_bots}
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

**Output real, small** (`results/small/analises/10_flag_bots_calibracao.csv`, 1 linhas):

```csv
utilizadores_com_atividade_apos_registo,p50,p90,p95,p99,p99_5,p99_9,maximo,sinalizados_a_p99,sinalizados_a_p99_5,sinalizados_a_p99_9,utilizadores,regra_a,regra_b,suspeitos,submissao_lote,so_submissao_lote,pct_suspeitos
248,18.0,52.30000000000001,61.64999999999998,90.83000000000001,100.58999999999992,114.80099999999976,119,3,2,1,610,1,1,2,13,13,0.32786885245901637
```

**Output real, 1m** (`results/1m/analises/10_flag_bots_calibracao.csv`, 1 linhas):

```csv
utilizadores_com_atividade_apos_registo,p50,p90,p95,p99,p99_5,p99_9,maximo,sinalizados_a_p99,sinalizados_a_p99_5,sinalizados_a_p99_9,utilizadores,regra_a,regra_b,suspeitos,submissao_lote,so_submissao_lote,pct_suspeitos
2239,14.0,26.0,29.0,35.0,38.0,40.0,45,25,13,6,6040,6,0,6,339,339,0.09933774834437085
```

**32M:** não corrido.

### `sql/analise/anual.sql`

- **Dialeto:** DuckDB
- **Pergunta:** como evolui, ano a ano, o volume de avaliações, a média e o n.º de utilizadores que avaliaram pelo menos um filme nesse ano?

```sql
-- anual.sql (DuckDB) - avaliações, média e utilizadores ativos por ano
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 108 (id "novo-queries"), consultas_sql()["anual"]. Autor: Luís Pousada (e51d050).
--
-- Pergunta: como evolui, ano a ano, o volume de avaliações, a média e o n.º de utilizadores
-- que avaliaram pelo menos um filme nesse ano?
--
-- Alterações face ao original:
-- - year(to_timestamp(timestamp)) passa a ser a coluna year de ${ratings}, calculada em UTC
--   com epoch_ms (fase 1). to_timestamp depende do fuso da sessão (ver o relatório, P1);
-- - no Parquet particionado, year vem do nome das pastas e o timestamp nem é lido.
-- Fica próxima de sql/05_ratings_por_ano.sql (que continua no benchmark); acrescenta os
-- utilizadores ativos e não arredonda a média.
--
-- Parâmetros: ${ratings}
SELECT year AS ano,
       COUNT(*)               AS num_ratings,
       AVG(rating)            AS media,
       COUNT(DISTINCT userId) AS utilizadores
FROM ${ratings}
GROUP BY year
ORDER BY year;
```

**Output real, small** (`results/small/analises/anual.csv`, 23 linhas):

```csv
ano,num_ratings,media,utilizadores
1996,6040,3.5359271523178806,97
1997,1916,3.7275574112734864,33
1998,507,3.4358974358974357,11
1999,2439,3.772447724477245,27
2000,10061,3.39250571513766,56
```

**Output real, 1m** (`results/1m/analises/anual.csv`, 4 linhas):

```csv
ano,num_ratings,media,utilizadores
2000,904757,3.5903916742285498,6034
2001,68058,3.5122542537247643,1070
2002,24046,3.458828911253431,565
2003,3348,3.486559139784946,178
```

**32M:** não corrido.

### `sql/analise/distribuicao.sql`

- **Dialeto:** DuckDB
- **Pergunta:** para cada valor de rating, quantos utilizadores o usam e que peso tem, em média, no histórico de cada utilizador?

```sql
-- distribuicao.sql (DuckDB) - como os utilizadores usam cada valor da escala
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 108 (id "novo-queries"), consultas_sql()["distribuicao"]. Autor: Luís Pousada (e51d050).
--
-- Pergunta: para cada valor de rating, quantos utilizadores o usam e que peso tem, em média,
-- no histórico de cada utilizador?
--
-- Alterações face ao original:
-- - o original devolvia uma linha por (utilizador, valor): 3 976 linhas no small e ~1,5 M no
--   32M, só para alimentar o heatmap do notebook. A tabela (utilizador, valor) passa a ser
--   uma CTE e o resultado é agregado por valor (no máximo 10 linhas);
-- - prop_media_utilizador é a média, sobre TODOS os utilizadores (0 para quem não usa o
--   valor), da fração do histórico do utilizador com esse valor. As frações somam 1.
-- Os números podem ser reconstruídos a partir da saída original (validado no small e no 1M).
--
-- Parâmetros: ${ratings}
WITH d AS (SELECT userId, rating, COUNT(*) AS n FROM ${ratings} GROUP BY userId, rating),
     t AS (SELECT userId, SUM(n) AS total FROM d GROUP BY userId),
     g AS (SELECT COUNT(*) AS utilizadores, SUM(total) AS avaliacoes FROM t)
SELECT d.rating,
       COUNT(*)                                     AS utilizadores_que_usam,
       100.0 * COUNT(*) / g.utilizadores            AS pct_utilizadores,
       SUM(d.n)                                     AS num_ratings,
       100.0 * SUM(d.n) / g.avaliacoes              AS pct_ratings,
       SUM(d.n * 1.0 / t.total) / g.utilizadores    AS prop_media_utilizador
FROM d JOIN t ON d.userId = t.userId CROSS JOIN g
GROUP BY d.rating, g.utilizadores, g.avaliacoes
ORDER BY d.rating;
```

**Output real, small** (`results/small/analises/distribuicao.csv`, 10 linhas):

```csv
rating,utilizadores_que_usam,pct_utilizadores,num_ratings,pct_ratings,prop_media_utilizador
0.5,179,29.34426229508197,1370,1.3586417549287952,0.014444472452032222
1.0,351,57.540983606557376,2811,2.787694870879448,0.028688493920859908
1.5,191,31.311475409836067,1791,1.776151374509104,0.01106042123797917
2.0,491,80.49180327868852,7551,7.488397001071046,0.06217243169658144
2.5,291,47.704918032786885,5550,5.503986671426872,0.030453110656720402
```

**Output real, 1m** (`results/1m/analises/distribuicao.csv`, 5 linhas):

```csv
rating,utilizadores_que_usam,pct_utilizadores,num_ratings,pct_ratings,prop_media_utilizador
1.0,4667,77.26821192052981,56174,5.616226208722377,0.0493703110323177
2.0,5642,93.41059602649007,107557,10.75345252842156,0.09192010375144008
3.0,6013,99.55298013245033,261197,26.11424212339621,0.2358629344046159
4.0,6034,99.90066225165563,348971,34.889808030121706,0.3523277088074532
5.0,6014,99.56953642384106,226310,22.62627110933815,0.27051894200417353
```

**32M:** não corrido.

### `sql/analise/eventos.sql`

- **Dialeto:** DuckDB
- **Pergunta:** em que (filme, dia) houve muitas notas extremas no mesmo sentido, com a média do dia afastada do histórico anterior do filme? Quantos dos utilizadores desse dia são suspeitos?

```sql
-- eventos.sql (DuckDB) - dias em que um filme recebeu uma concentração de notas extremas que
-- mudou a sua média, cruzados com os utilizadores suspeitos
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 112 (id "novo-advanced"): SQL_AVANCADO["dias_filme"], a view "eventos" e a
--         consulta dos participantes (gravada em eventos_filme.parquet). Autor: Luís Pousada (e51d050).
--
-- Pergunta: em que (filme, dia) houve muitas notas extremas no mesmo sentido, com a média do dia
-- afastada do histórico anterior do filme? Quantos dos utilizadores desse dia são suspeitos?
--
-- Alterações face ao original:
-- - dias_filme e a view eventos só existem como CTEs (d, h, v, ev): a tabela filme x dia
--   (14,7 M linhas no 32M) nunca é devolvida (relatório, P6);
-- - o cruzamento passa a usar a nova deteção (10_flag_bots.sql, tabela ${flag_bots}):
--   suspeitos = regra A ou regra B; em_lote = submissão em lote (conta-se à parte, não é bot).
--   O original usava num_sinais > 0 da regra antiga, que sinalizava 34% dos utilizadores;
-- - LIMIT 100 (justificado): devolve os 100 eventos com mais suspeitos, para inspeção manual.
--   O total de eventos está na coluna total_eventos e no funil (filtros_eventos.sql); no 32M,
--   com estes limites, o notebook registou 90 108 eventos;
-- - limites na CTE lim, os do capítulo 9 (P7), iguais aos de filtros_eventos.sql, a decidir
--   com o Luís; COUNT(DISTINCT CASE ...) em vez de FILTER, como na versão Athena;
-- - dia como data (UTC): timestamp // 86400 é o n.º do dia desde 1970-01-01 em UTC.
--
-- Parâmetros: ${ratings}, ${movies}, ${flag_bots}
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

**Output real, small** (`results/small/analises/eventos.csv`, 0 linhas):

```csv
posicao,movieId,title,dia,tipo,utilizadores,n_anterior,media_anterior,media,variacao,suspeitos,em_lote,pct_suspeitos,total_eventos
```

**Output real, 1m** (`results/1m/analises/eventos.csv`, 100 linhas):

```csv
posicao,movieId,title,dia,tipo,utilizadores,n_anterior,media_anterior,media,variacao,suspeitos,em_lote,pct_suspeitos,total_eventos
1,2919,Year of Living Dangerously (1982),2000-11-20,Avaliações altas,21,260,3.896153846153846,4.476190476190476,0.5800366300366302,1,4,4.761904761904762,3884
2,1097,E.T. the Extra-Terrestrial (1982),2000-12-02,Avaliações altas,18,1901,3.9495002630194636,4.5,0.5504997369805364,1,2,5.555555555555555,3884
3,1721,Titanic (1997),2000-12-02,Avaliações altas,13,1243,3.582461786001609,4.3076923076923075,0.7252305216906985,1,1,7.6923076923076925,3884
4,2906,Random Hearts (1999),2000-11-20,Avaliações baixas,13,146,2.3972602739726026,1.6923076923076923,-0.7049525816649103,1,3,7.6923076923076925,3884
5,1282,Fantasia (1940),2000-12-02,Avaliações altas,11,706,3.9390934844192635,4.454545454545454,0.5154519701261906,1,2,9.090909090909092,3884
```

**32M:** não corrido.

### `sql/analise/evolucao_filmes.sql`

- **Dialeto:** DuckDB
- **Pergunta:** comparando os 5 anos anteriores com os 5 anos mais recentes, que filmes (com pelo menos 10 avaliações em cada período) mudaram mais de média?

```sql
-- evolucao_filmes.sql (DuckDB) - filmes cuja média mais subiu ou desceu entre dois períodos de 5 anos
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 112 (id "novo-advanced"), SQL_AVANCADO["evolucao_filmes"]. Autor: Luís Pousada (e51d050).
--
-- Pergunta: comparando os 5 anos anteriores com os 5 anos mais recentes, que filmes (com pelo
-- menos 10 avaliações em cada período) mudaram mais de média?
--
-- Alterações face ao original (relatório, P1 e P3):
-- - OPÇÃO USADA: SÓ ANOS COMPLETOS. O original terminava o período recente em MAX(ano), que é
--   um ano parcial (small: 2018 até 24/09; 32M: 2023 até 13/10; 1M: 2003 até 28/02), e
--   comparava 5 anos com pouco mais de 4. Aqui o último ano só conta se o último rating for
--   de 31 de dezembro (UTC); senão o fim passa para o ano anterior. Não se anualiza: as
--   médias de um ano parcial não precisam de anualização, mas o período ficaria desigual.
--   As colunas periodo_anterior, periodo_recente e criterio dizem, em cada linha, que anos
--   foram usados e que ano foi excluído;
-- - year de ${ratings} (UTC) em vez de year(to_timestamp(timestamp)) calculado 4 vezes por
--   linha (fuso, P1), e WHERE com os 10 anos usados (partition pruning no ratings_part);
-- - colunas pela ordem: movieId, title, contagens, médias, variação, posições, períodos.
-- No 1M (2000-04-25 a 2003-02-28) não há 10 anos completos: o resultado é vazio, como o
-- do original (que também não tinha dados no período anterior).
--
-- Parâmetros: ${ratings}, ${movies}
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

**Output real, small** (`results/small/analises/evolucao_filmes.csv`, 366 linhas):

```csv
movieId,title,n_anterior,n_recente,media_anterior,media_recente,variacao,posicao_anterior,posicao_recente,periodo_anterior,periodo_recente,criterio
1676,Starship Troopers (1997),11,16,2.9545454545454546,3.84375,0.8892045454545454,348,146,2008–2012,2013–2017,"só anos completos: exclui 2018 (parcial, último rating 2018-09-24)"
2916,Total Recall (1990),14,14,3.25,4.071428571428571,0.8214285714285712,321,50,2008–2012,2013–2017,"só anos completos: exclui 2018 (parcial, último rating 2018-09-24)"
344,Ace Ventura: Pet Detective (1994),28,21,2.625,3.4285714285714284,0.8035714285714284,365,291,2008–2012,2013–2017,"só anos completos: exclui 2018 (parcial, último rating 2018-09-24)"
57368,Cloverfield (2008),13,14,2.9615384615384617,3.7142857142857144,0.7527472527472527,346,195,2008–2012,2013–2017,"só anos completos: exclui 2018 (parcial, último rating 2018-09-24)"
2617,"Mummy, The (1999)",17,14,2.7941176470588234,3.5357142857142856,0.7415966386554622,361,259,2008–2012,2013–2017,"só anos completos: exclui 2018 (parcial, último rating 2018-09-24)"
```

**Output real, 1m** (`results/1m/analises/evolucao_filmes.csv`, 0 linhas):

```csv
movieId,title,n_anterior,n_recente,media_anterior,media_recente,variacao,posicao_anterior,posicao_recente,periodo_anterior,periodo_recente,criterio
```

**32M:** não corrido.

### `sql/analise/filmes_ano.sql`

- **Dialeto:** DuckDB
- **Pergunta:** como evoluiu, ano a ano, a média do filme com a maior subida (variação >= 0,5) e do filme com a maior descida (variação <= -0,5) de evolucao_filmes?

```sql
-- filmes_ano.sql (DuckDB) - série anual do filme que mais subiu e do que mais desceu (para gráfico)
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 112 (id "novo-advanced"), consulta "filmes_ano" (gravada em
--         filmes_ano_selecionados.parquet). Autor: Luís Pousada (e51d050).
--
-- Pergunta: como evoluiu, ano a ano, a média do filme com a maior subida (variação >= 0,5) e
-- do filme com a maior descida (variação <= -0,5) de evolucao_filmes?
--
-- Alterações face ao original:
-- - os filmes são escolhidos com a versão corrigida de evolucao_filmes (só anos completos);
--   as CTEs limites/fim/s/e são as mesmas de evolucao_filmes.sql;
-- - (SELECT ... LIMIT 1) UNION (SELECT ... LIMIT 1) passa a ROW_NUMBER() em CTEs (mesmo
--   resultado, portável para o Athena), e acrescenta-se a coluna tipo;
-- - year de ${ratings} (UTC) em vez de year(to_timestamp(timestamp)) (fuso).
-- A série usa todos os anos com avaliações desses filmes, como no original.
--
-- Parâmetros: ${ratings}, ${movies}
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
           WHERE n_anterior >= 10 AND n_recente >= 10),
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

**Output real, small** (`results/small/analises/filmes_ano.csv`, 39 linhas):

```csv
movieId,title,tipo,ano,avaliacoes,media
1380,Grease (1978),Maior descida,1997,2,3.5
1380,Grease (1978),Maior descida,1998,1,4.0
1380,Grease (1978),Maior descida,1999,2,5.0
1380,Grease (1978),Maior descida,2000,7,3.142857142857143
1380,Grease (1978),Maior descida,2001,2,3.5
```

**Output real, 1m** (`results/1m/analises/filmes_ano.csv`, 0 linhas):

```csv
movieId,title,tipo,ano,avaliacoes,media
```

**32M:** não corrido.

### `sql/analise/filtros_eventos.sql`

- **Dialeto:** DuckDB
- **Pergunta:** quantos pares (filme, dia) passam cada filtro, por ordem: histórico anterior -> n.º de utilizadores no dia -> proporção de notas extremas -> variação da média face ao histórico no mesmo sentido?

```sql
-- filtros_eventos.sql (DuckDB) - funil dos filtros dos "eventos" (concentrações de notas
-- extremas num filme, num dia)
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 112 (id "novo-advanced"): SQL_AVANCADO["dias_filme"] (tabela filme x dia),
--         a view "eventos" e a consulta "filtros". Autor: Luís Pousada (e51d050).
--
-- Pergunta: quantos pares (filme, dia) passam cada filtro, por ordem: histórico anterior ->
-- n.º de utilizadores no dia -> proporção de notas extremas -> variação da média face ao
-- histórico no mesmo sentido?
--
-- Alterações face ao original:
-- - dias_filme (uma linha por filme x dia: 99 538 no small, 14,7 M no 32M) deixa de ser um
--   resultado: só existe como CTE (d, h, v) e a query devolve uma linha (relatório, P6);
-- - os limites estão numa CTE (lim) e são devolvidos com o resultado. São os do capítulo 9
--   do notebook (os das queries SQL), não os do capítulo 8 (P7): escolher um só conjunto é
--   uma decisão a tomar com o Luís;
-- - count_if em vez de COUNT(*) FILTER e AVG((cond)::INTEGER); janela por extenso.
-- O dia é timestamp // 86400 (dia UTC, sem conversão de fuso).
--
-- Parâmetros: ${ratings}
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

**Output real, small** (`results/small/analises/filtros_eventos.csv`, 1 linhas):

```csv
todos_filme_dia,com_historico,com_utilizadores,com_extremos,eventos,min_anterior,min_utilizadores,nota_baixa,nota_alta,min_frac_extremas,min_variacao
99538,70858,0,0,0,5,5,2.0,4.0,0.51,0.5
```

**Output real, 1m** (`results/1m/analises/filtros_eventos.csv`, 1 linhas):

```csv
todos_filme_dia,com_historico,com_utilizadores,com_extremos,eventos,min_anterior,min_utilizadores,nota_baixa,nota_alta,min_frac_extremas,min_variacao
407251,393200,43440,30551,3884,5,5,2.0,4.0,0.51,0.5
```

**32M:** não corrido.

### `sql/analise/grupos_atividade.sql`

- **Dialeto:** DuckDB
- **Pergunta:** os utilizadores mais ativos (no total do seu histórico) dão notas diferentes dos menos ativos? Média, em cada ano, das médias dos utilizadores de cada faixa.

```sql
-- grupos_atividade.sql (DuckDB) - média anual por faixa de atividade total do utilizador
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 109 (id "novo-analytics"), consultas_complementares()["grupos_atividade"]. Autor: Luís Pousada (e51d050).
--
-- Pergunta: os utilizadores mais ativos (no total do seu histórico) dão notas diferentes dos
-- menos ativos? Média, em cada ano, das médias dos utilizadores de cada faixa.
--
-- Alterações face ao original (relatório, P1 e P4):
-- - faixas novas. O MovieLens só inclui utilizadores com pelo menos 20 avaliações, por isso
--   as faixas originais "Até 5" e "6–20" ficavam sempre vazias (ou só com quem tinha
--   exatamente 20). Faixas fixas a partir de 20, iguais em todos os datasets (para os
--   comparar): 20–49, 50–99, 100–249, 250–999 e 1000 ou mais. Utilizadores por faixa:
--   small 225/137/143/93/12; 1M 1743/1352/1720/1184/41; no 32M (mediana 73, p90 364,
--   máximo 33 332) também nenhuma fica vazia;
-- - faixa_min (limite inferior) para ordenar as faixas corretamente;
-- - ANY_VALUE (não existe no Athena) substituído por um join depois de agregar;
-- - year de ${ratings} (UTC) em vez de year(to_timestamp(timestamp)) (fuso).
-- A coluna utilizadores conta pares (utilizador, ano) da faixa nesse ano: é o n.º de
-- utilizadores da faixa ativos nesse ano.
--
-- Parâmetros: ${ratings}
WITH totais AS (SELECT userId, COUNT(*) AS total FROM ${ratings} GROUP BY userId),
     u AS (SELECT userId, year AS ano, AVG(rating) AS media_utilizador, COUNT(*) AS n
           FROM ${ratings}
           GROUP BY userId, year),
     g AS (SELECT u.ano, u.media_utilizador, u.n,
                  CASE WHEN t.total < 50 THEN 20 WHEN t.total < 100 THEN 50 WHEN t.total < 250 THEN 100
                       WHEN t.total < 1000 THEN 250 ELSE 1000 END AS faixa_min
           FROM u JOIN totais t ON u.userId = t.userId)
SELECT ano,
       faixa_min,
       CASE faixa_min WHEN 20 THEN '20–49' WHEN 50 THEN '50–99' WHEN 100 THEN '100–249'
                      WHEN 250 THEN '250–999' ELSE '1000 ou mais' END AS grupo,
       AVG(media_utilizador) AS media,
       COUNT(*)              AS utilizadores,
       SUM(n)                AS avaliacoes
FROM g
GROUP BY ano, faixa_min
ORDER BY ano, faixa_min;
```

**Output real, small** (`results/small/analises/grupos_atividade.csv`, 108 linhas):

```csv
ano,faixa_min,grupo,media,utilizadores,avaliacoes
1996,20,20–49,3.6632748220549933,45,1471
1996,50,50–99,3.571784559639958,34,2239
1996,100,100–249,3.429990940873896,17,2016
1996,250,250–999,3.4936305732484074,1,314
1997,20,20–49,3.6484258969121552,18,574
```

**Output real, 1m** (`results/1m/analises/grupos_atividade.csv`, 20 linhas):

```csv
ano,faixa_min,grupo,media,utilizadores,avaliacoes
2000,20,20–49,3.771832504045591,1742,55570
2000,50,50–99,3.7738989609173794,1352,91982
2000,100,100–249,3.7118898780347807,1717,252550
2000,250,250–999,3.54734214380573,1182,459585
2000,1000,1000 ou mais,3.3608922223688915,41,45070
```

**32M:** não corrido.

### `sql/analise/integridade.sql`

- **Dialeto:** DuckDB
- **Pergunta:** movies tem ids repetidos? Há avaliações de filmes que não existem em movies? O 05_analises.py falha se ids_filmes_repetidos ou ratings_sem_filme forem diferentes de 0.

```sql
-- integridade.sql (DuckDB) - chaves e relações entre ratings e movies
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 109 (id "novo-analytics"), consultas_complementares()["integridade"]. Autor: Luís Pousada (e51d050).
--
-- Pergunta: movies tem ids repetidos? Há avaliações de filmes que não existem em movies?
-- O 05_analises.py falha se ids_filmes_repetidos ou ratings_sem_filme forem diferentes de 0.
--
-- Alterações face ao original (relatório, P5):
-- - o original chamava filmes_sem_metadados a um COUNT(*) de "ratings ANTI JOIN movies", ou
--   seja, contava LINHAS de avaliações, não filmes. Passa a haver duas colunas:
--   ratings_sem_filme (linhas) e filmes_sem_metadados (COUNT(DISTINCT movieId));
-- - NOT EXISTS em vez de ANTI JOIN (só existe no DuckDB), igual no Athena.
--
-- Parâmetros: ${ratings}, ${movies}
SELECT (SELECT COUNT(*) - COUNT(DISTINCT movieId) FROM ${movies})               AS ids_filmes_repetidos,
       (SELECT COUNT(*) FROM ${ratings} r
         WHERE NOT EXISTS (SELECT 1 FROM ${movies} m WHERE m.movieId = r.movieId))  AS ratings_sem_filme,
       (SELECT COUNT(DISTINCT r.movieId) FROM ${ratings} r
         WHERE NOT EXISTS (SELECT 1 FROM ${movies} m WHERE m.movieId = r.movieId))  AS filmes_sem_metadados,
       (SELECT COUNT(*) FROM ${movies} WHERE title IS NULL OR genres IS NULL)       AS filmes_com_nulos;
```

**Output real, small** (`results/small/analises/integridade.csv`, 1 linhas):

```csv
ids_filmes_repetidos,ratings_sem_filme,filmes_sem_metadados,filmes_com_nulos
0,0,0,0
```

**Output real, 1m** (`results/1m/analises/integridade.csv`, 1 linhas):

```csv
ids_filmes_repetidos,ratings_sem_filme,filmes_sem_metadados,filmes_com_nulos
0,0,0,0
```

**32M:** não corrido.

### `sql/analise/mensal.sql`

- **Dialeto:** DuckDB
- **Pergunta:** como se distribuem as avaliações ao longo dos meses (picos, lacunas)?

```sql
-- mensal.sql (DuckDB) - avaliações e média por mês
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 109 (id "novo-analytics"), consultas_complementares()["mensal"]. Autor: Luís Pousada (e51d050).
--
-- Pergunta: como se distribuem as avaliações ao longo dos meses (picos, lacunas)?
--
-- Alterações face ao original:
-- - strftime(to_timestamp(timestamp), ...) passa a strftime(epoch_ms(timestamp * 1000), ...).
--   to_timestamp devolve TIMESTAMP WITH TIME ZONE e o mês dependia do fuso da sessão: em
--   America/New_York ou Asia/Tokyo o original dava outros números (relatório, P1, e
--   testes do bloco 1). epoch_ms devolve TIMESTAMP sem fuso, ou seja, UTC;
-- - GROUP BY 1 em vez do alias.
--
-- Parâmetros: ${ratings}
SELECT strftime(epoch_ms(timestamp * 1000), '%Y-%m') AS mes,
       COUNT(*)    AS num_ratings,
       AVG(rating) AS media
FROM ${ratings}
GROUP BY 1
ORDER BY 1;
```

**Output real, small** (`results/small/analises/mensal.csv`, 267 linhas):

```csv
mes,num_ratings,media
1996-03,58,3.9827586206896552
1996-04,165,3.7393939393939393
1996-05,832,3.514423076923077
1996-06,883,3.5402038505096263
1996-07,489,3.6952965235173822
```

**Output real, 1m** (`results/1m/analises/mensal.csv`, 35 linhas):

```csv
mes,num_ratings,media
2000-04,11396,3.5533520533520533
2000-05,67437,3.6134466242567136
2000-06,54486,3.6339059574936683
2000-07,90334,3.630072840790843
2000-08,182109,3.572173807994113
```

**32M:** não corrido.

### `sql/analise/perfis_ativos.sql`

- **Dialeto:** DuckDB
- **Pergunta:** entre os utilizadores que avaliaram em cada ano (e com pelo menos 2 avaliações acumuladas até esse ano), quantos usaram até aí só estrelas inteiras, só valores não inteiros (x,5) ou os dois?

```sql
-- perfis_ativos.sql (DuckDB) - por ano, utilizadores ativos com histórico só de inteiros,
-- só de não inteiros ou misto
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 109 (id "novo-analytics"), consultas_complementares()["perfis_ativos"]. Autor: Luís Pousada (e51d050).
--
-- Pergunta: entre os utilizadores que avaliaram em cada ano (e com pelo menos 2 avaliações
-- acumuladas até esse ano), quantos usaram até aí só estrelas inteiras, só valores não
-- inteiros (x,5) ou os dois?
--
-- Alterações face ao original:
-- - year de ${ratings} (UTC) em vez de year(to_timestamp(timestamp)) (fuso, P1);
-- - count_if(cond) em vez de SUM((cond)::BIGINT) e janela escrita por extenso em vez da
--   cláusula WINDOW, para ficar igual à versão Athena;
-- - rótulo "Só não inteiros" (P8: um 0,5 não é um "meio ponto" de um inteiro).
-- A lógica é a do original.
--
-- Parâmetros: ${ratings}
WITH y AS (SELECT userId, year AS ano, COUNT(*) AS n,
                  count_if(rating = floor(rating))  AS inteiros,
                  count_if(rating != floor(rating)) AS nao_inteiros
           FROM ${ratings}
           GROUP BY userId, year),
     c AS (SELECT ano,
                  SUM(n)            OVER (PARTITION BY userId ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS total,
                  SUM(inteiros)     OVER (PARTITION BY userId ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS i,
                  SUM(nao_inteiros) OVER (PARTITION BY userId ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ni
           FROM y)
SELECT ano,
       CASE WHEN ni = 0 THEN 'Só inteiros' WHEN i = 0 THEN 'Só não inteiros' ELSE 'Misto' END AS perfil,
       COUNT(*) AS utilizadores
FROM c
WHERE total >= 2
GROUP BY 1, 2
ORDER BY 1, 2;
```

**Output real, small** (`results/small/analises/perfis_ativos.csv`, 28 linhas):

```csv
ano,perfil,utilizadores
1996,Só inteiros,97
1997,Só inteiros,33
1998,Só inteiros,11
1999,Só inteiros,27
2000,Só inteiros,56
```

**Output real, 1m** (`results/1m/analises/perfis_ativos.csv`, 4 linhas):

```csv
ano,perfil,utilizadores
2000,Só inteiros,6034
2001,Só inteiros,1070
2002,Só inteiros,565
2003,Só inteiros,178
```

**32M:** não corrido.

### `sql/analise/perfis_cumulativos.sql`

- **Dialeto:** DuckDB
- **Pergunta:** como perfis_ativos, mas cada utilizador conta em todos os anos desde que entrou (mesmo nos anos sem atividade), com o histórico acumulado até esse ano.

```sql
-- perfis_cumulativos.sql (DuckDB) - perfis de uso da escala na população acumulada
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 109 (id "novo-analytics"), consultas_complementares()["perfis_cumulativos"]. Autor: Luís Pousada (e51d050).
--
-- Pergunta: como perfis_ativos, mas cada utilizador conta em todos os anos desde que entrou
-- (mesmo nos anos sem atividade), com o histórico acumulado até esse ano.
--
-- Alterações face ao original:
-- - year de ${ratings} (UTC) em vez de year(to_timestamp(timestamp)) (fuso, P1);
-- - count_if, janela por extenso e GROUP BY 1, 2, como na versão Athena;
-- - rótulo "Só não inteiros" (P8).
-- A grelha utilizadores x anos é intencional (no 32M, 200 948 x 29 = 5,8 M linhas), mas só
-- existe como CTE: o resultado devolvido é agregado (no máximo 3 linhas por ano).
--
-- Parâmetros: ${ratings}
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

**Output real, small** (`results/small/analises/perfis_cumulativos.csv`, 39 linhas):

```csv
ano,perfil,utilizadores
1996,Só inteiros,97
1997,Só inteiros,124
1998,Só inteiros,133
1999,Só inteiros,159
2000,Só inteiros,207
```

**Output real, 1m** (`results/1m/analises/perfis_cumulativos.csv`, 4 linhas):

```csv
ano,perfil,utilizadores
2000,Só inteiros,6034
2001,Só inteiros,6038
2002,Só inteiros,6040
2003,Só inteiros,6040
```

**32M:** não corrido.

### `sql/analise/ponderado.sql`

- **Dialeto:** DuckDB
- **Pergunta:** que filmes têm a melhor média quando se "puxa" a média dos filmes com poucas avaliações para a média global? weighted = v/(v+m)*R + m/(v+m)*C, com m = 100 avaliações, R = média do filme, v = n.º de avaliações do filme e C = média global.

```sql
-- ponderado.sql (DuckDB) - top 10 de filmes por média bayesiana (média ponderada)
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 108 (id "novo-queries"), consultas_sql()["ponderado"]. Autor: Luís Pousada (e51d050).
--
-- Pergunta: que filmes têm a melhor média quando se "puxa" a média dos filmes com poucas
-- avaliações para a média global? weighted = v/(v+m)*R + m/(v+m)*C, com m = 100 avaliações,
-- R = média do filme, v = n.º de avaliações do filme e C = média global.
--
-- Alterações face ao original:
-- - ${ratings}/${movies} em vez das views do notebook (convenção da fase 1);
-- - aliases R e C passam a media_filme e media_global (no Athena, R e r seriam o mesmo nome);
-- - acrescenta a coluna media_global, para validar a média global contra o 04_eda.py.
-- A fórmula, o peso 100 e o desempate por movieId são os do original.
--
-- Parâmetros: ${ratings}, ${movies}
WITH s AS (SELECT movieId, AVG(rating) AS media_filme, COUNT(*) AS v
           FROM ${ratings} GROUP BY movieId),
     p AS (SELECT AVG(rating) AS media_global FROM ${ratings})
SELECT s.movieId, m.title, s.media_filme AS avg_rating, s.v AS num_ratings,
       s.v / (s.v + 100.0) * s.media_filme + 100.0 / (s.v + 100.0) * p.media_global AS weighted,
       p.media_global
FROM s CROSS JOIN p
JOIN ${movies} m ON s.movieId = m.movieId
ORDER BY weighted DESC, s.movieId
LIMIT 10;
```

**Output real, small** (`results/small/analises/ponderado.csv`, 10 linhas):

```csv
movieId,title,avg_rating,num_ratings,weighted,media_global
318,"Shawshank Redemption, The (1994)",4.429022082018927,317,4.206608389356586,3.501556983616962
2959,Fight Club (1999),4.272935779816514,218,4.030363831326088,3.501556983616962
296,Pulp Fiction (1994),4.197068403908795,307,4.026181077055765,3.501556983616962
260,Star Wars: Episode IV - A New Hope (1977),4.231075697211155,251,4.02323560786808,3.501556983616962
858,"Godfather, The (1972)",4.2890625,192,4.019368830005808,3.501556983616962
```

**Output real, 1m** (`results/1m/analises/ponderado.csv`, 10 linhas):

```csv
movieId,title,avg_rating,num_ratings,weighted,media_global
318,"Shawshank Redemption, The (1994)",4.554557700942973,2227,4.512744497336886,3.581564453029317
858,"Godfather, The (1972)",4.524966261808367,2223,4.484354905425283,3.581564453029317
527,Schindler's List (1993),4.510416666666667,2304,4.471778887397226,3.581564453029317
50,"Usual Suspects, The (1995)",4.517106001121705,1783,4.467422435105114,3.581564453029317
1198,Raiders of the Lost Ark (1981),4.477724741447892,2514,4.44344163936608,3.581564453029317
```

**32M:** não corrido.

### `sql/analise/qualidade.sql`

- **Dialeto:** DuckDB
- **Pergunta:** as avaliações têm nulos, valores fora da escala (0,5 a 5 em meios pontos) ou o mesmo utilizador a avaliar o mesmo filme mais de uma vez? O 05_analises.py falha se linhas_com_nulos ou fora_dominio_comum forem diferentes de 0 (as mesmas asserções do notebook) e compara linhas/utilizadores/filmes com o 04_eda.py.

```sql
-- qualidade.sql (DuckDB) - nulos, domínio da escala e pares (utilizador, filme) repetidos
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 108 (id "novo-queries"), consultas_sql()["qualidade"]. Autor: Luís Pousada (e51d050).
--
-- Pergunta: as avaliações têm nulos, valores fora da escala (0,5 a 5 em meios pontos) ou o
-- mesmo utilizador a avaliar o mesmo filme mais de uma vez?
-- O 05_analises.py falha se linhas_com_nulos ou fora_dominio_comum forem diferentes de 0
-- (as mesmas asserções do notebook) e compara linhas/utilizadores/filmes com o 04_eda.py.
--
-- Alterações face ao original: ${ratings} e "timestamp" entre aspas (palavra reservada
-- noutros motores). A lógica é a mesma.
-- No 32M, COUNT(DISTINCT (userId, movieId)) guarda 32 M pares; o DuckDB despeja para disco
-- se faltar memória.
--
-- Parâmetros: ${ratings}
SELECT COUNT(*)                                       AS linhas,
       COUNT(DISTINCT userId)                         AS utilizadores,
       COUNT(DISTINCT movieId)                        AS filmes,
       COUNT(*) - COUNT(DISTINCT (userId, movieId))   AS pares_repetidos,
       COUNT(*) FILTER (WHERE userId IS NULL OR movieId IS NULL OR rating IS NULL
                              OR "timestamp" IS NULL) AS linhas_com_nulos,
       COUNT(*) FILTER (WHERE rating < 0.5 OR rating > 5
                              OR rating * 2 != floor(rating * 2)) AS fora_dominio_comum,
       COUNT(*) FILTER (WHERE rating != floor(rating)) AS nao_inteiros,
       COUNT(*) FILTER (WHERE rating < 1)              AS inferior_a_um
FROM ${ratings};
```

**Output real, small** (`results/small/analises/qualidade.csv`, 1 linhas):

```csv
linhas,utilizadores,filmes,pares_repetidos,linhas_com_nulos,fora_dominio_comum,nao_inteiros,inferior_a_um
100836,610,9724,0,0,0,30398,1370
```

**Output real, 1m** (`results/1m/analises/qualidade.csv`, 1 linhas):

```csv
linhas,utilizadores,filmes,pares_repetidos,linhas_com_nulos,fora_dominio_comum,nao_inteiros,inferior_a_um
1000209,6040,3706,0,0,0,0,0
```

**32M:** não corrido.

### `sql/analise/valores_ano.sql`

- **Dialeto:** DuckDB
- **Pergunta:** quantas avaliações de cada valor (0,5 a 5) houve em cada ano? Mostra, por exemplo, a partir de que ano aparecem os meios pontos.

```sql
-- valores_ano.sql (DuckDB) - distribuição dos valores de rating em cada ano
-- Origem: notebook Lab_Parquet_DuckDB_Polars_Arrow_EDA_BDF26_G1_v1_3.ipynb (igual no _v2),
--         célula 108 (id "novo-queries"), consultas_sql()["valores_ano"]. Autor: Luís Pousada (e51d050).
--
-- Pergunta: quantas avaliações de cada valor (0,5 a 5) houve em cada ano? Mostra, por
-- exemplo, a partir de que ano aparecem os meios pontos.
--
-- Alterações face ao original: year de ${ratings} (UTC, fase 1) em vez de
-- year(to_timestamp(timestamp)), que depende do fuso da sessão (relatório, P1).
--
-- Parâmetros: ${ratings}
SELECT year AS ano, rating, COUNT(*) AS num_ratings
FROM ${ratings}
GROUP BY year, rating
ORDER BY year, rating;
```

**Output real, small** (`results/small/analises/valores_ano.csv`, 195 linhas):

```csv
ano,rating,num_ratings
1996,1.0,195
1996,2.0,404
1996,3.0,2575
1996,4.0,1701
1996,5.0,1165
```

**Output real, 1m** (`results/1m/analises/valores_ano.csv`, 20 linhas):

```csv
ano,rating,num_ratings
2000,1.0,51027
2000,2.0,96069
2000,3.0,234296
2000,4.0,314446
2000,5.0,208919
```

**32M:** não corrido.

### 4.3 `sql/cloud/` (DuckDB, só fase 2)

### `sql/cloud/06_ratings_desde_2015.sql`

- **Dialeto:** DuckDB
- **Pergunta:** Partition pruning: a mesma agregação da 05_ratings_por_ano.sql, mas só a partir de 2015. Está em sql/cloud/ (e não em sql/) para não alterar o benchmark da fase 1. A versão para o Athena está em sql/athena/queries/06_ratings_desde_2015.sql.

```sql
-- 06_ratings_desde_2015.sql (DuckDB) - query extra do benchmark da fase 2
-- Partition pruning: a mesma agregação da 05_ratings_por_ano.sql, mas só a partir de 2015.
-- Está em sql/cloud/ (e não em sql/) para não alterar o benchmark da fase 1.
-- A versão para o Athena está em sql/athena/queries/06_ratings_desde_2015.sql.
--
-- Ligação às aulas:
-- - Parquet particionado: com WHERE year >= 2015 o DuckDB não abre as pastas
--   year=1995 ... year=2014 (partition pruning).
-- - Parquet sem partição e CSV: year é calculado a partir do timestamp, linha a linha,
--   e o filtro só se aplica depois de ler o ficheiro.
--
-- Parâmetros: ${ratings}
SELECT year,
       COUNT(*)                 AS num_ratings,
       ROUND(AVG(rating), 3)    AS avg_rating
FROM ${ratings}
WHERE year >= 2015
GROUP BY year
ORDER BY year;
```

**Output:** sem CSV de resultados. N.º de linhas (DuckDB sobre `data/cloud/`, `results/cloud_benchmarks.csv`): small: 4, 32m: 9.

### 4.4 `sql/athena/queries/` (Athena, benchmark)

### `sql/athena/queries/01_generos.sql`

- **Dialeto:** Athena (Trino)
- **Pergunta:** quais são os géneros de filmes no dataset?

```sql
-- 01_generos.sql (Athena) - equivalente a sql/01_generos.sql
-- Pergunta 7.1: quais são os géneros de filmes no dataset?
--
-- Diferença para o DuckDB: em Trino/Athena, partir uma lista em linhas faz-se com
-- CROSS JOIN UNNEST(...) AS t(coluna), em vez de unnest() dentro do SELECT.
-- O Athena cobra no mínimo 10 MB por query, e movies tem ~1.4 MB: esta query paga o mínimo.
--
-- Parâmetros: ${movies}
SELECT DISTINCT t.genre
FROM ${movies} AS m
CROSS JOIN UNNEST(split(m.genres, '|')) AS t(genre)
ORDER BY t.genre
```

**Output:** nunca corrida no Athena (não há linhas `engine=athena` em `results/cloud_benchmarks.csv`). A mesma pergunta em DuckDB sobre `data/cloud/` deu: small: 20 linhas, 32m: 20 linhas.

### `sql/athena/queries/02_filmes_por_genero.sql`

- **Dialeto:** Athena (Trino)
- **Pergunta:** qual é o número de filmes por género?

```sql
-- 02_filmes_por_genero.sql (Athena) - equivalente a sql/02_filmes_por_genero.sql
-- Pergunta 7.2: qual é o número de filmes por género?
--
-- Diferença para o DuckDB: CROSS JOIN UNNEST em vez de unnest() no SELECT.
--
-- Parâmetros: ${movies}
WITH movie_genre AS (
    SELECT m.movieid, t.genre
    FROM ${movies} AS m
    CROSS JOIN UNNEST(split(m.genres, '|')) AS t(genre)
)
SELECT genre,
       COUNT(*)                                                         AS num_movies,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ${movies}), 1)    AS pct_movies
FROM movie_genre
GROUP BY genre
ORDER BY num_movies DESC, genre
```

**Output:** nunca corrida no Athena (não há linhas `engine=athena` em `results/cloud_benchmarks.csv`). A mesma pergunta em DuckDB sobre `data/cloud/` deu: small: 20 linhas, 32m: 20 linhas.

### `sql/athena/queries/03_avaliacoes_por_utilizador.sql`

- **Dialeto:** Athena (Trino)
- **Pergunta:** qual é a distribuição das avaliações por utilizador?

```sql
-- 03_avaliacoes_por_utilizador.sql (Athena) - equivalente a sql/03_avaliacoes_por_utilizador.sql
-- Pergunta 7.3: qual é a distribuição das avaliações por utilizador?
--
-- Diferença para o DuckDB: o Athena não tem MEDIAN exata. approx_percentile(rating, 0.5)
-- dá uma mediana aproximada, por isso a coluna median pode diferir ligeiramente da do DuckDB
-- (o n.º de linhas, um por utilizador, é o mesmo).
--
-- Parâmetros: ${ratings}
SELECT r.userid,
       COUNT(*)                                 AS num_ratings,
       ROUND(AVG(r.rating), 3)                  AS mean,
       ROUND(STDDEV_SAMP(r.rating), 3)          AS std,
       MIN(r.rating)                            AS min,
       approx_percentile(r.rating, 0.5)         AS median,
       MAX(r.rating)                            AS max
FROM ${ratings} AS r
GROUP BY r.userid
ORDER BY r.userid
```

**Output:** nunca corrida no Athena (não há linhas `engine=athena` em `results/cloud_benchmarks.csv`). A mesma pergunta em DuckDB sobre `data/cloud/` deu: small: 610 linhas, 32m: 200948 linhas.

### `sql/athena/queries/04_top_filmes.sql`

- **Dialeto:** Athena (Trino)
- **Pergunta:** quais são os filmes com a média de avaliação mais alta (mín. 100 avaliações)?

```sql
-- 04_top_filmes.sql (Athena) - equivalente a sql/04_top_filmes.sql
-- Pergunta 7.4: quais são os filmes com a média de avaliação mais alta (mín. 100 avaliações)?
--
-- Diferença para o DuckDB: JOIN ... ON em vez de USING, para poder usar m.movieid
-- qualificado no GROUP BY sem ambiguidade.
--
-- Parâmetros: ${ratings}, ${movies}
SELECT m.title, ROUND(AVG(r.rating), 2) AS avg_rating, COUNT(*) AS num_ratings
FROM ${ratings} AS r
JOIN ${movies} AS m ON r.movieid = m.movieid
GROUP BY m.movieid, m.title
HAVING COUNT(*) >= 100
ORDER BY AVG(r.rating) DESC
LIMIT 10
```

**Output:** nunca corrida no Athena (não há linhas `engine=athena` em `results/cloud_benchmarks.csv`). A mesma pergunta em DuckDB sobre `data/cloud/` deu: small: 10 linhas, 32m: 10 linhas.

### `sql/athena/queries/05_ratings_por_ano.sql`

- **Dialeto:** Athena (Trino)
- **Pergunta:** Query temporal: número de ratings e média por ano.

```sql
-- 05_ratings_por_ano.sql (Athena) - equivalente a sql/05_ratings_por_ano.sql
-- Query temporal: número de ratings e média por ano.
--
-- Em ratings_part, year vem do nome das pastas e o Athena só lê a coluna rating.
-- Em ratings e ratings_csv, year é calculado a partir do timestamp (ver athena_benchmark.py),
-- o que obriga a ler também essa coluna. Compare o DataScannedInBytes dos três formatos.
--
-- Parâmetros: ${ratings}
SELECT r.year,
       COUNT(*)                 AS num_ratings,
       ROUND(AVG(r.rating), 3)  AS avg_rating
FROM ${ratings} AS r
GROUP BY r.year
ORDER BY r.year
```

**Output:** nunca corrida no Athena (não há linhas `engine=athena` em `results/cloud_benchmarks.csv`). A mesma pergunta em DuckDB sobre `data/cloud/` deu: small: 23 linhas, 32m: 29 linhas.

### `sql/athena/queries/06_ratings_desde_2015.sql`

- **Dialeto:** Athena (Trino)
- **Pergunta:** Partition pruning: a mesma agregação da query 05, mas só a partir de 2015.

```sql
-- 06_ratings_desde_2015.sql (Athena) - equivalente a sql/cloud/06_ratings_desde_2015.sql
-- Partition pruning: a mesma agregação da query 05, mas só a partir de 2015.
--
-- Em ratings_part, o filtro year >= 2015 é resolvido pelos nomes das pastas: o Athena
-- nem abre os ficheiros dos anos anteriores e cobra só os bytes das pastas lidas.
-- Em ratings (Parquet sem partição) tem de ler as colunas timestamp e rating do ficheiro todo;
-- em ratings_csv lê o ficheiro inteiro.
--
-- Parâmetros: ${ratings}
SELECT r.year,
       COUNT(*)                 AS num_ratings,
       ROUND(AVG(r.rating), 3)  AS avg_rating
FROM ${ratings} AS r
WHERE r.year >= 2015
GROUP BY r.year
ORDER BY r.year
```

**Output:** nunca corrida no Athena (não há linhas `engine=athena` em `results/cloud_benchmarks.csv`). A mesma pergunta em DuckDB sobre `data/cloud/` deu: small: 4 linhas, 32m: 9 linhas.

### 4.5 `sql/athena/analise/` (Athena, análises)

### `sql/athena/analise/10_flag_bots.sql`

- **Dialeto:** Athena (Trino)
- **Pergunta:** que utilizadores têm comportamento suspeito (regra A: ritmo sustentado fora do registo; regra B: registo extremo) ou de submissão em lote? Uma linha por utilizador, com classificação e justificação (nunca "bot confirmado"). (equivalente Athena de `sql/analise/10_flag_bots.sql`)

```sql
-- 10_flag_bots.sql (Athena) - equivalente a sql/analise/10_flag_bots.sql
--
-- *** A VALIDAR COM O LUÍS *** - substitui utilizadores_sinalizados (notebook, célula 112).
-- A explicação das regras (eventos, submissão em lote, regras A e B, sinais complementares)
-- está no cabeçalho da versão DuckDB.
--
-- COMO CORRER: o resultado tem uma linha por utilizador (200 948 no 32M), por isso NÃO é
-- devolvido ao cliente. Corre-se como CTAS em Parquet, e as perguntas fazem-se sobre a tabela:
--   CREATE TABLE flag_bots
--   WITH (format = 'PARQUET', external_location = 's3://<bucket-resultados>/ctas/flag_bots/')
--   AS <esta query>
-- Depois: 10_flag_bots_calibracao.sql (uma linha) e eventos.sql leem ${flag_bots} = flag_bots.
--
-- Fuso horário: from_unixtime("timestamp") devolve UTC; os intervalos e as janelas usam o
-- timestamp em segundos, sem conversão.
-- Diferenças para o DuckDB:
-- - MEDIAN e quantile_cont não existem: approx_percentile(CAST(x AS double), p). É uma
--   aproximação; a mediana dos intervalos (inteiros) e os quantis podem diferir ligeiramente,
--   o que só importa para quem está exatamente no limiar;
-- - frações com CAST(... AS double) (no Trino, 100.0 * x / y teria só 1 casa decimal);
-- - approx_percentile(CASE WHEN fase THEN x END, p) em vez de FILTER (os agregados ignoram
--   NULL; é a forma mais portável);
-- - "timestamp" entre aspas; date_format(from_unixtime(...)) em vez de strftime(epoch_ms(...)).
-- A CONFIRMAR NA AWS: a janela RANGE BETWEEN CURRENT ROW AND 599 FOLLOWING (frame RANGE com
-- deslocamento numérico) é suportada pelas versões recentes do Trino; se o Athena a recusar,
-- a alternativa é um self-join dos eventos com e2.ts BETWEEN e1.ts AND e1.ts + 599.
--
-- Parâmetros: ${ratings}
WITH lim AS (SELECT 86400 AS registo_s,
                    100   AS regra_b_min_eventos,
                    2     AS regra_b_max_mediana_s,
                    10    AS lote_min_avaliacoes),
     ev AS (SELECT r.userid, r."timestamp" AS ts, COUNT(*) AS k
            FROM ${ratings} AS r
            GROUP BY r.userid, r."timestamp"),
     fase AS (SELECT ev.userid, ev.ts, ev.k,
                     ev.ts - MIN(ev.ts) OVER (PARTITION BY ev.userid) < l.registo_s AS no_registo
              FROM ev CROSS JOIN lim AS l),
     ritmo AS (SELECT fase.*,
                      ts - LAG(ts) OVER (PARTITION BY userid, no_registo ORDER BY ts) AS intervalo,
                      COUNT(*) OVER (PARTITION BY userid, no_registo ORDER BY ts
                                     RANGE BETWEEN CURRENT ROW AND 599 FOLLOWING)  AS eventos_10min
               FROM fase),
     por_eventos AS (SELECT userid,
                            COUNT(*)                                          AS eventos,
                            MAX(k)                                            AS max_avaliacoes_mesmo_segundo,
                            100 * CAST(count_if(k >= 2) AS double) / COUNT(*) AS pct_eventos_lote,
                            count_if(no_registo)                              AS eventos_registo,
                            approx_percentile(CASE WHEN no_registo THEN CAST(intervalo AS double) END, 0.5) AS mediana_intervalo_registo_s,
                            MAX(eventos_10min) FILTER (WHERE no_registo)      AS max_eventos_10min_registo,
                            count_if(NOT no_registo)                          AS eventos_apos_registo,
                            approx_percentile(CASE WHEN NOT no_registo THEN CAST(intervalo AS double) END, 0.5) AS mediana_intervalo_apos_s,
                            MAX(eventos_10min) FILTER (WHERE NOT no_registo)  AS max_eventos_10min_apos,
                            MIN(ts)                                           AS primeiro_ts,
                            MAX(ts)                                           AS ultimo_ts
                     FROM ritmo
                     GROUP BY userid),
     notas AS (SELECT r.userid, COUNT(*) AS avaliacoes, stddev_samp(r.rating) AS desvio_notas
               FROM ${ratings} AS r GROUP BY r.userid),
     por_nota AS (SELECT r.userid, r.rating, COUNT(*) AS n FROM ${ratings} AS r GROUP BY r.userid, r.rating),
     modal AS (SELECT userid, MAX(n) AS n_nota_modal FROM por_nota GROUP BY userid),
     base AS (SELECT e.*, n.avaliacoes, n.desvio_notas,
                     100 * CAST(m.n_nota_modal AS double) / n.avaliacoes AS pct_nota_modal
              FROM por_eventos AS e
              JOIN notas AS n ON e.userid = n.userid
              JOIN modal AS m ON e.userid = m.userid),
     limiar_a AS (SELECT approx_percentile(CAST(max_eventos_10min_apos AS double), 0.999) AS limiar_regra_a   -- QUANTIL DA REGRA A
                  FROM base WHERE eventos_apos_registo > 0),
     limiares_c AS (SELECT approx_percentile(desvio_notas, 0.01)     AS limiar_desvio_baixo,
                           approx_percentile(pct_nota_modal, 0.99)   AS limiar_modal_alto,
                           approx_percentile(pct_eventos_lote, 0.99) AS limiar_lote_alto
                    FROM base),
     f AS (SELECT b.*, a.limiar_regra_a,
                  COALESCE(b.eventos_apos_registo > 0 AND b.max_eventos_10min_apos >= a.limiar_regra_a, false) AS regra_a,
                  COALESCE(b.eventos_registo >= l.regra_b_min_eventos
                           AND b.mediana_intervalo_registo_s <= l.regra_b_max_mediana_s, false)               AS regra_b,
                  b.max_avaliacoes_mesmo_segundo >= l.lote_min_avaliacoes                                     AS submissao_lote,
                  IF(b.desvio_notas <= c.limiar_desvio_baixo, 1, 0)
                    + IF(b.pct_nota_modal >= c.limiar_modal_alto, 1, 0)
                    + IF(b.pct_eventos_lote >= c.limiar_lote_alto, 1, 0)                                     AS sinais_complementares
           FROM base AS b CROSS JOIN limiar_a AS a CROSS JOIN limiares_c AS c CROSS JOIN lim AS l)
SELECT userid, avaliacoes, eventos,
       date_format(from_unixtime(primeiro_ts), '%Y-%m-%d') AS primeiro_dia,
       date_format(from_unixtime(ultimo_ts), '%Y-%m-%d')   AS ultimo_dia,
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
ORDER BY userid
```

**Output (emulação DuckDB; não corrido no Athena), small** (`results/small/analises/athena_emulado/10_flag_bots.csv`, 610 linhas):

```csv
userId,avaliacoes,eventos,primeiro_dia,ultimo_dia,eventos_registo,mediana_intervalo_registo_s,max_eventos_10min_registo,eventos_apos_registo,mediana_intervalo_apos_s,max_eventos_10min_apos,limiar_regra_a,max_avaliacoes_mesmo_segundo,pct_eventos_lote,desvio_notas,pct_nota_modal,regra_a,regra_b,submissao_lote,sinais_complementares,classificacao
1,232,119,2000-07-30,2000-08-08,118,20.0,26,1,,1,114.80099999999976,7,45.378151260504204,0.8000480467733436,53.44827586206897,false,false,false,0,sem sinais
2,29,29,2015-10-24,2015-10-24,29,9.5,29,0,,,114.80099999999976,1,0.0,0.8056145345791144,31.03448275862069,false,false,false,0,sem sinais
3,39,39,2011-05-27,2011-05-27,39,12.0,27,0,,,114.80099999999976,1,0.0,2.0906417019771424,51.282051282051285,false,false,false,0,sem sinais
4,216,160,1999-12-13,2001-12-05,39,28.5,16,121,38.5,22,114.80099999999976,4,26.25,1.3142038589753633,29.62962962962963,false,false,false,0,sem sinais
5,44,17,1996-11-08,1996-11-08,17,23.0,17,0,,,114.80099999999976,5,82.3529411764706,0.9904405665441197,38.63636363636363,false,false,false,0,sem sinais
```

**Output (emulação DuckDB; não corrido no Athena), 1m** (`results/1m/analises/athena_emulado/10_flag_bots.csv`, 6040 linhas):

```csv
userId,avaliacoes,eventos,primeiro_dia,ultimo_dia,eventos_registo,mediana_intervalo_registo_s,max_eventos_10min_registo,eventos_apos_registo,mediana_intervalo_apos_s,max_eventos_10min_apos,limiar_regra_a,max_avaliacoes_mesmo_segundo,pct_eventos_lote,desvio_notas,pct_nota_modal,regra_a,regra_b,submissao_lote,sinais_complementares,classificacao
1,53,34,2000-12-31,2001-01-06,28,36.0,16,6,39.0,6,40.0,5,35.294117647058826,0.6809666142721429,50.943396226415096,false,false,false,0,sem sinais
2,129,66,2000-12-31,2000-12-31,66,26.0,24,0,,,40.0,6,56.06060606060606,1.001512905945397,33.333333333333336,false,false,false,0,sem sinais
3,51,31,2000-12-31,2000-12-31,31,29.0,15,0,,,40.0,3,48.38709677419355,0.9849853188912879,43.13725490196079,false,false,false,0,sem sinais
4,21,7,2000-12-31,2000-12-31,7,35.5,7,0,,,40.0,5,71.42857142857143,1.077916862241593,47.61904761904762,false,false,false,0,sem sinais
5,198,83,2000-12-31,2000-12-31,83,35.0,22,0,,,40.0,5,71.08433734939759,1.132699316852714,30.80808080808081,false,false,false,0,sem sinais
```

**32M:** não corrido.

### `sql/athena/analise/10_flag_bots_calibracao.sql`

- **Dialeto:** Athena (Trino)
- **Pergunta:** como se distribui o máximo de eventos numa janela de 10 min, depois das primeiras 24 h, e quantos utilizadores ficariam sinalizados com o limiar no p99, no p99,5 e no p99,9? Inclui também os totais de cada regra e categoria, e a taxa de sinalizados. (equivalente Athena de `sql/analise/10_flag_bots_calibracao.sql`)

```sql
-- 10_flag_bots_calibracao.sql (Athena) - equivalente a sql/analise/10_flag_bots_calibracao.sql
--
-- *** A VALIDAR COM O LUÍS ***
-- Lê a tabela flag_bots criada por CTAS a partir de sql/athena/analise/10_flag_bots.sql
-- (${flag_bots} = flag_bots). Resultado agregado: uma linha.
-- Quantis com approx_percentile (aproximados; no DuckDB são exatos, quantile_cont).
-- Frações com CAST(... AS double). Não converte o timestamp (sem questões de fuso).
--
-- Parâmetros: ${flag_bots}
WITH a AS (SELECT CAST(max_eventos_10min_apos AS double) AS x
           FROM ${flag_bots} WHERE eventos_apos_registo > 0),
     q AS (SELECT COUNT(*)                     AS utilizadores_com_atividade_apos_registo,
                  approx_percentile(x, 0.5)    AS p50,
                  approx_percentile(x, 0.9)    AS p90,
                  approx_percentile(x, 0.95)   AS p95,
                  approx_percentile(x, 0.99)   AS p99,
                  approx_percentile(x, 0.995)  AS p99_5,
                  approx_percentile(x, 0.999)  AS p99_9,
                  MAX(x)                       AS maximo
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
                  100 * CAST(count_if(regra_a OR regra_b) AS double) / COUNT(*) AS pct_suspeitos
           FROM ${flag_bots})
SELECT s.*, t.* FROM s CROSS JOIN t
```

**Output (emulação DuckDB; não corrido no Athena), small** (`results/small/analises/athena_emulado/10_flag_bots_calibracao.csv`, 1 linhas):

```csv
utilizadores_com_atividade_apos_registo,p50,p90,p95,p99,p99_5,p99_9,maximo,sinalizados_a_p99,sinalizados_a_p99_5,sinalizados_a_p99_9,utilizadores,regra_a,regra_b,suspeitos,submissao_lote,so_submissao_lote,pct_suspeitos
248,18.0,52.30000000000001,61.64999999999998,90.83000000000001,100.58999999999992,114.80099999999976,119.0,3,2,1,610,1,1,2,13,13,0.32786885245901637
```

**Output (emulação DuckDB; não corrido no Athena), 1m** (`results/1m/analises/athena_emulado/10_flag_bots_calibracao.csv`, 1 linhas):

```csv
utilizadores_com_atividade_apos_registo,p50,p90,p95,p99,p99_5,p99_9,maximo,sinalizados_a_p99,sinalizados_a_p99_5,sinalizados_a_p99_9,utilizadores,regra_a,regra_b,suspeitos,submissao_lote,so_submissao_lote,pct_suspeitos
2239,14.0,26.0,29.0,35.0,38.0,40.0,45.0,25,13,6,6040,6,0,6,339,339,0.09933774834437085
```

**32M:** não corrido.

### `sql/athena/analise/anual.sql`

- **Dialeto:** Athena (Trino)
- **Pergunta:** como evolui, ano a ano, o volume de avaliações, a média e o n.º de utilizadores que avaliaram pelo menos um filme nesse ano? (equivalente Athena de `sql/analise/anual.sql`)

```sql
-- anual.sql (Athena) - equivalente a sql/analise/anual.sql
-- Origem: notebook do Luís, célula 108 ("novo-queries"), consultas_sql()["anual"].
--
-- Fuso horário: em ratings_part, year vem do nome das pastas (calculado em UTC no
-- prepare_cloud.py); nas tabelas sem partição, year = year(from_unixtime("timestamp")) e
-- from_unixtime devolve a data em UTC. O resultado não depende do fuso da sessão.
-- Diferenças para o DuckDB: GROUP BY pela coluna (o Trino não aceita aliases do SELECT
-- no GROUP BY); nomes de colunas em minúsculas.
-- Resultado agregado: uma linha por ano.
--
-- Parâmetros: ${ratings}
SELECT r.year AS ano,
       COUNT(*)                 AS num_ratings,
       AVG(r.rating)            AS media,
       COUNT(DISTINCT r.userid) AS utilizadores
FROM ${ratings} AS r
GROUP BY r.year
ORDER BY r.year
```

**Output (emulação DuckDB; não corrido no Athena), small** (`results/small/analises/athena_emulado/anual.csv`, 23 linhas):

```csv
ano,num_ratings,media,utilizadores
1996,6040,3.5359271523178806,97
1997,1916,3.7275574112734864,33
1998,507,3.4358974358974357,11
1999,2439,3.772447724477245,27
2000,10061,3.39250571513766,56
```

**Output (emulação DuckDB; não corrido no Athena), 1m** (`results/1m/analises/athena_emulado/anual.csv`, 4 linhas):

```csv
ano,num_ratings,media,utilizadores
2000,904757,3.5903916742285498,6034
2001,68058,3.5122542537247643,1070
2002,24046,3.458828911253431,565
2003,3348,3.486559139784946,178
```

**32M:** não corrido.

### `sql/athena/analise/distribuicao.sql`

- **Dialeto:** Athena (Trino)
- **Pergunta:** para cada valor de rating, quantos utilizadores o usam e que peso tem, em média, no histórico de cada utilizador? (equivalente Athena de `sql/analise/distribuicao.sql`)

```sql
-- distribuicao.sql (Athena) - equivalente a sql/analise/distribuicao.sql
-- Origem: notebook do Luís, célula 108 ("novo-queries"), consultas_sql()["distribuicao"].
--
-- Resultado agregado (no máximo 10 linhas, uma por valor). A tabela (utilizador, valor), que no
-- 32M teria ~1,5 M linhas, só existe como CTE e nunca é devolvida ao cliente.
-- Divisões: sempre com CAST(... AS double). No Trino, bigint / bigint é divisão inteira e
-- uma divisão com um literal decimal (100.0 * x / y) fica com a escala do literal (1 casa).
-- Não usa o timestamp, por isso não há questões de fuso horário.
--
-- Parâmetros: ${ratings}
WITH d AS (SELECT r.userid, r.rating, COUNT(*) AS n FROM ${ratings} AS r GROUP BY r.userid, r.rating),
     t AS (SELECT d.userid, SUM(d.n) AS total FROM d GROUP BY d.userid),
     g AS (SELECT COUNT(*) AS utilizadores, SUM(t.total) AS avaliacoes FROM t)
SELECT d.rating,
       COUNT(*)                                                    AS utilizadores_que_usam,
       100 * CAST(COUNT(*) AS double) / g.utilizadores             AS pct_utilizadores,
       SUM(d.n)                                                    AS num_ratings,
       100 * CAST(SUM(d.n) AS double) / g.avaliacoes               AS pct_ratings,
       SUM(CAST(d.n AS double) / t.total) / g.utilizadores         AS prop_media_utilizador
FROM d JOIN t ON d.userid = t.userid CROSS JOIN g
GROUP BY d.rating, g.utilizadores, g.avaliacoes
ORDER BY d.rating
```

**Output (emulação DuckDB; não corrido no Athena), small** (`results/small/analises/athena_emulado/distribuicao.csv`, 10 linhas):

```csv
rating,utilizadores_que_usam,pct_utilizadores,num_ratings,pct_ratings,prop_media_utilizador
0.5,179,29.34426229508197,1370,1.3586417549287952,0.014444472452032222
1.0,351,57.540983606557376,2811,2.787694870879448,0.028688493920859922
1.5,191,31.311475409836067,1791,1.776151374509104,0.011060421237979168
2.0,491,80.49180327868852,7551,7.488397001071046,0.06217243169658144
2.5,291,47.704918032786885,5550,5.503986671426872,0.030453110656720402
```

**Output (emulação DuckDB; não corrido no Athena), 1m** (`results/1m/analises/athena_emulado/distribuicao.csv`, 5 linhas):

```csv
rating,utilizadores_que_usam,pct_utilizadores,num_ratings,pct_ratings,prop_media_utilizador
1.0,4667,77.26821192052981,56174,5.616226208722377,0.049370311032317746
2.0,5642,93.41059602649007,107557,10.75345252842156,0.0919201037514402
3.0,6013,99.55298013245033,261197,26.11424212339621,0.23586293440461573
4.0,6034,99.90066225165563,348971,34.889808030121706,0.352327708807453
5.0,6014,99.56953642384106,226310,22.62627110933815,0.27051894200417337
```

**32M:** não corrido.

### `sql/athena/analise/eventos.sql`

- **Dialeto:** Athena (Trino)
- **Pergunta:** em que (filme, dia) houve muitas notas extremas no mesmo sentido, com a média do dia afastada do histórico anterior do filme? Quantos dos utilizadores desse dia são suspeitos? (equivalente Athena de `sql/analise/eventos.sql`)

```sql
-- eventos.sql (Athena) - equivalente a sql/analise/eventos.sql
-- Origem: notebook do Luís, célula 112 ("novo-advanced"): dias_filme, view "eventos" e participantes.
--
-- A tabela filme x dia (14,7 M linhas no 32M) só existe como CTE. Se for precisa para outras
-- análises, cria-se com CTAS em Parquet; nunca é devolvida ao cliente.
-- ${flag_bots} é a tabela flag_bots criada por CTAS a partir de 10_flag_bots.sql.
-- LIMIT (posicao <= 100) justificado: os 100 eventos com mais suspeitos, para inspeção; o total
-- vem na coluna total_eventos e no funil (filtros_eventos.sql).
-- Dia: "timestamp" / 86400 (divisão inteira no Trino = dia UTC); a data sai com
-- CAST(from_unixtime(dia * 86400) AS date), em UTC.
-- Frações com CAST(... AS double) (no Trino, x * 1.0 / y teria só 1 casa decimal).
-- Limites do capítulo 9 (P7), a decidir com o Luís.
--
-- Parâmetros: ${ratings}, ${movies}, ${flag_bots}
WITH lim AS (SELECT 5 AS min_anterior, 5 AS min_utilizadores, 2.0 AS nota_baixa, 4.0 AS nota_alta,
                    0.51 AS min_frac_extremas, 0.5 AS min_variacao),
     d AS (SELECT r.movieid, r."timestamp" / 86400 AS dia, COUNT(*) AS n,
                  COUNT(DISTINCT r.userid) AS utilizadores, SUM(r.rating) AS soma, AVG(r.rating) AS media,
                  CAST(count_if(r.rating <= l.nota_baixa) AS double) / COUNT(*) AS frac_baixas,
                  CAST(count_if(r.rating >= l.nota_alta)  AS double) / COUNT(*) AS frac_altas
           FROM ${ratings} AS r CROSS JOIN lim AS l
           GROUP BY r.movieid, r."timestamp" / 86400),
     h AS (SELECT d.*,
                  SUM(n)    OVER (PARTITION BY movieid ORDER BY dia ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - n    AS n_anterior,
                  SUM(soma) OVER (PARTITION BY movieid ORDER BY dia ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - soma AS soma_anterior
           FROM d),
     v AS (SELECT h.*, soma_anterior / NULLIF(n_anterior, 0) AS media_anterior,
                  media - soma_anterior / NULLIF(n_anterior, 0) AS variacao
           FROM h),
     ev AS (SELECT v.movieid, v.dia, v.utilizadores, v.n_anterior, v.media_anterior, v.media, v.variacao,
                   CASE WHEN v.frac_baixas >= l.min_frac_extremas AND v.variacao <= -l.min_variacao THEN 'Avaliações baixas'
                        WHEN v.frac_altas  >= l.min_frac_extremas AND v.variacao >=  l.min_variacao THEN 'Avaliações altas'
                   END AS tipo
            FROM v CROSS JOIN lim AS l
            WHERE v.n_anterior >= l.min_anterior AND v.utilizadores >= l.min_utilizadores),
     e AS (SELECT * FROM ev WHERE tipo IS NOT NULL),
     p AS (SELECT r.movieid, r."timestamp" / 86400 AS dia,
                  COUNT(DISTINCT r.userid)                                           AS participantes,
                  COUNT(DISTINCT CASE WHEN f.regra_a OR f.regra_b THEN r.userid END) AS suspeitos,
                  COUNT(DISTINCT CASE WHEN f.submissao_lote THEN r.userid END)       AS em_lote
           FROM ${ratings} AS r
           JOIN e ON r.movieid = e.movieid AND r."timestamp" / 86400 = e.dia
           LEFT JOIN ${flag_bots} AS f ON r.userid = f.userid
           GROUP BY r.movieid, r."timestamp" / 86400),
     x AS (SELECT e.*, p.participantes, p.suspeitos, p.em_lote,
                  100 * CAST(p.suspeitos AS double) / p.participantes AS pct_suspeitos,
                  ROW_NUMBER() OVER (ORDER BY p.suspeitos DESC, e.utilizadores DESC, e.movieid, e.dia) AS posicao,
                  COUNT(*) OVER () AS total_eventos
           FROM e JOIN p ON e.movieid = p.movieid AND e.dia = p.dia)
SELECT x.posicao, x.movieid, m.title, CAST(from_unixtime(x.dia * 86400) AS date) AS dia, x.tipo,
       x.utilizadores, x.n_anterior, x.media_anterior, x.media, x.variacao,
       x.suspeitos, x.em_lote, x.pct_suspeitos, x.total_eventos
FROM x JOIN ${movies} AS m ON x.movieid = m.movieid
WHERE x.posicao <= 100
ORDER BY x.posicao
```

**Output (emulação DuckDB; não corrido no Athena), small** (`results/small/analises/athena_emulado/eventos.csv`, 0 linhas):

```csv
posicao,movieId,title,dia,tipo,utilizadores,n_anterior,media_anterior,media,variacao,suspeitos,em_lote,pct_suspeitos,total_eventos
```

**Output (emulação DuckDB; não corrido no Athena), 1m** (`results/1m/analises/athena_emulado/eventos.csv`, 100 linhas):

```csv
posicao,movieId,title,dia,tipo,utilizadores,n_anterior,media_anterior,media,variacao,suspeitos,em_lote,pct_suspeitos,total_eventos
1,2919,Year of Living Dangerously (1982),2000-11-20,Avaliações altas,21,260,3.896153846153846,4.476190476190476,0.5800366300366302,1,4,4.761904761904762,3884
2,1097,E.T. the Extra-Terrestrial (1982),2000-12-02,Avaliações altas,18,1901,3.9495002630194636,4.5,0.5504997369805364,1,2,5.555555555555555,3884
3,1721,Titanic (1997),2000-12-02,Avaliações altas,13,1243,3.582461786001609,4.3076923076923075,0.7252305216906985,1,1,7.6923076923076925,3884
4,2906,Random Hearts (1999),2000-11-20,Avaliações baixas,13,146,2.3972602739726026,1.6923076923076923,-0.7049525816649103,1,3,7.6923076923076925,3884
5,1282,Fantasia (1940),2000-12-02,Avaliações altas,11,706,3.9390934844192635,4.454545454545454,0.5154519701261906,1,2,9.090909090909092,3884
```

**32M:** não corrido.

### `sql/athena/analise/evolucao_filmes.sql`

- **Dialeto:** Athena (Trino)
- **Pergunta:** comparando os 5 anos anteriores com os 5 anos mais recentes, que filmes (com pelo menos 10 avaliações em cada período) mudaram mais de média? (equivalente Athena de `sql/analise/evolucao_filmes.sql`)

```sql
-- evolucao_filmes.sql (Athena) - equivalente a sql/analise/evolucao_filmes.sql
-- Origem: notebook do Luís, célula 112 ("novo-advanced"), SQL_AVANCADO["evolucao_filmes"].
--
-- Opção usada: só anos completos (o último ano só conta se o último rating for de 31/12;
-- senão o fim passa para o ano anterior). As colunas periodo_anterior, periodo_recente e
-- criterio indicam os anos usados e o ano excluído.
-- Fuso horário: from_unixtime devolve UTC; year vem das pastas de ratings_part ou de
-- year(from_unixtime("timestamp")). O WHERE nos 10 anos permite partition pruning em ratings_part.
-- Tamanho do resultado: uma linha por filme com >= 10 avaliações em cada período (366 no
-- small; no 32M fica limitado ao n.º de filmes, dezenas de milhares no máximo, poucos MB).
-- É um resultado agregado (por filme) e não leva LIMIT, porque a análise usa os dois
-- extremos e a distribuição completa da variação.
--
-- Parâmetros: ${ratings}, ${movies}
WITH limites AS (SELECT MAX(r.year) AS ano_max, MAX(r."timestamp") AS ts_max FROM ${ratings} AS r),
     fim AS (SELECT CASE WHEN month(from_unixtime(ts_max)) = 12 AND day(from_unixtime(ts_max)) = 31
                         THEN ano_max ELSE ano_max - 1 END AS ano,
                    ano_max,
                    date_format(from_unixtime(ts_max), '%Y-%m-%d') AS ultimo_dia
             FROM limites),
     s AS (SELECT r.movieid,
                  COUNT(*)      FILTER (WHERE r.year BETWEEN f.ano - 9 AND f.ano - 5) AS n_anterior,
                  COUNT(*)      FILTER (WHERE r.year BETWEEN f.ano - 4 AND f.ano)     AS n_recente,
                  AVG(r.rating) FILTER (WHERE r.year BETWEEN f.ano - 9 AND f.ano - 5) AS media_anterior,
                  AVG(r.rating) FILTER (WHERE r.year BETWEEN f.ano - 4 AND f.ano)     AS media_recente
           FROM ${ratings} AS r CROSS JOIN fim AS f
           WHERE r.year BETWEEN f.ano - 9 AND f.ano
           GROUP BY r.movieid),
     e AS (SELECT s.*, media_recente - media_anterior AS variacao,
                  RANK() OVER (ORDER BY media_anterior DESC) AS posicao_anterior,
                  RANK() OVER (ORDER BY media_recente DESC)  AS posicao_recente
           FROM s
           WHERE n_anterior >= 10 AND n_recente >= 10)
SELECT e.movieid, m.title, e.n_anterior, e.n_recente, e.media_anterior, e.media_recente,
       e.variacao, e.posicao_anterior, e.posicao_recente,
       CAST(f.ano - 9 AS varchar) || '–' || CAST(f.ano - 5 AS varchar) AS periodo_anterior,
       CAST(f.ano - 4 AS varchar) || '–' || CAST(f.ano AS varchar)     AS periodo_recente,
       CASE WHEN f.ano < f.ano_max
            THEN 'só anos completos: exclui ' || CAST(f.ano_max AS varchar) || ' (parcial, último rating ' || f.ultimo_dia || ')'
            ELSE 'só anos completos: o último ano está completo' END AS criterio
FROM e CROSS JOIN fim AS f
JOIN ${movies} AS m ON e.movieid = m.movieid
ORDER BY e.variacao DESC, e.movieid
```

**Output (emulação DuckDB; não corrido no Athena), small** (`results/small/analises/athena_emulado/evolucao_filmes.csv`, 366 linhas):

```csv
movieId,title,n_anterior,n_recente,media_anterior,media_recente,variacao,posicao_anterior,posicao_recente,periodo_anterior,periodo_recente,criterio
1676,Starship Troopers (1997),11,16,2.9545454545454546,3.84375,0.8892045454545454,348,146,2008–2012,2013–2017,"só anos completos: exclui 2018 (parcial, último rating 2018-09-24)"
2916,Total Recall (1990),14,14,3.25,4.071428571428571,0.8214285714285712,321,50,2008–2012,2013–2017,"só anos completos: exclui 2018 (parcial, último rating 2018-09-24)"
344,Ace Ventura: Pet Detective (1994),28,21,2.625,3.4285714285714284,0.8035714285714284,365,291,2008–2012,2013–2017,"só anos completos: exclui 2018 (parcial, último rating 2018-09-24)"
57368,Cloverfield (2008),13,14,2.9615384615384617,3.7142857142857144,0.7527472527472527,346,195,2008–2012,2013–2017,"só anos completos: exclui 2018 (parcial, último rating 2018-09-24)"
2617,"Mummy, The (1999)",17,14,2.7941176470588234,3.5357142857142856,0.7415966386554622,361,259,2008–2012,2013–2017,"só anos completos: exclui 2018 (parcial, último rating 2018-09-24)"
```

**Output (emulação DuckDB; não corrido no Athena), 1m** (`results/1m/analises/athena_emulado/evolucao_filmes.csv`, 0 linhas):

```csv
movieId,title,n_anterior,n_recente,media_anterior,media_recente,variacao,posicao_anterior,posicao_recente,periodo_anterior,periodo_recente,criterio
```

**32M:** não corrido.

### `sql/athena/analise/filmes_ano.sql`

- **Dialeto:** Athena (Trino)
- **Pergunta:** como evoluiu, ano a ano, a média do filme com a maior subida (variação >= 0,5) e do filme com a maior descida (variação <= -0,5) de evolucao_filmes? (equivalente Athena de `sql/analise/filmes_ano.sql`)

```sql
-- filmes_ano.sql (Athena) - equivalente a sql/analise/filmes_ano.sql
-- Origem: notebook do Luís, célula 112 ("novo-advanced"), consulta "filmes_ano".
--
-- Mesmas CTEs de sql/athena/analise/evolucao_filmes.sql (só anos completos); os dois filmes
-- são escolhidos com ROW_NUMBER() (em vez de UNION de subqueries com LIMIT).
-- Fuso horário: from_unixtime devolve UTC.
-- Resultado agregado: uma linha por (filme, ano), para 2 filmes (dezenas de linhas).
--
-- Parâmetros: ${ratings}, ${movies}
WITH limites AS (SELECT MAX(r.year) AS ano_max, MAX(r."timestamp") AS ts_max FROM ${ratings} AS r),
     fim AS (SELECT CASE WHEN month(from_unixtime(ts_max)) = 12 AND day(from_unixtime(ts_max)) = 31
                         THEN ano_max ELSE ano_max - 1 END AS ano,
                    ano_max,
                    date_format(from_unixtime(ts_max), '%Y-%m-%d') AS ultimo_dia
             FROM limites),
     s AS (SELECT r.movieid,
                  COUNT(*)      FILTER (WHERE r.year BETWEEN f.ano - 9 AND f.ano - 5) AS n_anterior,
                  COUNT(*)      FILTER (WHERE r.year BETWEEN f.ano - 4 AND f.ano)     AS n_recente,
                  AVG(r.rating) FILTER (WHERE r.year BETWEEN f.ano - 9 AND f.ano - 5) AS media_anterior,
                  AVG(r.rating) FILTER (WHERE r.year BETWEEN f.ano - 4 AND f.ano)     AS media_recente
           FROM ${ratings} AS r CROSS JOIN fim AS f
           WHERE r.year BETWEEN f.ano - 9 AND f.ano
           GROUP BY r.movieid),
     e AS (SELECT s.*, media_recente - media_anterior AS variacao,
                  RANK() OVER (ORDER BY media_anterior DESC) AS posicao_anterior,
                  RANK() OVER (ORDER BY media_recente DESC)  AS posicao_recente
           FROM s
           WHERE n_anterior >= 10 AND n_recente >= 10),
     sobe AS (SELECT movieid, ROW_NUMBER() OVER (ORDER BY variacao DESC, movieid) AS k FROM e WHERE variacao >= 0.5),
     desce AS (SELECT movieid, ROW_NUMBER() OVER (ORDER BY variacao, movieid) AS k FROM e WHERE variacao <= -0.5),
     escolhidos AS (SELECT movieid, 'Maior subida' AS tipo FROM sobe WHERE k = 1
                    UNION ALL
                    SELECT movieid, 'Maior descida' AS tipo FROM desce WHERE k = 1)
SELECT r.movieid, m.title, x.tipo, r.year AS ano, COUNT(*) AS avaliacoes, AVG(r.rating) AS media
FROM ${ratings} AS r
JOIN escolhidos AS x ON r.movieid = x.movieid
JOIN ${movies} AS m ON r.movieid = m.movieid
GROUP BY r.movieid, m.title, x.tipo, r.year
ORDER BY r.movieid, r.year
```

**Output (emulação DuckDB; não corrido no Athena), small** (`results/small/analises/athena_emulado/filmes_ano.csv`, 39 linhas):

```csv
movieId,title,tipo,ano,avaliacoes,media
1380,Grease (1978),Maior descida,1997,2,3.5
1380,Grease (1978),Maior descida,1998,1,4.0
1380,Grease (1978),Maior descida,1999,2,5.0
1380,Grease (1978),Maior descida,2000,7,3.142857142857143
1380,Grease (1978),Maior descida,2001,2,3.5
```

**Output (emulação DuckDB; não corrido no Athena), 1m** (`results/1m/analises/athena_emulado/filmes_ano.csv`, 0 linhas):

```csv
movieId,title,tipo,ano,avaliacoes,media
```

**32M:** não corrido.

### `sql/athena/analise/filtros_eventos.sql`

- **Dialeto:** Athena (Trino)
- **Pergunta:** quantos pares (filme, dia) passam cada filtro, por ordem: histórico anterior -> n.º de utilizadores no dia -> proporção de notas extremas -> variação da média face ao histórico no mesmo sentido? (equivalente Athena de `sql/analise/filtros_eventos.sql`)

```sql
-- filtros_eventos.sql (Athena) - equivalente a sql/analise/filtros_eventos.sql
-- Origem: notebook do Luís, célula 112 ("novo-advanced"): dias_filme, view "eventos" e "filtros".
--
-- A tabela filme x dia (14,7 M linhas no 32M) só existe como CTE: o resultado devolvido é
-- uma linha. Se for precisa para outras análises, cria-se com CTAS em Parquet
-- (CREATE TABLE dias_filme WITH (format = 'PARQUET') AS SELECT ... das CTEs d/h/v),
-- nunca como resultado devolvido ao cliente.
-- Dia: "timestamp" / 86400 (no Trino, bigint / bigint é divisão inteira = dia UTC); não há
-- conversão de fuso.
-- Limites do capítulo 9 do notebook (P7), na CTE lim, a decidir com o Luís.
-- Frações com CAST(... AS double): no Trino, count_if(...) * 1.0 / COUNT(*) ficaria com a
-- escala do literal 1.0 (1 casa decimal) e 0.51 seria comparado com 0.5.
--
-- Parâmetros: ${ratings}
WITH lim AS (SELECT 5 AS min_anterior, 5 AS min_utilizadores, 2.0 AS nota_baixa, 4.0 AS nota_alta,
                    0.51 AS min_frac_extremas, 0.5 AS min_variacao),
     d AS (SELECT r.movieid, r."timestamp" / 86400 AS dia, COUNT(*) AS n,
                  COUNT(DISTINCT r.userid) AS utilizadores, SUM(r.rating) AS soma, AVG(r.rating) AS media,
                  CAST(count_if(r.rating <= l.nota_baixa) AS double) / COUNT(*) AS frac_baixas,
                  CAST(count_if(r.rating >= l.nota_alta)  AS double) / COUNT(*) AS frac_altas
           FROM ${ratings} AS r CROSS JOIN lim AS l
           GROUP BY r.movieid, r."timestamp" / 86400),
     h AS (SELECT d.*,
                  SUM(n)    OVER (PARTITION BY movieid ORDER BY dia ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - n    AS n_anterior,
                  SUM(soma) OVER (PARTITION BY movieid ORDER BY dia ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - soma AS soma_anterior
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
FROM v CROSS JOIN lim AS l
GROUP BY l.min_anterior, l.min_utilizadores, l.nota_baixa, l.nota_alta, l.min_frac_extremas, l.min_variacao
```

**Output (emulação DuckDB; não corrido no Athena), small** (`results/small/analises/athena_emulado/filtros_eventos.csv`, 1 linhas):

```csv
todos_filme_dia,com_historico,com_utilizadores,com_extremos,eventos,min_anterior,min_utilizadores,nota_baixa,nota_alta,min_frac_extremas,min_variacao
99538,70858,0,0,0,5,5,2.0,4.0,0.51,0.5
```

**Output (emulação DuckDB; não corrido no Athena), 1m** (`results/1m/analises/athena_emulado/filtros_eventos.csv`, 1 linhas):

```csv
todos_filme_dia,com_historico,com_utilizadores,com_extremos,eventos,min_anterior,min_utilizadores,nota_baixa,nota_alta,min_frac_extremas,min_variacao
407251,393200,43440,30551,3884,5,5,2.0,4.0,0.51,0.5
```

**32M:** não corrido.

### `sql/athena/analise/grupos_atividade.sql`

- **Dialeto:** Athena (Trino)
- **Pergunta:** os utilizadores mais ativos (no total do seu histórico) dão notas diferentes dos menos ativos? Média, em cada ano, das médias dos utilizadores de cada faixa. (equivalente Athena de `sql/analise/grupos_atividade.sql`)

```sql
-- grupos_atividade.sql (Athena) - equivalente a sql/analise/grupos_atividade.sql
-- Origem: notebook do Luís, célula 109 ("novo-analytics"), consultas_complementares()["grupos_atividade"].
--
-- Fuso horário: year vem das pastas de ratings_part ou de year(from_unixtime("timestamp")),
-- e from_unixtime devolve UTC.
-- Faixas fixas a partir de 20 (mínimo do MovieLens): 20–49, 50–99, 100–249, 250–999, 1000+.
-- Sem ANY_VALUE (join depois de agregar); GROUP BY com as colunas, sem aliases.
-- Resultado agregado: no máximo 5 linhas por ano.
--
-- Parâmetros: ${ratings}
WITH totais AS (SELECT r.userid, COUNT(*) AS total FROM ${ratings} AS r GROUP BY r.userid),
     u AS (SELECT r.userid, r.year AS ano, AVG(r.rating) AS media_utilizador, COUNT(*) AS n
           FROM ${ratings} AS r
           GROUP BY r.userid, r.year),
     g AS (SELECT u.ano, u.media_utilizador, u.n,
                  CASE WHEN t.total < 50 THEN 20 WHEN t.total < 100 THEN 50 WHEN t.total < 250 THEN 100
                       WHEN t.total < 1000 THEN 250 ELSE 1000 END AS faixa_min
           FROM u JOIN totais AS t ON u.userid = t.userid)
SELECT ano,
       faixa_min,
       CASE faixa_min WHEN 20 THEN '20–49' WHEN 50 THEN '50–99' WHEN 100 THEN '100–249'
                      WHEN 250 THEN '250–999' ELSE '1000 ou mais' END AS grupo,
       AVG(media_utilizador) AS media,
       COUNT(*)              AS utilizadores,
       SUM(n)                AS avaliacoes
FROM g
GROUP BY ano, faixa_min
ORDER BY ano, faixa_min
```

**Output (emulação DuckDB; não corrido no Athena), small** (`results/small/analises/athena_emulado/grupos_atividade.csv`, 108 linhas):

```csv
ano,faixa_min,grupo,media,utilizadores,avaliacoes
1996,20,20–49,3.6632748220549933,45,1471
1996,50,50–99,3.571784559639957,34,2239
1996,100,100–249,3.429990940873896,17,2016
1996,250,250–999,3.4936305732484074,1,314
1997,20,20–49,3.6484258969121552,18,574
```

**Output (emulação DuckDB; não corrido no Athena), 1m** (`results/1m/analises/athena_emulado/grupos_atividade.csv`, 20 linhas):

```csv
ano,faixa_min,grupo,media,utilizadores,avaliacoes
2000,20,20–49,3.771832504045591,1742,55570
2000,50,50–99,3.7738989609173803,1352,91982
2000,100,100–249,3.7118898780347798,1717,252550
2000,250,250–999,3.54734214380573,1182,459585
2000,1000,1000 ou mais,3.3608922223688915,41,45070
```

**32M:** não corrido.

### `sql/athena/analise/integridade.sql`

- **Dialeto:** Athena (Trino)
- **Pergunta:** movies tem ids repetidos? Há avaliações de filmes que não existem em movies? O 05_analises.py falha se ids_filmes_repetidos ou ratings_sem_filme forem diferentes de 0. (equivalente Athena de `sql/analise/integridade.sql`)

```sql
-- integridade.sql (Athena) - equivalente a sql/analise/integridade.sql
-- Origem: notebook do Luís, célula 109 ("novo-analytics"), consultas_complementares()["integridade"].
--
-- NOT EXISTS (portável) em vez de ANTI JOIN; colunas qualificadas.
-- Não usa o timestamp, por isso não há questões de fuso horário.
-- Resultado agregado: uma linha.
--
-- Parâmetros: ${ratings}, ${movies}
SELECT (SELECT COUNT(*) - COUNT(DISTINCT m.movieid) FROM ${movies} AS m)          AS ids_filmes_repetidos,
       (SELECT COUNT(*) FROM ${ratings} AS r
         WHERE NOT EXISTS (SELECT 1 FROM ${movies} AS m WHERE m.movieid = r.movieid)) AS ratings_sem_filme,
       (SELECT COUNT(DISTINCT r.movieid) FROM ${ratings} AS r
         WHERE NOT EXISTS (SELECT 1 FROM ${movies} AS m WHERE m.movieid = r.movieid)) AS filmes_sem_metadados,
       (SELECT COUNT(*) FROM ${movies} AS m WHERE m.title IS NULL OR m.genres IS NULL) AS filmes_com_nulos
```

**Output (emulação DuckDB; não corrido no Athena), small** (`results/small/analises/athena_emulado/integridade.csv`, 1 linhas):

```csv
ids_filmes_repetidos,ratings_sem_filme,filmes_sem_metadados,filmes_com_nulos
0,0,0,0
```

**Output (emulação DuckDB; não corrido no Athena), 1m** (`results/1m/analises/athena_emulado/integridade.csv`, 1 linhas):

```csv
ids_filmes_repetidos,ratings_sem_filme,filmes_sem_metadados,filmes_com_nulos
0,0,0,0
```

**32M:** não corrido.

### `sql/athena/analise/mensal.sql`

- **Dialeto:** Athena (Trino)
- **Pergunta:** como se distribuem as avaliações ao longo dos meses (picos, lacunas)? (equivalente Athena de `sql/analise/mensal.sql`)

```sql
-- mensal.sql (Athena) - equivalente a sql/analise/mensal.sql
-- Origem: notebook do Luís, célula 109 ("novo-analytics"), consultas_complementares()["mensal"].
--
-- Fuso horário: from_unixtime("timestamp") devolve o instante em UTC (timestamp sem fuso da
-- sessão), por isso o mês não depende de onde a query corre.
-- date_format usa os códigos do MySQL; '%Y-%m' é igual ao do DuckDB.
-- Resultado agregado: uma linha por mês (267 no small; ~340 no 32M).
--
-- Parâmetros: ${ratings}
SELECT date_format(from_unixtime(r."timestamp"), '%Y-%m') AS mes,
       COUNT(*)      AS num_ratings,
       AVG(r.rating) AS media
FROM ${ratings} AS r
GROUP BY 1
ORDER BY 1
```

**Output (emulação DuckDB; não corrido no Athena), small** (`results/small/analises/athena_emulado/mensal.csv`, 267 linhas):

```csv
mes,num_ratings,media
1996-03,58,3.9827586206896552
1996-04,165,3.7393939393939393
1996-05,832,3.514423076923077
1996-06,883,3.5402038505096263
1996-07,489,3.6952965235173822
```

**Output (emulação DuckDB; não corrido no Athena), 1m** (`results/1m/analises/athena_emulado/mensal.csv`, 35 linhas):

```csv
mes,num_ratings,media
2000-04,11396,3.5533520533520533
2000-05,67437,3.6134466242567136
2000-06,54486,3.6339059574936683
2000-07,90334,3.630072840790843
2000-08,182109,3.572173807994113
```

**32M:** não corrido.

### `sql/athena/analise/perfis_ativos.sql`

- **Dialeto:** Athena (Trino)
- **Pergunta:** entre os utilizadores que avaliaram em cada ano (e com pelo menos 2 avaliações acumuladas até esse ano), quantos usaram até aí só estrelas inteiras, só valores não inteiros (x,5) ou os dois? (equivalente Athena de `sql/analise/perfis_ativos.sql`)

```sql
-- perfis_ativos.sql (Athena) - equivalente a sql/analise/perfis_ativos.sql
-- Origem: notebook do Luís, célula 109 ("novo-analytics"), consultas_complementares()["perfis_ativos"].
--
-- Fuso horário: year vem das pastas de ratings_part ou de year(from_unixtime("timestamp")),
-- e from_unixtime devolve UTC.
-- Diferenças para o original: count_if em vez de SUM((cond)::BIGINT); janela por extenso
-- (sem a cláusula WINDOW); GROUP BY 1, 2 (o Trino não aceita aliases no GROUP BY).
-- Resultado agregado: no máximo 3 linhas por ano.
--
-- Parâmetros: ${ratings}
WITH y AS (SELECT r.userid, r.year AS ano, COUNT(*) AS n,
                  count_if(r.rating = floor(r.rating))  AS inteiros,
                  count_if(r.rating <> floor(r.rating)) AS nao_inteiros
           FROM ${ratings} AS r
           GROUP BY r.userid, r.year),
     c AS (SELECT ano,
                  SUM(n)            OVER (PARTITION BY userid ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS total,
                  SUM(inteiros)     OVER (PARTITION BY userid ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS i,
                  SUM(nao_inteiros) OVER (PARTITION BY userid ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ni
           FROM y)
SELECT ano,
       CASE WHEN ni = 0 THEN 'Só inteiros' WHEN i = 0 THEN 'Só não inteiros' ELSE 'Misto' END AS perfil,
       COUNT(*) AS utilizadores
FROM c
WHERE total >= 2
GROUP BY 1, 2
ORDER BY 1, 2
```

**Output (emulação DuckDB; não corrido no Athena), small** (`results/small/analises/athena_emulado/perfis_ativos.csv`, 28 linhas):

```csv
ano,perfil,utilizadores
1996,Só inteiros,97
1997,Só inteiros,33
1998,Só inteiros,11
1999,Só inteiros,27
2000,Só inteiros,56
```

**Output (emulação DuckDB; não corrido no Athena), 1m** (`results/1m/analises/athena_emulado/perfis_ativos.csv`, 4 linhas):

```csv
ano,perfil,utilizadores
2000,Só inteiros,6034
2001,Só inteiros,1070
2002,Só inteiros,565
2003,Só inteiros,178
```

**32M:** não corrido.

### `sql/athena/analise/perfis_cumulativos.sql`

- **Dialeto:** Athena (Trino)
- **Pergunta:** como perfis_ativos, mas cada utilizador conta em todos os anos desde que entrou (mesmo nos anos sem atividade), com o histórico acumulado até esse ano. (equivalente Athena de `sql/analise/perfis_cumulativos.sql`)

```sql
-- perfis_cumulativos.sql (Athena) - equivalente a sql/analise/perfis_cumulativos.sql
-- Origem: notebook do Luís, célula 109 ("novo-analytics"), consultas_complementares()["perfis_cumulativos"].
--
-- Fuso horário: year vem das pastas de ratings_part ou de year(from_unixtime("timestamp")),
-- e from_unixtime devolve UTC.
-- Diferenças: UNNEST(sequence(a, b)) em vez de unnest(range(a, b + 1)); count_if; janela por
-- extenso; GROUP BY 1, 2.
-- A grelha utilizadores x anos (5,8 M linhas no 32M) fica dentro da query; o resultado
-- devolvido é agregado (no máximo 3 linhas por ano).
--
-- Parâmetros: ${ratings}
WITH limites AS (SELECT MIN(r.year) AS a, MAX(r.year) AS b FROM ${ratings} AS r),
     anos AS (SELECT t.ano FROM limites CROSS JOIN UNNEST(sequence(limites.a, limites.b)) AS t(ano)),
     y AS (SELECT r.userid, r.year AS ano,
                  count_if(r.rating = floor(r.rating))  AS i,
                  count_if(r.rating <> floor(r.rating)) AS ni
           FROM ${ratings} AS r
           GROUP BY r.userid, r.year),
     grelha AS (SELECT u.userid, a.ano, COALESCE(y.i, 0) AS i, COALESCE(y.ni, 0) AS ni
                FROM (SELECT DISTINCT r.userid FROM ${ratings} AS r) AS u
                CROSS JOIN anos AS a
                LEFT JOIN y ON u.userid = y.userid AND a.ano = y.ano),
     c AS (SELECT ano,
                  SUM(i)  OVER (PARTITION BY userid ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS i,
                  SUM(ni) OVER (PARTITION BY userid ORDER BY ano ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ni
           FROM grelha)
SELECT ano,
       CASE WHEN ni = 0 THEN 'Só inteiros' WHEN i = 0 THEN 'Só não inteiros' ELSE 'Misto' END AS perfil,
       COUNT(*) AS utilizadores
FROM c
WHERE i + ni >= 2
GROUP BY 1, 2
ORDER BY 1, 2
```

**Output (emulação DuckDB; não corrido no Athena), small** (`results/small/analises/athena_emulado/perfis_cumulativos.csv`, 39 linhas):

```csv
ano,perfil,utilizadores
1996,Só inteiros,97
1997,Só inteiros,124
1998,Só inteiros,133
1999,Só inteiros,159
2000,Só inteiros,207
```

**Output (emulação DuckDB; não corrido no Athena), 1m** (`results/1m/analises/athena_emulado/perfis_cumulativos.csv`, 4 linhas):

```csv
ano,perfil,utilizadores
2000,Só inteiros,6034
2001,Só inteiros,6038
2002,Só inteiros,6040
2003,Só inteiros,6040
```

**32M:** não corrido.

### `sql/athena/analise/ponderado.sql`

- **Dialeto:** Athena (Trino)
- **Pergunta:** que filmes têm a melhor média quando se "puxa" a média dos filmes com poucas avaliações para a média global? weighted = v/(v+m)*R + m/(v+m)*C, com m = 100 avaliações, R = média do filme, v = n.º de avaliações do filme e C = média global. (equivalente Athena de `sql/analise/ponderado.sql`)

```sql
-- ponderado.sql (Athena) - equivalente a sql/analise/ponderado.sql
-- Origem: notebook do Luís, célula 108 ("novo-queries"), consultas_sql()["ponderado"].
--
-- Diferenças para o DuckDB:
-- - CAST(... AS double) nas duas frações: no Athena (Trino), bigint / bigint é divisão
--   inteira e daria 0 sem erro (era o problema da versão da célula 90), e 100.0 / bigint
--   seria uma divisão decimal arredondada à escala do literal (1 casa);
-- - JOIN ... ON com nomes qualificados; os nomes de colunas saem em minúsculas.
-- LIMIT 10 justificado: é um top 10 (a pergunta pede só os 10 primeiros).
-- Não usa o timestamp, por isso não há questões de fuso horário.
--
-- Parâmetros: ${ratings}, ${movies} (substituídos como em scripts/athena_benchmark.py)
WITH s AS (SELECT r.movieid, AVG(r.rating) AS media_filme, COUNT(*) AS v
           FROM ${ratings} AS r GROUP BY r.movieid),
     p AS (SELECT AVG(r.rating) AS media_global FROM ${ratings} AS r)
SELECT s.movieid, m.title, s.media_filme AS avg_rating, s.v AS num_ratings,
       CAST(s.v AS double) / (s.v + 100) * s.media_filme
         + CAST(100 AS double) / (s.v + 100) * p.media_global AS weighted,
       p.media_global
FROM s CROSS JOIN p
JOIN ${movies} AS m ON s.movieid = m.movieid
ORDER BY weighted DESC, s.movieid
LIMIT 10
```

**Output (emulação DuckDB; não corrido no Athena), small** (`results/small/analises/athena_emulado/ponderado.csv`, 10 linhas):

```csv
movieId,title,avg_rating,num_ratings,weighted,media_global
318,"Shawshank Redemption, The (1994)",4.429022082018927,317,4.206608389356586,3.501556983616962
2959,Fight Club (1999),4.272935779816514,218,4.030363831326088,3.501556983616962
296,Pulp Fiction (1994),4.197068403908795,307,4.026181077055765,3.501556983616962
260,Star Wars: Episode IV - A New Hope (1977),4.231075697211155,251,4.02323560786808,3.501556983616962
858,"Godfather, The (1972)",4.2890625,192,4.019368830005808,3.501556983616962
```

**Output (emulação DuckDB; não corrido no Athena), 1m** (`results/1m/analises/athena_emulado/ponderado.csv`, 10 linhas):

```csv
movieId,title,avg_rating,num_ratings,weighted,media_global
318,"Shawshank Redemption, The (1994)",4.554557700942973,2227,4.512744497336886,3.581564453029317
858,"Godfather, The (1972)",4.524966261808367,2223,4.484354905425283,3.581564453029317
527,Schindler's List (1993),4.510416666666667,2304,4.471778887397226,3.581564453029317
50,"Usual Suspects, The (1995)",4.517106001121705,1783,4.467422435105114,3.581564453029317
1198,Raiders of the Lost Ark (1981),4.477724741447892,2514,4.44344163936608,3.581564453029317
```

**32M:** não corrido.

### `sql/athena/analise/qualidade.sql`

- **Dialeto:** Athena (Trino)
- **Pergunta:** as avaliações têm nulos, valores fora da escala (0,5 a 5 em meios pontos) ou o mesmo utilizador a avaliar o mesmo filme mais de uma vez? O 05_analises.py falha se linhas_com_nulos ou fora_dominio_comum forem diferentes de 0 (as mesmas asserções do notebook) e compara linhas/utilizadores/filmes com o 04_eda.py. (equivalente Athena de `sql/analise/qualidade.sql`)

```sql
-- qualidade.sql (Athena) - equivalente a sql/analise/qualidade.sql
-- Origem: notebook do Luís, célula 108 ("novo-queries"), consultas_sql()["qualidade"].
--
-- Diferenças para o DuckDB:
-- - COUNT(DISTINCT (a, b)) não existe no Trino: os pares distintos contam-se numa subquery
--   (lê ratings duas vezes; no 32M em Parquet são ~320 MB, ~0,002 USD);
-- - count_if(cond) em vez de COUNT(*) FILTER (WHERE cond) (os dois funcionam no Trino);
-- - "timestamp" entre aspas (palavra reservada).
-- Não converte o timestamp, por isso não há questões de fuso horário.
-- Resultado agregado: uma linha.
--
-- Parâmetros: ${ratings}
SELECT COUNT(*)                 AS linhas,
       COUNT(DISTINCT r.userid) AS utilizadores,
       COUNT(DISTINCT r.movieid) AS filmes,
       COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT d.userid, d.movieid FROM ${ratings} AS d) AS pares)
                                AS pares_repetidos,
       count_if(r.userid IS NULL OR r.movieid IS NULL OR r.rating IS NULL OR r."timestamp" IS NULL)
                                AS linhas_com_nulos,
       count_if(r.rating < 0.5 OR r.rating > 5 OR r.rating * 2 <> floor(r.rating * 2))
                                AS fora_dominio_comum,
       count_if(r.rating <> floor(r.rating)) AS nao_inteiros,
       count_if(r.rating < 1)   AS inferior_a_um
FROM ${ratings} AS r
```

**Output (emulação DuckDB; não corrido no Athena), small** (`results/small/analises/athena_emulado/qualidade.csv`, 1 linhas):

```csv
linhas,utilizadores,filmes,pares_repetidos,linhas_com_nulos,fora_dominio_comum,nao_inteiros,inferior_a_um
100836,610,9724,0,0,0,30398,1370
```

**Output (emulação DuckDB; não corrido no Athena), 1m** (`results/1m/analises/athena_emulado/qualidade.csv`, 1 linhas):

```csv
linhas,utilizadores,filmes,pares_repetidos,linhas_com_nulos,fora_dominio_comum,nao_inteiros,inferior_a_um
1000209,6040,3706,0,0,0,0,0
```

**32M:** não corrido.

### `sql/athena/analise/valores_ano.sql`

- **Dialeto:** Athena (Trino)
- **Pergunta:** quantas avaliações de cada valor (0,5 a 5) houve em cada ano? Mostra, por exemplo, a partir de que ano aparecem os meios pontos. (equivalente Athena de `sql/analise/valores_ano.sql`)

```sql
-- valores_ano.sql (Athena) - equivalente a sql/analise/valores_ano.sql
-- Origem: notebook do Luís, célula 108 ("novo-queries"), consultas_sql()["valores_ano"].
--
-- Fuso horário: year vem das pastas de ratings_part ou de year(from_unixtime("timestamp")),
-- e from_unixtime devolve UTC. O resultado não depende do fuso da sessão.
-- Resultado agregado: no máximo 10 valores por ano.
--
-- Parâmetros: ${ratings}
SELECT r.year AS ano, r.rating, COUNT(*) AS num_ratings
FROM ${ratings} AS r
GROUP BY r.year, r.rating
ORDER BY r.year, r.rating
```

**Output (emulação DuckDB; não corrido no Athena), small** (`results/small/analises/athena_emulado/valores_ano.csv`, 195 linhas):

```csv
ano,rating,num_ratings
1996,1.0,195
1996,2.0,404
1996,3.0,2575
1996,4.0,1701
1996,5.0,1165
```

**Output (emulação DuckDB; não corrido no Athena), 1m** (`results/1m/analises/athena_emulado/valores_ano.csv`, 20 linhas):

```csv
ano,rating,num_ratings
2000,1.0,51027
2000,2.0,96069
2000,3.0,234296
2000,4.0,314446
2000,5.0,208919
```

**32M:** não corrido.

### 4.6 `sql/athena/ddl/` (DDL Athena)

### `sql/athena/ddl/00_database.sql`

- **Dialeto:** Athena (Hive DDL / Glue Data Catalog)
- **Função (DDL, sem pergunta analítica):** Base de dados no Glue Data Catalog onde ficam as tabelas do dataset (ex.: movielens_32m).

```sql
-- 00_database.sql
-- Base de dados no Glue Data Catalog onde ficam as tabelas do dataset (ex.: movielens_32m).
-- No Athena, uma "base de dados" é só um agrupamento de tabelas no catálogo: não guarda dados.
--
-- Parâmetros: ${database} (substituído pelo scripts/athena_setup.py)
CREATE DATABASE IF NOT EXISTS ${database}
```

**Output:** nenhum; DDL nunca executado no Athena (só verificado com `athena_setup.py --dry-run`).

### `sql/athena/ddl/01_ratings.sql`

- **Dialeto:** Athena (Hive DDL / Glue Data Catalog)
- **Função (DDL, sem pergunta analítica):** ratings em Parquet (zstd), sem partição: um único ficheiro em ratings/.

```sql
-- 01_ratings.sql
-- ratings em Parquet (zstd), sem partição: um único ficheiro em ratings/.
--
-- Notas:
-- - EXTERNAL: a tabela só aponta para os ficheiros no S3. Apagar a tabela (DROP TABLE)
--   não apaga os dados.
-- - O catálogo guarda os nomes em minúsculas (userId -> userid). Na leitura de Parquet
--   a correspondência de nomes não distingue maiúsculas, por isso os ficheiros servem tal como estão.
-- - timestamp é palavra reservada: no DDL vai entre backticks, nas queries entre aspas duplas.
-- - Tipos iguais aos dos ficheiros (ver reports/cloud_manifest_<dataset>.md).
--
-- Parâmetros: ${bucket}, ${pasta}
CREATE EXTERNAL TABLE IF NOT EXISTS ratings (
    userid      int,
    movieid     int,
    rating      double,
    `timestamp` bigint
)
STORED AS PARQUET
LOCATION 's3://${bucket}/${pasta}/ratings/'
```

**Output:** nenhum; DDL nunca executado no Athena (só verificado com `athena_setup.py --dry-run`).

### `sql/athena/ddl/02_ratings_part.sql`

- **Dialeto:** Athena (Hive DDL / Glue Data Catalog)
- **Função (DDL, sem pergunta analítica):** ratings em Parquet (zstd), particionado por ano: ratings_part/year=AAAA/*.parquet.

```sql
-- 02_ratings_part.sql
-- ratings em Parquet (zstd), particionado por ano: ratings_part/year=AAAA/*.parquet.
--
-- Notas:
-- - year não está dentro dos ficheiros: vem do nome da pasta, por isso aparece só em
--   PARTITIONED BY e não na lista de colunas.
-- - Depois de criar a tabela, o catálogo ainda não conhece as pastas year=AAAA.
--   O ficheiro seguinte (03_ratings_part_particoes.sql) carrega-as.
--
-- Parâmetros: ${bucket}, ${pasta}
CREATE EXTERNAL TABLE IF NOT EXISTS ratings_part (
    userid      int,
    movieid     int,
    rating      double,
    `timestamp` bigint
)
PARTITIONED BY (year int)
STORED AS PARQUET
LOCATION 's3://${bucket}/${pasta}/ratings_part/'
```

**Output:** nenhum; DDL nunca executado no Athena (só verificado com `athena_setup.py --dry-run`).

### `sql/athena/ddl/03_ratings_part_particoes.sql`

- **Dialeto:** Athena (Hive DDL / Glue Data Catalog)
- **Função (DDL, sem pergunta analítica):** Regista no catálogo as partições de ratings_part: percorre as pastas year=AAAA no S3

```sql
-- 03_ratings_part_particoes.sql
-- Regista no catálogo as partições de ratings_part: percorre as pastas year=AAAA no S3
-- e acrescenta uma partição por pasta. Tem de voltar a correr se forem acrescentados anos.
-- (Alternativa sem este passo: partition projection nas TBLPROPERTIES da tabela.)
--
-- Parâmetros: nenhum
MSCK REPAIR TABLE ratings_part
```

**Output:** nenhum; DDL nunca executado no Athena (só verificado com `athena_setup.py --dry-run`).

### `sql/athena/ddl/04_ratings_csv.sql`

- **Dialeto:** Athena (Hive DDL / Glue Data Catalog)
- **Função (DDL, sem pergunta analítica):** Cópia do ratings.csv original, para comparar os bytes lidos pelo Athena em CSV e em Parquet.

```sql
-- 04_ratings_csv.sql
-- Cópia do ratings.csv original, para comparar os bytes lidos pelo Athena em CSV e em Parquet.
--
-- Notas:
-- - LazySimpleSerDe (ROW FORMAT DELIMITED): serve porque o ratings.csv só tem números,
--   sem aspas nem vírgulas dentro dos campos.
-- - skip.header.line.count salta a linha de cabeçalho (userId,movieId,rating,timestamp).
--
-- Parâmetros: ${bucket}, ${pasta}
CREATE EXTERNAL TABLE IF NOT EXISTS ratings_csv (
    userid      int,
    movieid     int,
    rating      double,
    `timestamp` bigint
)
ROW FORMAT DELIMITED
    FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://${bucket}/${pasta}/ratings_csv/'
TBLPROPERTIES ('skip.header.line.count' = '1')
```

**Output:** nenhum; DDL nunca executado no Athena (só verificado com `athena_setup.py --dry-run`).

### `sql/athena/ddl/05_movies.sql`

- **Dialeto:** Athena (Hive DDL / Glue Data Catalog)
- **Função (DDL, sem pergunta analítica):** movies em Parquet (zstd). genres guarda vários géneros num só texto ("Action|Comedy").

```sql
-- 05_movies.sql
-- movies em Parquet (zstd). genres guarda vários géneros num só texto ("Action|Comedy").
--
-- Parâmetros: ${bucket}, ${pasta}
CREATE EXTERNAL TABLE IF NOT EXISTS movies (
    movieid     int,
    title       string,
    genres      string
)
STORED AS PARQUET
LOCATION 's3://${bucket}/${pasta}/movies/'
```

**Output:** nenhum; DDL nunca executado no Athena (só verificado com `athena_setup.py --dry-run`).

### `sql/athena/ddl/06_tags.sql`

- **Dialeto:** Athena (Hive DDL / Glue Data Catalog)
- **Função (DDL, sem pergunta analítica):** tags em Parquet (zstd). Não existe no dataset 1M (o athena_setup.py salta-a).

```sql
-- 06_tags.sql
-- tags em Parquet (zstd). Não existe no dataset 1M (o athena_setup.py salta-a).
--
-- Parâmetros: ${bucket}, ${pasta}
CREATE EXTERNAL TABLE IF NOT EXISTS tags (
    userid      int,
    movieid     int,
    tag         string,
    `timestamp` bigint
)
STORED AS PARQUET
LOCATION 's3://${bucket}/${pasta}/tags/'
```

**Output:** nenhum; DDL nunca executado no Athena (só verificado com `athena_setup.py --dry-run`).

### `sql/athena/ddl/07_links.sql`

- **Dialeto:** Athena (Hive DDL / Glue Data Catalog)
- **Função (DDL, sem pergunta analítica):** links em Parquet (zstd). imdbid é texto (mantém os zeros à esquerda, ex.: 0114709).

```sql
-- 07_links.sql
-- links em Parquet (zstd). imdbid é texto (mantém os zeros à esquerda, ex.: 0114709).
-- Não existe no dataset 1M (o athena_setup.py salta-a).
--
-- Parâmetros: ${bucket}, ${pasta}
CREATE EXTERNAL TABLE IF NOT EXISTS links (
    movieid     int,
    imdbid      string,
    tmdbid      int
)
STORED AS PARQUET
LOCATION 's3://${bucket}/${pasta}/links/'
```

**Output:** nenhum; DDL nunca executado no Athena (só verificado com `athena_setup.py --dry-run`).

## 5. Resultados quantitativos

### 5.1 `results/sizes.csv` (tamanhos em MB e tempos de conversão em s)

| run_at | dataset | table | csv_mb | parquet_mb | parquet_by_year_mb | n_partitions | seconds | seconds_by_year |
|---|---|---|---|---|---|---|---|---|
| 2026-11-01T17:46:55 | small | ratings | 2.48 | 0.69 | 0.77 | 23 | 0.019 | 0.014 |
| 2026-11-01T17:46:55 | small | movies | 0.49 | 0.25 |  |  | 0.005 |  |
| 2026-11-01T17:46:55 | small | tags | 0.12 | 0.05 |  |  | 0.002 |  |
| 2026-11-01T17:46:55 | small | links | 0.2 | 0.13 |  |  | 0.003 |  |
| 2026-11-01T17:46:58 | 1m | ratings | 23.59 | 5.21 | 5.25 | 4 | 0.046 | 0.02 |
| 2026-11-01T17:46:58 | 1m | movies | 0.17 | 0.09 |  |  | 0.003 |  |

Notas:
- O `sizes.csv` só tem small e 1M. **O 32M não tem linhas em `sizes.csv`** (no 32M só foram registados no `pipeline_runs.csv` os passos `benchmark` e `eda`; o `ingest`/`parquet` correram noutra cópia, `~/Desktop/Nova IMS 2 Semestre/BDF/`, a que `data/32m` aponta).
- Tamanhos do 32M disponíveis em `reports/cloud_manifest_32m.md` (Parquet fase 1, snappy → cloud, zstd):

| Tabela | Parquet fase 1 (snappy, MB) | Parquet cloud (zstd, MB) | Linhas |
|---|---:|---:|---:|
| ratings | 217.68 | 158.86 | 32 000 204 |
| ratings_part (29 anos) | 214.04 | 154.60 | 32 000 204 |
| ratings_csv | — | 877.08 (CSV) | 32 000 204 |
| movies | 2.19 | 1.40 | 87 585 |
| tags | 20.93 | 13.37 | 2 000 072 |
| links | 1.25 | 0.86 | 87 585 |

  (Para referência, `du -sh` na outra cópia: `ratings.csv` 836M, `tags.csv` 69M, `movies.csv` 4.0M, `links.csv` 1.9M. O tempo de conversão do 32M não está registado.)

### 5.2 `results/pipeline_runs.csv`

| run_at | dataset | step | seconds |
|---|---|---|---|
| 2026-11-01T17:46:55 | small | ingest | 0.21 |
| 2026-11-01T17:46:55 | small | parquet | 0.1 |
| 2026-11-01T17:46:55 | small | benchmark | 0.29 |
| 2026-11-01T17:46:57 | small | eda | 1.78 |
| 2026-11-01T17:46:57 | 1m | ingest | 0.19 |
| 2026-11-01T17:46:58 | 1m | parquet | 0.13 |
| 2026-11-01T17:46:58 | 1m | benchmark | 0.32 |
| 2026-11-01T17:46:59 | 1m | eda | 1.5 |
| 2026-11-01T21:17:28 | 32m | benchmark | 2.91 |
| 2026-11-01T21:17:32 | 32m | eda | 3.82 |
| 2026-11-05T19:55:26 | small | analises | 0.58 |

### 5.3 `results/benchmarks.csv` (completo; mediana de 3 corridas, segundos)

| run_at | dataset | query | formato | median_s | n_rows |
|---|---|---|---|---|---|
| 2026-11-01T17:46:55 | small | 01_generos | parquet | 0.0009 | 20 |
| 2026-11-01T17:46:55 | small | 01_generos | parquet_by_year | 0.0008 | 20 |
| 2026-11-01T17:46:55 | small | 02_filmes_por_genero | parquet | 0.0012 | 20 |
| 2026-11-01T17:46:55 | small | 02_filmes_por_genero | parquet_by_year | 0.001 | 20 |
| 2026-11-01T17:46:55 | small | 03_avaliacoes_por_utilizador | parquet | 0.0068 | 610 |
| 2026-11-01T17:46:55 | small | 03_avaliacoes_por_utilizador | parquet_by_year | 0.0025 | 610 |
| 2026-11-01T17:46:55 | small | 04_top_filmes | parquet | 0.0064 | 10 |
| 2026-11-01T17:46:55 | small | 04_top_filmes | parquet_by_year | 0.0045 | 10 |
| 2026-11-01T17:46:55 | small | 05_ratings_por_ano | parquet | 0.0023 | 23 |
| 2026-11-01T17:46:55 | small | 05_ratings_por_ano | parquet_by_year | 0.0014 | 23 |
| 2026-11-01T17:46:58 | 1m | 01_generos | parquet | 0.0006 | 18 |
| 2026-11-01T17:46:58 | 1m | 01_generos | parquet_by_year | 0.0006 | 18 |
| 2026-11-01T17:46:58 | 1m | 02_filmes_por_genero | parquet | 0.0009 | 18 |
| 2026-11-01T17:46:58 | 1m | 02_filmes_por_genero | parquet_by_year | 0.0008 | 18 |
| 2026-11-01T17:46:58 | 1m | 03_avaliacoes_por_utilizador | parquet | 0.0094 | 6040 |
| 2026-11-01T17:46:58 | 1m | 03_avaliacoes_por_utilizador | parquet_by_year | 0.0101 | 6040 |
| 2026-11-01T17:46:58 | 1m | 04_top_filmes | parquet | 0.0066 | 10 |
| 2026-11-01T17:46:58 | 1m | 04_top_filmes | parquet_by_year | 0.006 | 10 |
| 2026-11-01T17:46:58 | 1m | 05_ratings_por_ano | parquet | 0.0052 | 4 |
| 2026-11-01T17:46:58 | 1m | 05_ratings_por_ano | parquet_by_year | 0.001 | 4 |
| 2026-11-01T21:17:26 | 32m | 01_generos | parquet | 0.0026 | 20 |
| 2026-11-01T21:17:26 | 32m | 01_generos | parquet_by_year | 0.0025 | 20 |
| 2026-11-01T21:17:26 | 32m | 02_filmes_por_genero | parquet | 0.0027 | 20 |
| 2026-11-01T21:17:26 | 32m | 02_filmes_por_genero | parquet_by_year | 0.0027 | 20 |
| 2026-11-01T21:17:26 | 32m | 03_avaliacoes_por_utilizador | parquet | 0.2524 | 200948 |
| 2026-11-01T21:17:27 | 32m | 03_avaliacoes_por_utilizador | parquet_by_year | 0.2545 | 200948 |
| 2026-11-01T21:17:28 | 32m | 04_top_filmes | parquet | 0.1253 | 10 |
| 2026-11-01T21:17:28 | 32m | 04_top_filmes | parquet_by_year | 0.1259 | 10 |
| 2026-11-01T21:17:28 | 32m | 05_ratings_por_ano | parquet | 0.0735 | 29 |
| 2026-11-01T21:17:28 | 32m | 05_ratings_por_ano | parquet_by_year | 0.013 | 29 |
| 2026-11-05T19:37:06 | small | 01_generos | parquet | 0.0009 | 20 |
| 2026-11-05T19:37:06 | small | 01_generos | parquet_by_year | 0.0008 | 20 |
| 2026-11-05T19:37:06 | small | 02_filmes_por_genero | parquet | 0.0011 | 20 |
| 2026-11-05T19:37:06 | small | 02_filmes_por_genero | parquet_by_year | 0.001 | 20 |
| 2026-11-05T19:37:07 | small | 03_avaliacoes_por_utilizador | parquet | 0.0039 | 610 |
| 2026-11-05T19:37:07 | small | 03_avaliacoes_por_utilizador | parquet_by_year | 0.0028 | 610 |
| 2026-11-05T19:37:07 | small | 04_top_filmes | parquet | 0.0044 | 10 |
| 2026-11-05T19:37:07 | small | 04_top_filmes | parquet_by_year | 0.0041 | 10 |
| 2026-11-05T19:37:07 | small | 05_ratings_por_ano | parquet | 0.0022 | 23 |
| 2026-11-05T19:37:07 | small | 05_ratings_por_ano | parquet_by_year | 0.0014 | 23 |

### 5.4 `results/cloud_benchmarks.csv` (completo; só `engine=duckdb`)

| run_at | dataset | engine | query | formato | runs | median_s | median_engine_s | data_scanned_mb | n_rows |
|---|---|---|---|---|---|---|---|---|---|
| 2026-11-03T21:30:40 | small | duckdb | 01_generos | parquet | 3 | 0.0009 |  |  | 20 |
| 2026-11-03T21:30:40 | small | duckdb | 02_filmes_por_genero | parquet | 3 | 0.0012 |  |  | 20 |
| 2026-11-03T21:30:40 | small | duckdb | 03_avaliacoes_por_utilizador | csv | 3 | 0.0175 |  |  | 610 |
| 2026-11-03T21:30:40 | small | duckdb | 03_avaliacoes_por_utilizador | parquet | 3 | 0.0047 |  |  | 610 |
| 2026-11-03T21:30:40 | small | duckdb | 03_avaliacoes_por_utilizador | parquet_part | 3 | 0.0034 |  |  | 610 |
| 2026-11-03T21:30:40 | small | duckdb | 04_top_filmes | csv | 3 | 0.0158 |  |  | 10 |
| 2026-11-03T21:30:40 | small | duckdb | 04_top_filmes | parquet | 3 | 0.0047 |  |  | 10 |
| 2026-11-03T21:30:40 | small | duckdb | 04_top_filmes | parquet_part | 3 | 0.0055 |  |  | 10 |
| 2026-11-03T21:30:40 | small | duckdb | 05_ratings_por_ano | csv | 3 | 0.0192 |  |  | 23 |
| 2026-11-03T21:30:41 | small | duckdb | 05_ratings_por_ano | parquet | 3 | 0.0095 |  |  | 23 |
| 2026-11-03T21:30:41 | small | duckdb | 05_ratings_por_ano | parquet_part | 3 | 0.0016 |  |  | 23 |
| 2026-11-03T21:30:41 | small | duckdb | 06_ratings_desde_2015 | csv | 3 | 0.0203 |  |  | 4 |
| 2026-11-03T21:30:41 | small | duckdb | 06_ratings_desde_2015 | parquet | 3 | 0.0116 |  |  | 4 |
| 2026-11-03T21:30:41 | small | duckdb | 06_ratings_desde_2015 | parquet_part | 3 | 0.0012 |  |  | 4 |
| 2026-11-03T21:32:02 | 32m | duckdb | 01_generos | parquet | 3 | 0.0027 |  |  | 20 |
| 2026-11-03T21:32:02 | 32m | duckdb | 02_filmes_por_genero | parquet | 3 | 0.003 |  |  | 20 |
| 2026-11-03T21:32:04 | 32m | duckdb | 03_avaliacoes_por_utilizador | csv | 3 | 0.6797 |  |  | 200948 |
| 2026-11-03T21:32:05 | 32m | duckdb | 03_avaliacoes_por_utilizador | parquet | 3 | 0.2594 |  |  | 200948 |
| 2026-11-03T21:32:06 | 32m | duckdb | 03_avaliacoes_por_utilizador | parquet_part | 3 | 0.2894 |  |  | 200948 |
| 2026-11-03T21:32:07 | 32m | duckdb | 04_top_filmes | csv | 3 | 0.5538 |  |  | 10 |
| 2026-11-03T21:32:08 | 32m | duckdb | 04_top_filmes | parquet | 3 | 0.1521 |  |  | 10 |
| 2026-11-03T21:32:08 | 32m | duckdb | 04_top_filmes | parquet_part | 3 | 0.1513 |  |  | 10 |
| 2026-11-03T21:32:11 | 32m | duckdb | 05_ratings_por_ano | csv | 3 | 0.8595 |  |  | 29 |
| 2026-11-03T21:32:12 | 32m | duckdb | 05_ratings_por_ano | parquet | 3 | 0.547 |  |  | 29 |
| 2026-11-03T21:32:13 | 32m | duckdb | 05_ratings_por_ano | parquet_part | 3 | 0.0174 |  |  | 29 |
| 2026-11-03T21:32:16 | 32m | duckdb | 06_ratings_desde_2015 | csv | 3 | 0.9871 |  |  | 9 |
| 2026-11-03T21:32:17 | 32m | duckdb | 06_ratings_desde_2015 | parquet | 3 | 0.5885 |  |  | 9 |
| 2026-11-03T21:32:17 | 32m | duckdb | 06_ratings_desde_2015 | parquet_part | 3 | 0.0078 |  |  | 9 |

### 5.5 `eda_indicadores.csv` por dataset

| indicador | small | 1m | 32m |
|---|---:|---:|---:|
| n_ratings | 100836.0 | 1000209.0 | 32000204.0 |
| n_utilizadores | 610.0 | 6040.0 | 200948.0 |
| n_filmes_avaliados | 9724.0 | 3706.0 | 84432.0 |
| n_filmes_catalogo | 9742.0 | 3883.0 | 87585.0 |
| filmes_sem_avaliacoes | 18.0 | 177.0 | 3153.0 |
| esparsidade_pct | 98.3 | 95.532 | 99.811 |
| rating_media | 3.502 | 3.582 | 3.54 |
| rating_mediana | 3.5 | 4.0 | 3.5 |
| rating_desvio_padrao | 1.043 | 1.117 | 1.059 |
| rating_moda | 4.0 | 4.0 | 4.0 |
| ratings_por_user_min | 20.0 | 20.0 | 20.0 |
| ratings_por_user_mediana | 70.5 | 96.0 | 73.0 |
| ratings_por_user_media | 165.3 | 165.6 | 159.2 |
| ratings_por_user_p90 | 400.30000000000007 | 400.0 | 364.0 |
| ratings_por_user_max | 2698.0 | 2314.0 | 33332.0 |
| gini_user | 0.604 | 0.529 | 0.594 |
| pct_ratings_top10pct_user | 47.7 | 38.1 | 47.2 |
| ratings_por_movie_min | 1.0 | 1.0 | 1.0 |
| ratings_por_movie_mediana | 3.0 | 123.5 | 5.0 |
| ratings_por_movie_media | 10.4 | 269.9 | 379.0 |
| ratings_por_movie_p90 | 27.0 | 729.5 | 248.90000000000873 |
| ratings_por_movie_max | 329.0 | 3428.0 | 102929.0 |
| gini_movie | 0.716 | 0.634 | 0.952 |
| pct_ratings_top10pct_movie | 60.0 | 44.4 | 95.7 |
| ano_primeiro_rating | 1996.0 | 2000.0 | 1995.0 |
| ano_ultimo_rating | 2018.0 | 2003.0 | 2023.0 |
| n_generos | 19.0 | 18.0 | 19.0 |
| filmes_sem_ano_no_titulo | 13.0 | 0.0 | 617.0 |
| tags_total | 3683.0 | — | 2000072.0 |
| tags_utilizadores | 58.0 | — | 15848.0 |
| tags_filmes | 1572.0 | — | 51323.0 |

(`—` = indicador não existe no dataset; o 1M não tem tags.)

### 5.6 Figuras PNG geradas

```
results/1m/eda/01_distribuicao_ratings.png
results/1m/eda/02_atividade_utilizadores.png
results/1m/eda/03_popularidade_filmes.png
results/1m/eda/04_cauda_longa_filmes.png
results/1m/eda/05_evolucao_temporal.png
results/1m/eda/06_generos.png
results/1m/eda/07_ano_lancamento.png
results/1m/eda/08_heatmap_genero_ano.png
results/1m/eda/10_painel_resumo.png
results/32m/eda/01_distribuicao_ratings.png
results/32m/eda/02_atividade_utilizadores.png
results/32m/eda/03_popularidade_filmes.png
results/32m/eda/04_cauda_longa_filmes.png
results/32m/eda/05_evolucao_temporal.png
results/32m/eda/06_generos.png
results/32m/eda/07_ano_lancamento.png
results/32m/eda/08_heatmap_genero_ano.png
results/32m/eda/09_top_tags.png
results/32m/eda/10_painel_resumo.png
results/small/eda/01_distribuicao_ratings.png
results/small/eda/02_atividade_utilizadores.png
results/small/eda/03_popularidade_filmes.png
results/small/eda/04_cauda_longa_filmes.png
results/small/eda/05_evolucao_temporal.png
results/small/eda/06_generos.png
results/small/eda/07_ano_lancamento.png
results/small/eda/08_heatmap_genero_ano.png
results/small/eda/09_top_tags.png
results/small/eda/10_painel_resumo.png
```

O 1M não tem `09_top_tags.png` (não tem tags). Total: 29 ficheiros PNG. Não há figuras do `05_analises.py` nem do `06_coordenacao.py`.

## 6. Deteção de bots e coordenação

### 6.1 Regras (`sql/analise/10_flag_bots.sql`, a validar com o Luís)

Substitui a regra `utilizadores_sinalizados` do notebook do Luís (célula 112), que sinalizava 34,4% do small e 46,8% do 1M, sobretudo pelo pico normal do registo.

1. **Eventos de submissão:** avaliações com o mesmo `(userId, timestamp)` formam um evento; todos os ritmos são medidos em eventos.
2. **Submissão em lote** (categoria à parte, não é bot): pelo menos um evento com ≥ 10 avaliações no mesmo segundo.
3. **Regra A — ritmo sustentado fora do registo:** ignora as primeiras 24 h; `eventos_10min` = eventos numa janela `RANGE BETWEEN CURRENT ROW AND 599 FOLLOWING` (por utilizador e fase); limiar = quantil **p99,9** do máximo de `eventos_10min` entre os utilizadores com atividade depois do registo (calculado na própria query; definido num só sítio, `limiar_regra_a`).
4. **Regra B — registo extremo:** nas primeiras 24 h, ≥ 100 eventos **e** intervalo mediano ≤ 2 s.
5. **Sinais complementares** (0 a 3, não classificam sozinhos): desvio-padrão das notas no 1% mais baixo; % de nota modal no 1% mais alto; % de eventos em lote (≥ 2 avaliações) no 1% mais alto.
6. **Classificação:** `suspeito (regra A)`, `suspeito (regra B)`, `suspeito (regras A e B)`; senão `submissão em lote`; senão `sem sinais`. Nunca "bot confirmado".

`10_flag_bots_calibracao.sql` devolve a distribuição do ritmo sustentado e o n.º de sinalizados no p99 / p99,5 / p99,9.

### 6.2 Utilizadores sinalizados por dataset

| | small | 1M | 32M |
|---|---:|---:|---:|
| Utilizadores | 610 | 6 040 | 200 948 |
| Com atividade depois do registo | 248 | 2 239 | — |
| Ritmo sustentado p50 / p90 / p99 / p99,5 / p99,9 / máx. | 18 / 52,3 / 90,8 / 100,6 / 114,8 / 119 | 14 / 26 / 35 / 38 / 40 / 45 | — |
| Regra A no p99 / p99,5 / p99,9 | 3 / 2 / 1 | 25 / 13 / 6 | — |
| Regra B | 1 (o 89) | 0 | — |
| **Suspeitos (A ou B, p99,9)** | **2 (0,33%)** — 89 (B), 610 (A) | **6 (0,10%)** — 1077, 1117, 1875, 2880, 5522, 5536 (todos A, 40–45 eventos/10 min, mediana 14–19 s) | **não corrido** |
| Submissão em lote (à parte) | 13 (2,1%) | 339 (5,6%) | — |
| Regra original do Luís (`num_sinais > 0`) | 210 (34,4%) | 2 829 (46,8%) | — |

Sensibilidade da regra B: com ≥ 200 eventos o resultado é o mesmo. Fontes: `results/<ds>/analises/analises_relatorio.md` e `docs/validacao_queries_colega.md` §13.5.

### 6.3 Utilizadores de referência (small, `results/small/analises/10_flag_bots_referencia.csv`)


| userId | caso | esperado | obtido | ok | justificacao |
|---|---|---|---|---|---|
| 257 | 20 avaliações em 11 min no registo: não pode ser sinalizado | sem sinais | sem sinais | sim | depois do registo: máx. - eventos em 10 min (limiar 114.8); registo: 19 eventos, mediana de 4 s (a regra B exige >= 100 eventos e <= 2 s); máx. 2 avaliações no mesmo segundo; sinais complementares: 0/3 |
| 7 | uso normal: não pode ser sinalizado | sem sinais | sem sinais | sim | depois do registo: máx. 4 eventos em 10 min (limiar 114.8); registo: 102 eventos, mediana de 5 s (a regra B exige >= 100 eventos e <= 2 s); máx. 1 avaliações no mesmo segundo; sinais complementares: 0/3 |
| 89 | 518 avaliações em 23 min no registo, ~2 s cada: candidato | suspeito (regra B) | suspeito (regra B) | sim | regra B: 481 eventos nas primeiras 24 h, mediana de 2 s entre eventos (>= 100 e <= 2 s); sinais complementares: 0/3 |
| 610 | 566 avaliações numa hora, ~4 s cada, ~6 meses depois do registo | suspeito (regra A) | suspeito (regra A) | sim | regra A: 119 eventos em 10 min depois do registo (limiar p99,9 = 114.8), mediana de 4 s entre eventos; sinais complementares: 0/3 |
| 534 | muitas avaliações no mesmo segundo (2016): não é bot | submissão em lote | submissão em lote | sim | submissão em lote: até 128 avaliações no mesmo segundo (4% dos eventos com 2 ou mais), primeiro dia 2016-04-04; sinais complementares: 0/3 |

Os casos de lote dos anos 90 (191, 429, 99, 163) também ficam como `submissão em lote`.

### 6.4 Coordenação entre contas (`scripts/06_coordenacao.py`)

**1M** (20 permutações, ~2 s; notas 1 e 5): real vs permutações — U≥3,D≥1,5: 87 vs 73,1 (p=0,095); U≥3,D≥2: 20 vs 14,8 (p=0,143); U≥5,D≥1,5: 3 vs 2,0; U≥5,D≥2: 2 vs 0,35 (p=0,095); U≥10 e U≥20: 0. Nenhuma das 24 comparações passa Bonferroni (0,05/24; o menor valor-p possível é 0,048). As 10 rajadas mais fortes são todas de 20–21/11/2000 (pico de registos; 70 das 87 rajadas), contas no registo (98% nas primeiras 24 h), nenhuma suspeita no bloco 5.
**Conclusão 1M:** não há evidência de contas coordenadas; as rajadas explicam-se pelo registo em massa de novembro de 2000.

**32M** (200 permutações, 596,8 s, memória máx. ~6,3 GB; principal 0,5 e 5,0, sensibilidade ≤ 1,0; 40 comparações): principal U≥3,D≥1,5: 2 200 reais vs 931,1 (z=47,4, p=0,005); 25 das 40 comparações ficam acima de todas as permutações (p=0,005), mas nenhuma pode passar Bonferroni (0,05/40=0,00125 < 1/201) — seriam precisas ≥ 800 permutações. O excesso está todo antes de 2003 (até 2002: 2 016 reais vs 729; de 2003 em diante: 184 vs 202) e coincide com a mudança para a escala de meias estrelas (2003-02-18; 5,0 passa de 21,3% para 12,1% das notas), que a permutação dentro do filme não respeita. As 10 rajadas mais fortes são quase todas contas no registo (26/11/1996, 1997, 1999-12-11, 2005-03-22); a exceção é 22/05/1998 (Body Snatchers, Money Talks: contas antigas, 0% no registo), o único padrão por explicar.
**Conclusão 32M:** não há evidência de coordenação; o excesso é efeito da mudança de escala/linha de base não estratificada. Proposta (não implementada): permutar dentro de (filme, era antes/depois de 2003-02-18) ou (filme, ano), com ≥ 800 permutações. O `10_flag_bots.csv` do 32M não existe, por isso o top 10 do 32M não tem a coluna de suspeitos.

Ficheiros: `results/{1m,32m}/bots_coordenacao/` (o small não foi corrido). Linhas: 1m/bots_coordenacao/linha_base.csv: 480; 1m/bots_coordenacao/rajadas.csv: 87; 1m/bots_coordenacao/rajadas_por_ano.csv: 3; 1m/bots_coordenacao/teste.csv: 24; 1m/bots_coordenacao/top10_contas.csv: 45; 1m/bots_coordenacao/top10_rajadas.csv: 10; 1m/bots_coordenacao/verificacao_permutacao.csv: 6; 32m/bots_coordenacao/linha_base.csv: 8000; 32m/bots_coordenacao/rajadas.csv: 3041; 32m/bots_coordenacao/rajadas_por_ano.csv: 29; 32m/bots_coordenacao/teste.csv: 40; 32m/bots_coordenacao/top10_contas.csv: 94; 32m/bots_coordenacao/top10_rajadas.csv: 10; 32m/bots_coordenacao/verificacao_permutacao.csv: 6.

## 7. Cloud (AWS: S3 → Glue Data Catalog → Athena)

**Preparado:**
- `data/cloud/ml-latest-small/`, `ml-1m/`, `ml-32m/` gerados pelo `prepare_cloud.py`, com manifestos `reports/cloud_manifest_{small,1m,32m}.md` (todas as verificações passaram). Estrutura: `ratings/`, `ratings_part/year=AAAA/`, `ratings_csv/`, `movies/`, `tags/`, `links/` (o 1M só tem ratings e movies).
- DDL em `sql/athena/ddl/` (00–07): base `movielens_<dataset>` (ex.: `movielens_32m`); tabelas EXTERNAL `ratings` (Parquet zstd), `ratings_part` (Parquet, `PARTITIONED BY (year)`, partições por `MSCK REPAIR TABLE`), `ratings_csv` (LazySimpleSerDe), `movies`, `tags`, `links`. Localização `s3://${bucket}/${pasta}/<tabela>/`.
- Queries Athena: `sql/athena/queries/01–06` (benchmark) e `sql/athena/analise/` (16 análises; `flag_bots` como CTAS em Parquet).
- Scripts: `athena_setup.py`, `athena_benchmark.py`, `athena_common.py` (boto3).
- `config.yaml`: `region: us-east-1`, `workgroup: primary`, **`bucket_dados: null` e `bucket_resultados: null`** (nomes de exemplo nos comentários: `bdf26-g1-movielens-dados`, `bdf26-g1-athena-resultados`). Credenciais do AWS Academy Learner Lab em `~/.aws/credentials` (fora do repositório; `.aws/`, `*.env` e chaves no `.gitignore`).

**Executado:**
- Só a parte local: `athena_benchmark.py --engines duckdb` no small e no 32M (secção 5.4) e a emulação Athena no DuckDB (`05_analises.py --emular-athena`) no small e no 1M — as 16 queries dão o mesmo n.º de linhas que as versões DuckDB.
- **Nenhuma query correu no Athena.** O `aws s3 sync` não foi feito, não há buckets configurados, e `results/cloud_benchmarks.csv` não tem linhas `engine=athena` (as colunas `median_engine_s` e `data_scanned_mb` estão vazias). **Não há bytes lidos nem custos reais.**
- Estimativa do README (não medida): o benchmark completo do 32M leria ~12 GB no Athena (sobretudo as 12 corridas sobre o CSV, 877 MB cada); a 5 USD/TB custaria menos de 0,10 USD. O Athena cobra no mínimo 10 MB por query.

## 8. Pendentes

### 8.1 TODOs no código

Não há `TODO`/`FIXME`/`XXX` no código. Marcadores encontrados:
- `*** A VALIDAR COM O LUÍS ***` em `sql/analise/10_flag_bots.sql`, `sql/analise/10_flag_bots_calibracao.sql`, `sql/athena/analise/10_flag_bots.sql`, `sql/athena/analise/10_flag_bots_calibracao.sql`; o docstring de `scripts/06_coordenacao.py` diz "a validar com o Luís".
- `sql/10_flag_bots.sql`: "ESQUELETO, ainda sem regras" (ignorado pelo benchmark).
- `docs/validacao_queries_colega.md` §P10: "falta confirmar a passagem exata" da referência Harper & Konstan (2015).

### 8.2 `docs/validacao_queries_colega.md` §13.9 Pendentes (copiado)

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


Questões em aberto da secção 12 do mesmo documento foram respondidas em §13.0.

### 8.3 O que não foi corrido (resumo)

- **32M:** não correram `05_analises.py` (logo não há `results/32m/analises/`, nem `10_flag_bots.csv`, nem calibração da regra A no 32M) nem os passos `ingest`/`parquet` neste repositório (sem linhas no `sizes.csv`). Correram no 32M: `benchmark`, `eda`, `prepare_cloud.py`, `athena_benchmark.py --engines duckdb` e `06_coordenacao.py` (200 permutações).
- **small:** `06_coordenacao.py` não foi corrido.
- **Athena:** nada (sem upload para o S3, sem buckets no `config.yaml`, sem DDL executado, sem queries, sem bytes/custos). Falta também o script `scripts/athena_analises.py` para correr `sql/athena/analise/`.
- **Validação do Luís:** regras de bots (A, B, quantil, lote, sinais complementares), limites dos eventos (P7), faixas de `grupos_atividade`, opção "só anos completos" de `evolucao_filmes`, notebook oficial (P12), bloco 6 (linha de base estratificada, ≥ 800 permutações, caso 22/05/1998).
- **Git:** nada integrado no `main`; `main` local divergente de `origin/main`.
- **Documentação:** README desatualizado quanto ao passo `analises` e ao `06_coordenacao.py`; a secção "Estrutura do repositório" do topo do README ainda descreve só o notebook.

