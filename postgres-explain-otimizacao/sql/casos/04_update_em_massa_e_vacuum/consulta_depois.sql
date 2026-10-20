-- A consulta não muda. Depois do VACUUM, Heap Fetches volta a zero.
SELECT zona_origem_id, count(*) AS corridas, sum(valor_total) AS faturamento
FROM corridas
WHERE iniciada_em >= TIMESTAMP '2025-03-01'
  AND iniciada_em <  TIMESTAMP '2025-04-01'
GROUP BY zona_origem_id
ORDER BY faturamento DESC;
