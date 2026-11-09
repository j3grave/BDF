# BDF 2026 — MovieLens: próximos passos

Estado em 08/11/2026. O pipeline local e a fase cloud correm cada um com um só comando e estão testados no small e no 32M. Falta integrar o trabalho no `main`, fechar a validação com o Luís, completar o 32M e preparar as entregas.

| Prioridade | Bloco | Responsável | Estado |
| --- | --- | --- | --- |
| 1 | Fechar e partilhar o código | Tiago | Em curso |
| 2 | Validação das regras e queries | Luís | Por iniciar |
| 3 | Fechar o 32M | Tiago | Por iniciar |
| 4 | Entregas da cadeira | Grupo | Por iniciar |
| 5 | Melhorias opcionais | A definir | Opcional |

---

## 1. Fechar e partilhar o código

O `main` só tem o notebook inicial. O branch `fase2-cloud-pipeline` contém todo o trabalho (fases 1 e 2, queries do Luís, deteção de bots, passo `cloud`), por isso basta um Pull Request.

- [ ] **Desfazer as alterações dos testes** e confirmar que a árvore de trabalho fica limpa:
  ```bash
  git restore results/ reports/
  git status
  ```
- [ ] **Teste do clone limpo**, como se fosse um colega:
  ```bash
  git clone --branch fase2-cloud-pipeline "/Users/tiagovacasflgueira/Desktop/Nova IMS 2 Semestre/Enterprise Data Science Bootcamp/edsb-class06-class07/BDF" /tmp/bdf_teste
  cd /tmp/bdf_teste
  python3.13 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  python run_pipeline.py --dataset small
  python run_pipeline.py --dataset small --steps cloud
  ```
  Critério: termina com "concluído", a validação dá `OK` e o benchmark não tem avisos.
- [ ] **Confirmar que nenhum commit tem co-autoria** antes do push:
  ```bash
  git --no-pager log --format='%h %s%n%b' origin/main..fase2-cloud-pipeline | grep -i claude
  ```
  Critério: não devolve nada.
- [ ] **Push do branch:**
  ```bash
  git push -u origin fase2-cloud-pipeline
  ```
- [ ] **Alinhar o `main` local com o `origin/main`.** Estão divergentes: 4 commits antigos só locais e 6 só no GitHub. Os 4 locais são uploads antigos do GitHub Desktop e podem ser descartados.
- [ ] **Abrir um Pull Request** de `fase2-cloud-pipeline` para `main` no GitHub, com pelo menos um colega como revisor.
- [ ] **Merge** depois da revisão. Os branches `fase1-pipeline`, `fase2-cloud-prep` e `integracao-queries-luis` ficam contidos e podem ser arquivados.

---

## 2. Validação pelo Luís

Sem esta validação, a deteção de bots não pode entrar no relatório como resultado final. Os detalhes estão em `docs/validacao_queries_colega.md`, secção 13.

- [ ] **Regras de bots** (`sql/analise/10_flag_bots.sql`):
  - regra A: ritmo sustentado fora do registo, com limiar no quantil p99,9;
  - regra B: registo extremo, com ≥ 100 eventos e intervalo mediano ≤ 2 s;
  - limite de submissão em lote: ≥ 10 avaliações no mesmo segundo;
  - os três sinais complementares.
- [ ] **Limites dos eventos** (`eventos.sql` e `filtros_eventos.sql`): um só conjunto de limites.
- [ ] **Faixas de `grupos_atividade`** (20–49, 50–99, 100–249, 250–999, 1000+).
- [ ] **Opção "só anos completos"** em `evolucao_filmes`.
- [ ] **Notebook oficial:** qual dos três notebooks da raiz fica como referência.
- [ ] **Coordenação entre contas** (`06_coordenacao.py`): aceitar a conclusão atual ("sem evidência de coordenação") ou correr a linha de base estratificada por era (antes e depois de 18/02/2003), com ≥ 800 permutações. Explicar também o caso de 22/05/1998.

---

## 3. Fechar o 32M

É a evidência de escala, o ponto que mais conta na avaliação.

- [ ] **Registar o `ingest` e o `parquet` do 32M neste repositório.** Correram noutra cópia e faltam no `results/sizes.csv`, incluindo o tempo de conversão:
  ```bash
  python run_pipeline.py --dataset 32m --steps ingest parquet
  ```
  Critério: o `sizes.csv` passa a ter linhas do 32M, com cerca de 218 MB no `ratings` em Parquet e 29 partições.
- [ ] **Decidir onde gravar o `10_flag_bots.csv` do 32M.** Terá 200 948 linhas e dezenas de MB, e o `.gitignore` versiona `results/**/*.csv`.
- [ ] **Correr as análises no 32M** (só depois do ponto 2):
  ```bash
  python scripts/05_analises.py --dataset 32m --emular-athena
  ```
- [ ] **Calibrar a regra A no 32M:** ver a distribuição e o número de sinalizados no p99, p99,5 e p99,9.

---

## 4. Entregas da cadeira

- [ ] **Relatório final.** O resumo do projeto já tem os passos, as queries, os inputs, os outputs e os resultados. Falta adaptá-lo à estrutura pedida no enunciado.
- [ ] **Apresentação.** Bons candidatos:
  - o diagrama do pipeline (fase local e fase cloud);
  - a tabela de MB lidos no Athena (32M): a mesma query lê 877 MB em CSV, 94 MB em Parquet e 4,7 MB em Parquet particionado (186 vezes menos);
  - o custo: o benchmark completo do 32M custou 0,06 USD, 90% dele nas queries sobre CSV;
  - DuckDB local vs Athena: a esta escala o portátil é mais rápido; a vantagem do Athena é escalar sem infraestrutura e cobrar só os dados lidos;
  - a deteção de bots: 0,33% de suspeitos no small e 0,10% no 1M, contra 34% e 47% da regra original;
  - uma demonstração ao vivo no query editor do Athena. Atenção a não mostrar o ID da conta nos nomes dos buckets.
- [ ] **README:**
  - acrescentar o passo `analises` à lista de passos;
  - documentar o `06_coordenacao.py` (corre à mão, fora do pipeline);
  - atualizar a secção "Estrutura do repositório", que ainda só descreve o notebook.

---

## 5. Melhorias opcionais

Só se houver tempo depois dos pontos 1 a 4.

- [ ] `scripts/athena_analises.py`, para correr as 16 análises de `sql/athena/analise/` no Athena. Hoje só foram testadas em emulação no DuckDB.
- [ ] Figuras para o `05_analises.py`, movendo o estilo NOVA IMS do `04_eda.py` para um módulo partilhado.
- [ ] Desempate por `movieId` em `sql/athena/queries/04_top_filmes.sql`, igual à versão DuckDB.
- [ ] Acrescentar `dados/` e `lab_resultados.zip` ao `.gitignore`.
- [ ] Upload do passo `cloud` com comparação por checksum (ETag), além do tamanho.

---

## Regras de trabalho do grupo

- **Commits** sem linhas "Co-Authored-By: Claude" nem "Generated with Claude Code".
- **Testes novos** primeiro no small. O 32M só depois de o small passar.
- **Fase cloud:** cada colega corre-a na sua conta do Learner Lab:
  ```bash
  python run_pipeline.py --dataset small --steps cloud
  ```
  As credenciais copiam-se em cada sessão com `pbpaste > ~/.aws/credentials`. Nunca carregar em **Reset** no Learner Lab, porque apaga os buckets e o catálogo.
- **Nada vai para o repositório com** credenciais, o ID da conta AWS ou dados (CSV, Parquet, `.duckdb`).
