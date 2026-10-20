-- Cenário: chega uma carga em massa com uma forma de pagamento que não existia (pix).
-- Desligo o autovacuum só nesta tabela para reproduzir a janela entre o fim da carga
-- e o momento em que o autovacuum rodaria ANALYZE sozinho. Ele volta no caso 4.
ALTER TABLE corridas SET (autovacuum_enabled = false);

SELECT setseed(0.3);

-- Uma carga de 20% do tamanho atual da tabela, toda em janeiro de 2026 e toda em pix.
WITH ultimo AS (
    SELECT max(id) AS id, count(*) AS total FROM corridas
),
novas AS (
    SELECT g, greatest(3, round(exp(2.3 + random() * 1.4)))::int AS duracao
    FROM ultimo, generate_series(1, ultimo.total / 5) AS g
)
INSERT INTO corridas (id, motorista_id, zona_origem_id, zona_destino_id, iniciada_em,
                      duracao_min, distancia_km, valor_total, forma_pagamento, avaliacao)
SELECT ultimo.id + n.g,
       1 + floor(random() * 20000)::int,
       1 + floor(power(random(), 2.5) * 260)::int,
       1 + floor(power(random(), 2.5) * 260)::int,
       TIMESTAMP '2026-01-01' + random() * INTERVAL '31 days',
       n.duracao,
       round(n.duracao * 0.45, 2),
       round(5 + n.duracao * 0.45 * 2.5 + n.duracao * 0.4, 2),
       'pix',
       NULL
FROM novas AS n, ultimo;
