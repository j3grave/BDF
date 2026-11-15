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
