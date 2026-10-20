-- ANALYZE lê uma amostra da tabela e atualiza as estatísticas.
-- Regra que tirei daqui: depois de toda carga em massa, rodar ANALYZE na hora,
-- sem esperar o autovacuum.
ANALYZE corridas;
