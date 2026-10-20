-- Índice covering: a chave continua sendo iniciada_em, e INCLUDE guarda zona e valor
-- dentro do próprio índice. A consulta passa a ser respondida só pelo índice
-- (Index Only Scan), desde que o VACUUM tenha marcado as páginas como visíveis.
-- Custo: o índice fica maior e todo UPDATE em valor_total também atualiza o índice.
CREATE INDEX idx_corridas_relatorio_mensal
    ON corridas (iniciada_em) INCLUDE (zona_origem_id, valor_total);
