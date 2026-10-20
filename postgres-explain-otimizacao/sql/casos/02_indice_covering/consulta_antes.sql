-- Relatório mensal: corridas e faturamento por zona de origem em março.
-- O índice do caso 1 acha as linhas do mês, mas zona e valor estão só na tabela:
-- para cada linha encontrada no índice o banco ainda visita a página da tabela.
SELECT zona_origem_id, count(*) AS corridas, sum(valor_total) AS faturamento
FROM corridas
WHERE iniciada_em >= TIMESTAMP '2025-03-01'
  AND iniciada_em <  TIMESTAMP '2025-04-01'
GROUP BY zona_origem_id
ORDER BY faturamento DESC;
