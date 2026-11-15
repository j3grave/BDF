# Revisão do branch `fase2-cloud-pipeline`

Data: 15/11/2026. Commit revisto: `5e607be` (igual ao `origin/fase2-cloud-pipeline`).
Âmbito: `scripts/`, `sql/` (DuckDB e Athena), `run_pipeline.py`, `config.yaml`, `.gitignore`,
histórico do git e documentação. Nenhum ficheiro foi alterado durante a revisão, exceto este.

## Resumo

| Nível | N.º | Conclusão |
|---|---:|---|
| Bloqueante | 0 | Nada impede o merge para o `main`. |
| Importante | 6 | Uma decisão de git (branch do Luís), o ficheiro `credentials` na pasta do projeto e documentação desatualizada. |
| Menor | 12 | Coerência DuckDB/Athena, resultados que mudam a cada corrida e pormenores de código e documentação. |

## 1. Verificações feitas

### 1.1 Git

| Verificação | Resultado |
|---|---|
| Árvore de trabalho | Limpa. `HEAD` = `origin/fase2-cloud-pipeline` = `5e607be`. |
| `origin/fase1-pipeline` contido | Sim. |
| `origin/fase2-cloud-prep` contido | Sim. |
| `origin/integracao-queries-luis` contido | **Não.** Faltam 2 commits (ver I1). |
| `origin/main` contido | Sim. O PR para o `main` não tem conflitos (0 commits atrás, 39 à frente). |
| `main` local vs `origin/main` | **Já alinhados** (`e51d050`, 0/0). Os 4 commits locais antigos já não existem. |
| Commits com atribuição ao Claude ou à Anthropic | Nenhum (ver secção 3). |

### 1.2 Teste com um clone limpo

Clone de `https://github.com/j3grave/BDF.git`, branch `fase2-cloud-pipeline`, em `/tmp/bdf_revisao`.
Python 3.13.18 (Homebrew), venv novo, `pip install -r requirements.txt`. Instalou duckdb 2.0.0,
polars 2.1.0, pandas 3.1.1, numpy 2.5.4, matplotlib 3.11.2, pyarrow 26.0.1, boto3 1.44.3 e PyYAML 6.0.3.

`python run_pipeline.py --dataset small`: **os 5 passos terminaram sem erro** (ingest, parquet,
benchmark, eda e analises), em 14 s no total. As 15 verificações do `05_analises.py` deram `[ok]`.

Testes extra, sem AWS:

| Teste | Resultado |
|---|---|
| `05_analises.py --emular-athena` | As 16 versões Athena emuladas dão o mesmo resultado que as versões DuckDB. |
| `05_analises.py --fonte csv` | Todas as verificações passam. |
| `prepare_cloud.py --dataset small` | Verificações OK; manifesto gerado. |
| `athena_setup.py --dry-run` | DDL igual aos ficheiros locais nas 6 tabelas. |
| `athena_benchmark.py --engines duckdb` | 14 combinações, com o mesmo n.º de linhas da fase 1. |
| `athena_benchmark.py --engines athena --dry-run` | Gera as 14 queries do Athena sem erros. |

O `cloud_pipeline.py` **não foi corrido**, como pedido.

### 1.3 Passo `cloud`: problemas evidentes?

Não encontrei nenhum. A ordem é a correta: credenciais → `prepare_cloud` → buckets → upload →
`athena_setup --recriar` (com `MSCK REPAIR TABLE` depois do upload) → validação por ano → benchmark.
O benchmark só escreve no CSV se o n.º de linhas for igual nos dois motores. Os nomes dos buckets
com o ID da conta nunca são escritos em ficheiros. Os pontos M7 e M8 são melhorias, não erros.

### 1.4 Credenciais, ID da conta e caminhos absolutos

| Verificação | Resultado |
|---|---|
| `git log -p \| grep -iE "aws_access\|aws_secret\|[0-9]{12}"` | 23 800 linhas, **todas falsos positivos**: base64 das imagens PNG dos notebooks, floats com 12+ casas decimais e IDs de widgets do Jupyter. |
| Mesma procura em todos os branches, sem notebooks | 0 chaves AWS, 0 IDs de conta de 12 dígitos. Os buckets aparecem sempre como `bdf26-g1-dados-<ID da conta>`. |
| Chaves `AKIA…`/`ASIA…` | Só dentro de base64 de PNG (falso positivo). |
| Caminhos absolutos do Mac em ficheiros versionados | Só em `proximos_passos.md:26-27` (ver M10). Nenhum no código. |
| Ficheiro `credentials` na raiz | Existe, com chaves AWS reais. Está no `.gitignore` (linha 37) e **nunca foi versionado** em nenhum branch (ver I2). |

