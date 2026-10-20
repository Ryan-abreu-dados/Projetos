-- Índice na ordem da paginação. Os dois jeitos de paginar usam o mesmo índice,
-- então a diferença medida vem só da forma da consulta.
CREATE INDEX idx_corridas_paginacao ON corridas (iniciada_em, id);
