-- 10_flag_bots.sql (DuckDB) - utilizadores com comportamento SUSPEITO (nunca "bot confirmado")
--
-- Uma regra mais simples (muita atividade) sinalizava 34% dos utilizadores do small, sobretudo
-- pelo pico normal do registo. Estas regras sinalizam menos de 1%.
--
-- Princípio: sinalizar o que não é fisicamente plausível para um humano, e não "muita
-- atividade". O timestamp regista o momento em que a avaliação foi GRAVADA, não o clique:
-- nos anos 90 o formulário submetia uma página inteira de avaliações com o mesmo segundo.
--
-- Passos:
-- 1. Eventos de submissão: as avaliações com o mesmo (userId, timestamp) formam um evento;
--    k = n.º de avaliações do evento. Todos os ritmos são medidos em eventos, não em avaliações.
-- 2. Submissão em lote (NÃO é bot): utilizador com pelo menos um evento com >= 10 avaliações
--    no mesmo segundo. Casos de referência
--    no small: 191, 429, 99, 163 (anos 90) e 534 (2016).
-- 3. Regra A - ritmo sustentado não humano, fora do registo:
--    - ignora as primeiras 24 h de cada utilizador (registo). Nessas 24 h quase todos avaliam
--      20 ou mais filmes em poucos minutos, porque o site o pede ao criar a conta (ver
--      registo_24h.sql), por isso um pico aí não distingue um bot de uma pessoa;
--    - eventos_10min = n.º de eventos na janela [t, t + 599 s] (janela deslizante de 10 min);
--    - regra_a: max_eventos_10min_apos >= 100, ou seja, um evento a cada 6 s durante 10 min
--      seguidos. O limiar é fixo, igual nos três datasets; o 10_flag_bots_calibracao.sql
--      mostra a distribuição e quantos ficariam sinalizados com outros limiares.
--    Referência: o 610 do small (566 avaliações numa hora, ~4 s cada, quase 6 meses depois
--    do registo) tem de ser sinalizado.
-- 4. Sinais complementares (não classificam sozinhos; contam-se em sinais_complementares):
--    desvio-padrão das notas no 1% mais baixo, % da nota mais frequente no 1% mais alto e %
--    de eventos em lote (k >= 2) no 1% mais alto, entre todos os utilizadores do dataset.
--
-- Saída: uma linha por utilizador (610 no small, 200 948 no 32M). Localmente vai para CSV;
-- no Athena é um CTAS em Parquet (ver a versão Athena), nunca um resultado para o cliente.
-- O 04_analise.py guarda-a na tabela temporária ${flag_bots}, usada por
-- 10_flag_bots_calibracao.sql e eventos.sql.
--
-- Parâmetros: ${ratings}
WITH lim AS (SELECT 86400 AS registo_s,           -- primeiras 24 h de cada utilizador
                    100   AS limiar_regra_a,       -- eventos em 10 min depois do registo
                    10    AS lote_min_avaliacoes), -- avaliações no mesmo segundo
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
     -- Limiares dos sinais complementares, calculados a partir da distribuição do próprio dataset
     limiares_c AS (SELECT quantile_cont(desvio_notas, 0.01)     AS limiar_desvio_baixo,
                           quantile_cont(pct_nota_modal, 0.99)   AS limiar_modal_alto,
                           quantile_cont(pct_eventos_lote, 0.99) AS limiar_lote_alto
                    FROM base),
     f AS (SELECT b.*, l.limiar_regra_a,
                  COALESCE(b.max_eventos_10min_apos >= l.limiar_regra_a, false)                               AS regra_a,
                  b.max_avaliacoes_mesmo_segundo >= l.lote_min_avaliacoes                                     AS submissao_lote,
                  CASE WHEN b.desvio_notas <= c.limiar_desvio_baixo THEN 1 ELSE 0 END
                    + CASE WHEN b.pct_nota_modal >= c.limiar_modal_alto THEN 1 ELSE 0 END
                    + CASE WHEN b.pct_eventos_lote >= c.limiar_lote_alto THEN 1 ELSE 0 END                    AS sinais_complementares
           FROM base b CROSS JOIN limiares_c c CROSS JOIN lim l)
SELECT userId, avaliacoes, eventos,
       strftime(epoch_ms(primeiro_ts * 1000), '%Y-%m-%d') AS primeiro_dia,
       strftime(epoch_ms(ultimo_ts * 1000), '%Y-%m-%d')   AS ultimo_dia,
       eventos_registo, eventos_apos_registo, mediana_intervalo_apos_s, max_eventos_10min_apos, limiar_regra_a,
       max_avaliacoes_mesmo_segundo, pct_eventos_lote, desvio_notas, pct_nota_modal,
       regra_a, submissao_lote, sinais_complementares,
       CASE WHEN regra_a THEN 'suspeito (regra A)'
            WHEN submissao_lote THEN 'submissão em lote'
            ELSE 'sem sinais' END AS classificacao
FROM f
ORDER BY userId;
