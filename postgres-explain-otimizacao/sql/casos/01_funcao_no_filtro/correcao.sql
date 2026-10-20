-- Correção em duas partes: um índice em iniciada_em e a consulta reescrita como intervalo
-- (consulta_depois.sql). Só o índice não resolve: com date(...) o plano continua Seq Scan.
CREATE INDEX idx_corridas_iniciada_em ON corridas (iniciada_em);
