# Assistente RAG: instruções para sessões de IA

- **Especificação completa e plano em partes:** `docs/assistente-rag/` do repositório do site
  (`Ryan-abreu-dados/ryanabreu-516e34f2`). Leia o README de lá e a parte em execução antes de mexer.
- **Formato misto:** o Ryan está aprendendo. Tarefas marcadas como dele (ex.: `dividir_por_secao` em
  `assistente/chunking.py`) não devem ser implementadas por você, a menos que ele peça. Explique, dê dicas
  e revise.
- **Nunca inventar fatos sobre o Ryan.** A base (`conhecimento/`) só tem o que está no site ou o que ele
  escreveu. Na dúvida, pergunte.
- **Nada interno da empresa** (números, clientes, tabelas). **Nenhum telefone.** **Nenhuma chave** no
  código, no chat ou no git; `.env` e `conhecimento/privado/` ficam fora do git.
- **Conferir a documentação oficial** (Gemini, Supabase, Vercel) antes de usar nomes de modelos, SDKs e
  parâmetros.
- Português, frases curtas, código comentado em português.

Comandos: `uv run pytest -q` · `uv run python -m assistente listar-trechos`
