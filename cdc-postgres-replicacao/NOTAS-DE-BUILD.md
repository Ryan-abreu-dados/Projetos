# Notas de build

Registro do que aconteceu enquanto eu construía e rodava o projeto. É a fonte da seção "o que deu errado" do README.

## 20/10/2026

- **Ambiente sem Docker.** Medi com dois clusters PostgreSQL 17 criados com `initdb` direto no Windows: origem na porta 5441 com `wal_level=logical`, destino na 5442. Como o servidor de destino precisa achar a origem, rodei com `ORIGEM_VISTA_PELO_DESTINO=host=localhost port=5441 ...`. No Docker, o padrão é `host=origem`. O caminho com Docker e o GitHub Actions ficam para validar no primeiro push.
- **`pg_ctl start` preso no Git Bash.** Subi os servidores com `Start-Process` pelo PowerShell.
- **Simulador, revisão antes de rodar.** `round(preco * %s, 2)` com o fator em `float` vira `double precision`, e `round(double precision, integer)` não existe. Troquei para `%s::numeric`.
- **Reconciliação, revisão antes de rodar.** Percebi que `--corrigir` com a replicação parada copiaria linhas que ainda iam chegar, e a chegada delas daria chave duplicada no destino. Coloquei a trava: sem a sonda chegar em 30 s, a reconciliação não roda.
- **Primeira rodada dos testes: 2 de 11 falharam, os dois por erro meu no teste.**
  - Comparei `Decimal('123.45')` com o float `123.45`. O psycopg devolve `numeric` como `Decimal`.
  - Para simular dado apagado no destino, tentei `DELETE FROM produtos WHERE id = 7`. A chave estrangeira de `itens_pedido` barrou. No destino, as chaves estrangeiras valem para quem escreve à mão, mas não para a replicação, que aplica as mudanças como réplica e não dispara essas checagens. Troquei para apagar um item de pedido.
- **Segunda rodada: 11 de 11.**
- **Rodada completa com a base cheia:** cópia inicial de 370.708 linhas em 2,6 s. O simulador chegou a 85 operações/s contra o alvo de 200: uma conexão só, e cada operação é um commit gravado em disco.
- **Atraso com mediana de 0,3 ms.** Desconfiei e conferi que a sonda consulta mesmo o destino (porta 5442). O número é o tempo de uma consulta: a primeira consulta depois do INSERT já achava a linha. p95 de 3,1 ms e máximo de 26,7 ms.
