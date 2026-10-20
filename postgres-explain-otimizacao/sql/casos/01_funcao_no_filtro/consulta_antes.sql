-- Quantas corridas e qual o ticket médio num dia.
-- date(iniciada_em) aplica uma função na coluna: o planejador não consegue usar
-- um índice comum em iniciada_em e precisa ler a tabela inteira.
SELECT count(*) AS corridas, round(avg(valor_total), 2) AS ticket_medio
FROM corridas
WHERE date(iniciada_em) = DATE '2025-03-10';
