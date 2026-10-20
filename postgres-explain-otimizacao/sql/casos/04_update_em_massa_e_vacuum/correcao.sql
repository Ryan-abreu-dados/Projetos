-- VACUUM remove as versões mortas e devolve a marca de "todas visíveis" às páginas.
-- Ele não encolhe o arquivo da tabela: o espaço fica livre para os próximos INSERT/UPDATE.
VACUUM (ANALYZE) corridas;

-- Prevenção: religo o autovacuum com limites menores. O padrão só dispara quando 20%
-- da tabela mudou; numa tabela de milhões de linhas isso demora demais.
ALTER TABLE corridas SET (
    autovacuum_enabled = true,
    autovacuum_vacuum_scale_factor = 0.02,
    autovacuum_analyze_scale_factor = 0.01
);
