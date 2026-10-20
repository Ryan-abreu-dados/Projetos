# Prints para o site

Salvar em `src/assets/` do site e adicionar no campo `imagens` do `.mdx`.

1. **`cargas-resultados.png`**: as duas primeiras tabelas de `resultados/resultados.md` renderizadas no GitHub.
   - alt: "Tabela com linhas recebidas, linhas na fato, rejeitadas e as conferências de idempotência todas marcadas como sim"
   - legenda: "Rodar duas vezes, em partes ou do zero dá o mesmo conteúdo."

2. **`cargas-dbt-build.png`**: terminal com o fim do `dbt build` (`PASS=19`). Para gerar: `cd modelos_dbt && dbt build --profiles-dir .` com `DUCKDB_PATH` apontando para `../dados/estacoes.duckdb`, ou o log em `modelos_dbt/logs/dbt.log`.
   - alt: "Saída do dbt build com modelos criados e testes de dados aprovados"
   - legenda: "Modelos e testes de dados na mesma passada."

3. **`cargas-schema-drift.png`**: terminal de `python -m pipeline gerar --drift-a-partir 20` seguido de `python -m pipeline rodar`, mostrando o alerta.
   - alt: "Mensagem de alerta: coluna umidade_pct fora do contrato, carga interrompida no dia 20"
   - legenda: "Coluna nova sem aviso para a carga."

4. **`cargas-actions.png`**: a aba Actions do repositório Projetos com os workflows `cargas-incrementais-dbt` e `cargas-incrementais-agendado` verdes.
   - alt: "Workflows de testes e de pipeline agendado concluídos com sucesso no GitHub Actions"
