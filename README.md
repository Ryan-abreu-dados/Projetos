# Projetos de engenharia de dados

> Projetos pessoais que recriam, com dados sintéticos, técnicas que uso no trabalho. Não contêm código nem dados de nenhuma empresa.

Cada pasta é um projeto independente, com README próprio, testes e `docker compose up` para rodar tudo.

| Projeto | O que mostra | Testes |
|---|---|---|
| [cdc-postgres-replicacao](cdc-postgres-replicacao) | Replicação incremental (CDC) entre dois PostgreSQL com replicação lógica: atraso medido, destino parado, conexão derrubada, conflitos e reconciliação por md5 | [![cdc](https://github.com/Ryan-abreu-dados/Projetos/actions/workflows/cdc.yml/badge.svg)](https://github.com/Ryan-abreu-dados/Projetos/actions/workflows/cdc.yml) |
| [cargas-incrementais-dbt](cargas-incrementais-dbt) | Cargas incrementais idempotentes com dbt e DuckDB: watermark, upsert, deduplicação, SCD tipo 2 e contrato de colunas | [![cargas](https://github.com/Ryan-abreu-dados/Projetos/actions/workflows/cargas.yml/badge.svg)](https://github.com/Ryan-abreu-dados/Projetos/actions/workflows/cargas.yml) |
| [postgres-explain-otimizacao](postgres-explain-otimizacao) | Cinco consultas lentas em 5 milhões de linhas, diagnosticadas com EXPLAIN ANALYZE e medidas antes e depois | [![explain](https://github.com/Ryan-abreu-dados/Projetos/actions/workflows/explain.yml/badge.svg)](https://github.com/Ryan-abreu-dados/Projetos/actions/workflows/explain.yml) |

Ferramentas: PostgreSQL 17, Python, dbt, DuckDB, Docker e GitHub Actions.

## English

Personal data engineering projects that recreate, with synthetic data, techniques I use at work. No company code or data. Each folder is a standalone project with its own README (English summary at the end), tests and a one-command `docker compose up`.
