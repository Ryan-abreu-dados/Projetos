# Prints para o site

Salvar em `src/assets/` do site e adicionar no campo `imagens` do `.mdx`.

1. **`cdc-resultados.png`**: a tabela de `resultados/resultados.md` renderizada no GitHub.
   - alt: "Tabela com atraso da replicação, WAL retido com o destino parado, tempo de recuperação e divergências"
   - legenda: "Loja em movimento, destino desligado por 30 s e conexão derrubada."

2. **`cdc-monitor-destino-parado.png`**: terminal com `python -m cdc.monitor` durante uma pausa (antes, rode `ALTER SUBSCRIPTION sub_loja DISABLE;` no destino e `python -m cdc.simulador --segundos 20` em outro terminal). Mostra `slot_ativo: false` e `wal_retido_mb` subindo. Depois, `ALTER SUBSCRIPTION sub_loja ENABLE;`.
   - alt: "Saída do monitor com o slot inativo e o WAL retido na origem crescendo"
   - legenda: "Com o destino parado, a origem guarda o WAL."

3. **`cdc-reconciliacao.png`**: terminal com `python -m cdc.reconciliar` depois de `UPDATE clientes SET cidade = 'x' WHERE id IN (5, 6);` rodado no destino, mostrando os ids divergentes; depois `--corrigir` e uma nova rodada com zero divergências.
   - alt: "Reconciliação listando os ids divergentes entre origem e destino e depois zero divergências"
   - legenda: "Divergência silenciosa: a replicação não acusa, a reconciliação acha."

4. **`cdc-testes.png`**: saída do `python -m pytest -v` com os 11 testes passando, ou a aba Actions do repositório Projetos com o workflow `cdc-postgres-replicacao` verde.
   - alt: "Onze testes de replicação aprovados, incluindo conflito de chave e coluna nova"
