-- Paginação por chave (keyset): "me dá as 50 linhas depois da última que eu vi".
-- O índice vai direto ao ponto e lê só 50 linhas, em qualquer página.
-- A comparação de linha (a, b) > (x, y) bate com a ordem do índice (iniciada_em, id).
SELECT id, iniciada_em, valor_total
FROM corridas
WHERE (iniciada_em, id) > (%(ultima_iniciada_em)s, %(ultimo_id)s)
ORDER BY iniciada_em, id
LIMIT 50;
