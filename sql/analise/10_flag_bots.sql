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
