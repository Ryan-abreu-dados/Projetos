# Assistente de IA do portfólio (RAG)

> Em construção. Um chat no site do Ryan Abreu que responde perguntas de recrutadores usando só uma base
> de conhecimento escrita e revisada por ele. Projeto de aprendizado de RAG (busca + modelo de linguagem).

**Pilha planejada:** Python 3.12 · FastAPI · Gemini API (`gemini-3.5-flash-lite`, `gemini-embedding-2`) ·
PostgreSQL com pgvector e busca por texto (Supabase) · Vercel.

## Estado

| Parte | O que entrega | Estado |
|---|---|---|
| 1 | Base de conhecimento em Markdown e divisão em trechos | em andamento |
| 2 | Chat no site com perguntas prontas | a fazer |
| 3 | Primeira resposta com o Gemini, sem RAG, e conjunto de avaliação | a fazer |
| 4 | Embeddings, busca por semelhança e limiar calibrado | a fazer |
| 5 | Busca híbrida (vetor + texto) no PostgreSQL | a fazer |
| 6 | Filtros, regras e conferência da saída | a fazer |
| 7 | API no ar | a fazer |
| 8 | Chat completo no site | a fazer |
| 9 | Avaliação final e resultados | a fazer |

## Rodar

```bash
uv sync
uv run pytest -q
uv run python -m assistente listar-trechos
```

## Base de conhecimento

`conhecimento/pt/` e `conhecimento/en/`: um arquivo por assunto, com cabeçalho (fonte, título, rótulo da
fonte, link) e uma seção `##` por pergunta ou tema. Fatos privados ficam em `conhecimento/privado/`,
fora do git. O telefone não entra na base.

Base atual (PT): 11 documentos, 45 trechos.
