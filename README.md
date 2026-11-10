# Projeto de engenharia de dados

> Projeto pessoal que recria, com dados sintéticos, técnicas que uso no trabalho. Não contêm código nem dados de nenhuma empresa.

O projeto tem README próprio, testes e `docker compose up` para rodar tudo.

| Projeto | O que mostra | Testes |
|---|---|---|
| [cdc-postgres-replicacao](cdc-postgres-replicacao) | Replicação incremental (CDC) entre dois PostgreSQL com replicação lógica: atraso medido, destino parado, conexão derrubada, conflitos e reconciliação por md5 | [![cdc](https://github.com/Ryan-abreu-dados/Projetos/actions/workflows/cdc.yml/badge.svg)](https://github.com/Ryan-abreu-dados/Projetos/actions/workflows/cdc.yml) |
| [assistente-rag](assistente-rag) | Em construção: assistente de IA (RAG) do portfólio, com Gemini, PostgreSQL com pgvector e busca híbrida | — |

Ferramentas: PostgreSQL 17, Python, Docker e GitHub Actions.

## English

Personal data engineering project that recreates, with synthetic data, techniques I use at work. No company code or data. The project has its own README (English summary at the end), tests and a one-command `docker compose up`.
