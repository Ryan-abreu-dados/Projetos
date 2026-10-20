-- Mesmo resultado, escrito como intervalo [início do dia, início do dia seguinte).
-- A coluna fica "limpa" do lado esquerdo e o índice pode ser usado.
SELECT count(*) AS corridas, round(avg(valor_total), 2) AS ticket_medio
FROM corridas
WHERE iniciada_em >= TIMESTAMP '2025-03-10'
  AND iniciada_em <  TIMESTAMP '2025-03-11';
