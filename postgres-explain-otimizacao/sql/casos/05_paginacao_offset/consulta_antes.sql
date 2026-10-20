-- Paginação com OFFSET: para entregar 50 linhas o banco percorre e descarta
-- todas as linhas das páginas anteriores. Quanto mais funda a página, mais lento.
SELECT id, iniciada_em, valor_total
FROM corridas
ORDER BY iniciada_em, id
LIMIT 50 OFFSET %(deslocamento)s;