### 1.5 Ficheiros de dados versionados

Nenhum `.parquet`, `.duckdb`, `.zip`, `.gz`, `.tsv` ou `.dat` no repositório nem no histórico. Os
CSV versionados são todos resultados agregados em `results/`, como o `.gitignore` permite
(`!results/**/*.csv`). O maior é `results/1m/analises/10_flag_bots.csv` (850 KB, uma linha por
utilizador; ver M6).

## 2. Constatações

### Bloqueante

Nenhuma.

### Importante

**I1. O `integracao-queries-luis` não está contido no `fase2-cloud-pipeline`.**
`git branch -r --contains origin/integracao-queries-luis` só devolve o próprio branch. Faltam dois
commits:
- `d602641`: acrescenta `bdf_inventario.md` (3 424 linhas). É um inventário com o estado de
  07/11/2026, já desatualizado. Na linha 3 tem o caminho absoluto do teu Mac.
- `2acfc90`: acrescenta o "BDF 2026 — MovieLens resumo do projeto.md". O ficheiro é **igual** ao
  que já está no `fase2-cloud-pipeline`.

Na prática, só o `bdf_inventario.md` se perde. O `proximos_passos.md:46` diz que o branch "fica
contido e pode ser arquivado", o que não é verdade. **Decisão tua:** descartar o inventário (é um
retrato antigo) ou trazê-lo para o `main` sem o caminho absoluto.

**I2. Ficheiro `credentials` com chaves AWS na pasta do projeto.**
`./credentials` tem um bloco `[default]` com `aws_access_key_id`, `aws_secret_access_key` e
`aws_session_token`. O `.gitignore:37` protege-o do git, mas fica exposto a quem copiar ou
comprimir a pasta (por exemplo, para entregar o trabalho). O README (linhas 226-234) manda pôr as
credenciais em `~/.aws/credentials`. Recomendação: apagar o ficheiro da pasta do projeto. As
credenciais do Learner Lab expiram ao fim de cerca de 4 horas, mas convém não as deixar ali.

**I3. README: a secção "Estrutura do repositório" só descreve o notebook** (`README.md:66-77`).
Já conhecido. Não menciona `scripts/`, `sql/`, `docs/`, `reports/` nem `results/`.

**I4. README: o `06_coordenacao.py` não está documentado.** Já conhecido. Corre à mão, fora do
`run_pipeline.py`, e escreve em `results/<ds>/bots_coordenacao/`.

**I5. README: o passo `analises` está incompleto e a estrutura de pastas está desatualizada.**
- `README.md:144` já lista o `analises`, mas a tabela de passos (`README.md:149-154`) não tem a
  linha do `05_analises.py`.
- `README.md:92-95`: "correu os quatro passos". Hoje são cinco.
- `README.md:160-193` ("Estrutura de pastas"): faltam `05_analises.py`, `06_coordenacao.py`,
  `sql/analise/`, `sql/athena/analise/`, `docs/`, `results/<ds>/analises/` e
  `results/<ds>/bots_coordenacao/`.
- Falta uma secção sobre as análises e a deteção de bots, com a indicação de que as regras ainda
  estão a ser validadas pelo Luís.

**I6. `proximos_passos.md` e o resumo do projeto estão desatualizados quanto ao git e ao 32M.**
- `proximos_passos.md:44`: "o `main` local e o `origin/main` estão divergentes (4 commits só
  locais)". Já não é verdade.
- `proximos_passos.md:71-75`: pede para registar o `ingest`/`parquet` do 32M. Já foi feito no
  `650fc3b`: o `results/sizes.csv:8-11` tem as 4 linhas do 32M (218 MB, 29 partições).
- `BDF 2026 — MovieLens resumo do projeto.md:561-601`: diz que o `integracao-queries-luis`
  "contém tudo", propõe o PR a partir desse branch e tem por fazer o registo do 32M e o passo
  `cloud`, que já estão feitos.

### Menor

**M1. `sql/athena/queries/04_top_filmes.sql:13` não desempata por `movieId`; `sql/04_top_filmes.sql:22`
desempata.** Já conhecido (`proximos_passos.md:108`). O n.º de linhas é sempre igual. A ordem só
muda se houver empates na média dentro do top 10. Isso não acontece no small nem no 1M; no 32M
não foi verificado. Correção: `ORDER BY AVG(r.rating) DESC, m.movieid`.

