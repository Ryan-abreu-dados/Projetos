-- Escolhe uma página no meio da tabela (40 por cento das linhas já vistas) e guarda a
-- última linha da página anterior, que é o que um app guardaria para pedir a próxima.
WITH alvo AS (
    SELECT (count(*) * 0.4)::bigint AS deslocamento FROM corridas
)
SELECT alvo.deslocamento,
       anterior.iniciada_em AS ultima_iniciada_em,
       anterior.id AS ultimo_id
FROM alvo,
     LATERAL (
         SELECT iniciada_em, id
         FROM corridas
         ORDER BY iniciada_em, id
         OFFSET alvo.deslocamento - 1
         LIMIT 1
     ) AS anterior;
