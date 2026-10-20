-- O mesmo relatório do caso 2, logo depois do UPDATE em massa.
-- Olhar "Heap Fetches" no plano: é quantas vezes o Index Only Scan teve de ir à tabela.
SELECT zona_origem_id, count(*) AS corridas, sum(valor_total) AS faturamento
FROM corridas
WHERE iniciada_em >= TIMESTAMP '2025-03-01'
  AND iniciada_em <  TIMESTAMP '2025-04-01'
GROUP BY zona_origem_id
ORDER BY faturamento DESC;