**M2. Quantis exatos no DuckDB e aproximados no Athena, na deteção de bots.**
`sql/analise/10_flag_bots.sql:86-90` usa `quantile_cont`;
`sql/athena/analise/10_flag_bots.sql:67-71` usa `approx_percentile`. O limiar da regra A
(p99,9) e os sinais complementares podem diferir ligeiramente entre os motores. Isto afeta só os
utilizadores mesmo no limiar. Está documentado no cabeçalho, mas, quando o Athena correr, convém
comparar a lista de sinalizados e não só o n.º de linhas. O mesmo acontece, por desenho, com o
`approx_percentile` da mediana em `sql/athena/queries/03_avaliacoes_por_utilizador.sql:14`.

**M3. A janela `RANGE BETWEEN CURRENT ROW AND 599 FOLLOWING` nunca foi testada no Athena**
(`sql/athena/analise/10_flag_bots.sql:42`). Está assinalado "a confirmar" no próprio ficheiro.
Só a emulação no DuckDB foi corrida.

**M4. `sql/10_flag_bots.sql` continua a ser um esqueleto.** A regra real está em
`sql/analise/10_flag_bots.sql`. Dois ficheiros com o mesmo nome e o comentário "as regras vão ser
definidas pelo Luís" (linha 2) confundem quem lê, e o `README.md:157-158` só fala do esqueleto.
Sugestão: no cabeçalho do esqueleto, apontar para `sql/analise/10_flag_bots.sql`.

**M5. Cada corrida altera ficheiros versionados.** Com `run_pipeline.py --dataset small` ficam
modificados 8 ficheiros:
- 3 CSV globais a que se acrescentam linhas;
- os tempos no `analises_relatorio.md` e no `analises_resumo.csv`;
- o último dígito dos floats em `distribuicao.csv` e `grupos_atividade.csv` (ordem das somas
  paralelas; já documentado em `docs/validacao_queries_colega.md`, 13.1);
- o PNG `09_top_tags.png`.

O `5e607be` acrescentou 5 corridas repetidas do small. Hoje o `results/pipeline_runs.csv` tem 36
linhas do small e o `results/benchmarks.csv` tem 80. Não é um erro, mas suja a árvore de trabalho e
dilui a evidência. Sugestões: no relatório, usar só a corrida mais recente de cada dataset; e
arredondar as frações a, por exemplo, 12 casas antes do `COPY`.

**M6. Resultados por utilizador versionados.** `results/{small,1m}/analises/10_flag_bots.csv` e as
cópias em `athena_emulado/` têm uma linha por utilizador (850 KB no 1M). No 32M seriam 200 948
linhas, dezenas de MB. Já identificado (`proximos_passos.md:76`). É preciso decidir antes de
correr as análises no 32M.

**M7. `cloud_pipeline.py:56-73`: a frescura de `data/cloud/` mede-se pela data do manifesto, que é
um ficheiro versionado.** Um `git checkout` ou `pull` que altere o `reports/cloud_manifest_<ds>.md`
muda a data do ficheiro, e o script pode considerar atualizada uma pasta feita com dados antigos.
É um caso raro. Por segurança, corre-se `prepare_cloud.py` à mão antes do passo `cloud`.

**M8. `cloud_pipeline.py:147`: o upload compara só o tamanho dos ficheiros.** Já documentado
(`proximos_passos.md:110`). Um Parquet regenerado com o mesmo tamanho não seria reenviado.

**M9. `.gitignore`: faltam `dados/` e `lab_resultados.zip`**, as pastas do notebook do Luís. Já
conhecido (`proximos_passos.md:109`). Para a tarefa do IMDb, convém acrescentar também `*.tsv.gz` e
`*.zip`. O `data/` já cobre `data/imdb/`, mas esta é uma proteção extra.

**M10. Caminho absoluto do Mac em `proximos_passos.md:26-27`** (`git clone ... "/Users/..."`).
Não é código, mas expõe o nome de utilizador e só funciona na tua máquina.

**M11. README, pormenores.**
- `README.md:87` recomenda Python 3.12, mas a versão testada é a 3.13 (`README.md:92`).
- A tabela "Tecnologias" (`README.md:369-377`) não tem AWS S3, Glue e Athena, nem o boto3.
- "Dados" (`README.md:31-43`) só descreve o `ml-latest-small`, e "Perguntas de análise"
  (`README.md:24-29`) só as 4 originais.
- `requirements.txt:9`: o comentário do boto3 não refere o `cloud_pipeline.py`.

**M12. Mensagens de commit.** `5e607be` ("Fase2-cloud_pipleline": gralha e não descreve a
alteração, que só acrescenta resultados) e `9526a0a` ("projecto", grafia anterior ao Acordo
Ortográfico). Como o branch já está publicado, corrigir exigiria reescrever o histórico. Fica só
registado.

