-- Linhas que o filtro do caso devolve. Usado para comparar a estimativa do planejador
-- (EXPLAIN sem ANALYZE) com a contagem real.
SELECT * FROM corridas WHERE forma_pagamento = 'pix';
