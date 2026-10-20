# Prints para o site

Salvar em `src/assets/` do site e adicionar no campo `imagens` do `.mdx`.

1. **`explain-tabela-resultados.png`**: a tabela de `resultados/bench.md` renderizada no GitHub.
   - alt: "Tabela com os cinco casos de otimização, tempo antes e depois de cada correção"
   - legenda: "Mediana de 5 execuções com cache quente, 5 milhões de linhas."

2. **`explain-caso1-antes-depois.png`**: terminal com o `EXPLAIN ANALYZE` do caso 1 antes (Seq Scan) e depois (Index Scan). Para gerar, com o banco do compose no ar e os dados carregados:
   ```bash
   psql -h localhost -p 5433 -U postgres -d corridas -f sql/casos/01_funcao_no_filtro/consulta_antes.sql
   ```
   prefixando a consulta com `EXPLAIN (ANALYZE, BUFFERS)`.
   - alt: "Plano de execução do PostgreSQL mostrando Seq Scan antes e Index Scan depois da correção"
   - legenda: "O mesmo filtro, escrito de dois jeitos."

3. **`explain-caso3-estimativa.png`**: trecho do `bench.md` do caso 3 com "Linhas estimadas x reais".
   - alt: "Estimativa do planejador de 1 linha contra 1 milhão de linhas reais antes do ANALYZE"
   - legenda: "Estatística defasada leva a um plano ruim."

4. **`explain-actions.png`**: a aba Actions do repositório Projetos com o workflow `postgres-explain-otimizacao` verde.
   - alt: "Workflow de testes do GitHub Actions concluído com sucesso"