## 3. Verificação de atribuição ao Claude (Tarefa 2)

```
git --no-pager log origin/main..fase2-cloud-pipeline --format='%h | %an <%ae> | %cn <%ce>%n%B' \
  | grep -inE "claude|anthropic|co-authored|generated with"
```

Não devolve nada (código de saída 1). Mais verificações:
- nenhum "🤖" nas mensagens;
- os 39 commits têm todos o mesmo autor, Tiago Felgueira;
- os committers são Tiago Felgueira (38) e `GitHub <noreply@github.com>` (1, o `9526a0a`, feito na
  interface web do GitHub);
- nenhum `noreply@anthropic.com`;
- a mesma procura em todos os branches dá 0 resultados.

## 4. Proposta de correções (a aprovar)

Por ordem, um commit por alteração. Nada disto foi feito.

1. I3, I4, I5, M11: atualizar o README (estrutura, passo `analises`, `06_coordenacao.py`, análises
   e bots marcadas como provisórias, Tecnologias).
2. I6, M10: atualizar o `proximos_passos.md` e a secção "Estado do git" do resumo.
3. M9: acrescentar ao `.gitignore` `dados/`, `lab_resultados.zip`, `*.tsv.gz` e `*.zip`.
4. M4: no cabeçalho de `sql/10_flag_bots.sql`, apontar para `sql/analise/10_flag_bots.sql`.
5. M1: desempate por `movieid` em `sql/athena/queries/04_top_filmes.sql`. Altera uma query da fase 2
   já medida no Athena; o n.º de linhas não muda.
6. I1: decisão sobre o `bdf_inventario.md`.
7. I2: apagar o `credentials` da pasta do projeto. É uma ação tua, fora do git.

M2, M3, M5, M6, M7, M8 e M12 ficam registados, sem alteração proposta agora.

## 5. Correções aplicadas (15/11/2026)

Aprovadas no ponto de paragem 1. Um commit por alteração, no `fase2-cloud-pipeline`, sem push.

| Ponto | Estado | Commit |
|---|---|---|
| I3, I4, I5, M11 (README) | Corrigido | `README: estrutura do repositório, passo analises, …` |
| I6, M10 (`proximos_passos.md`) | Corrigido | `proximos_passos: estado a 15/11 …` |
| I6 (resumo do projeto) | Corrigido | `Resumo do projeto: estado do git a 15/11 …` |
| M9 (`.gitignore`) | Corrigido | `gitignore: dados/ e lab_resultados.zip …` |
| M4 (esqueleto `sql/10_flag_bots.sql`) | Corrigido | `sql/10_flag_bots.sql: cabeçalho aponta …` |
| M1 (desempate na query 04 do Athena) | Corrigido; ainda não corrido no Athena | `Athena: desempate por movieid …` |
| I1 (`bdf_inventario.md`) | Por decidir | — |
| I2 (`credentials` na pasta do projeto) | Ação do Tiago, fora do git | — |

### Legibilidade do código

Revisão pedida para que o código seja simples de ler por alunos do 1.º ano da pós-graduação e
esteja comentado em português. Os comentários e as docstrings já estavam todos em português.
Alterações:

- `06_coordenacao.py`: o `main` (163 linhas) foi dividido em funções com nome
  (`linha_de_base`, `teste_permutacao`, `rajadas_por_ano`, `detalhe_rajadas`, `top_rajadas`,
  `escrever_relatorio`). Os `lambda` dentro do `agg` do pandas e o `**({...} if ... else {})`
  passaram a passos explícitos. Todas as funções têm docstring.
- `prepare_cloud.py`: o `main` (152 linhas) foi dividido numa função por etapa (cópia,
  partição, CSV e três verificações).
- `05_analises.py`, `athena_setup.py`, `athena_benchmark.py`, `athena_common.py` e
  `cloud_pipeline.py`: regex explicadas; `next(...)` e compreensões com várias condições
  substituídos por ciclos `for`; comentários sobre `**kwargs`, o polling do Athena e o callback do
  upload.

**Os resultados não mudaram.** Antes e depois das alterações corremos, no small e no 1M:
- `05_analises.py --emular-athena` e `06_coordenacao.py --repeticoes 5`: todos os CSV são iguais,
  com tolerância de 1e-9 nos floats, e os relatórios só diferem nos tempos;
- `prepare_cloud.py`: os manifestos são iguais. No 1M, o tamanho de uma partição varia 0,01 MB, mas
  isso também acontece entre corridas do código original, por causa da ordem de escrita;
- `athena_setup.py --dry-run` e `athena_benchmark.py --dry-run`: o SQL enviado é igual.
