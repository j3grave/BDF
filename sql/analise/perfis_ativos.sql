-- perfis_ativos.sql (DuckDB) - por ano, utilizadores ativos com histórico só de inteiros,
-- só de não inteiros ou misto
--
-- Pergunta: entre os utilizadores que avaliaram em cada ano (e com pelo menos 2 avaliações
-- acumuladas até esse ano), quantos usaram até aí só estrelas inteiras, só valores não
-- inteiros (x,5) ou os dois?
--
-- Notas:
-- - o ano é a coluna year de ${ratings} (UTC);
-- - count_if(cond) e janela escrita por extenso, como na versão Athena;
-- - rótulo "Só não inteiros" (um 0,5 não é um "meio ponto" de um inteiro).
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
