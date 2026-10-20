-- A consulta não muda. Com a estimativa certa, o planejador troca para Hash Join.
SELECT m.categoria, count(*) AS corridas, round(avg(c.valor_total), 2) AS ticket_medio
FROM corridas c
JOIN motoristas m ON m.id = c.motorista_id
WHERE c.forma_pagamento = 'pix'
GROUP BY m.categoria
ORDER BY m.categoria;
