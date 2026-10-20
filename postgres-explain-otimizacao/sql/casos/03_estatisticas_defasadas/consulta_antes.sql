-- Corridas pagas com pix por categoria de motorista.
-- As estatísticas ainda dizem que só existem "cartao" e "dinheiro". Para um valor que
-- não aparece nelas, o planejador estima 1 linha e escolhe um Nested Loop: uma busca
-- no índice de motoristas para cada corrida. Na prática vêm centenas de milhares.
SELECT m.categoria, count(*) AS corridas, round(avg(c.valor_total), 2) AS ticket_medio
FROM corridas c
JOIN motoristas m ON m.id = c.motorista_id
WHERE c.forma_pagamento = 'pix'
GROUP BY m.categoria
ORDER BY m.categoria;
