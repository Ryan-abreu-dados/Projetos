-- Cenário: reajuste de 5% no valor das corridas de março a junho.
-- No PostgreSQL um UPDATE não sobrescreve a linha: grava uma versão nova e deixa a
-- antiga como "morta" até o VACUUM limpar. As páginas mexidas perdem a marca de
-- "todas visíveis", e o Index Only Scan do caso 2 volta a consultar a tabela.
UPDATE corridas
SET valor_total = round(valor_total * 1.05, 2)
WHERE iniciada_em >= TIMESTAMP '2025-03-01'
  AND iniciada_em <  TIMESTAMP '2025-07-01';
