# Notas de build

Registro do que aconteceu enquanto eu construía e rodava o projeto. É a fonte da seção "o que deu errado" do README.

## 20/10/2026

- **Ambiente sem Docker.** A máquina onde medi não tinha Docker. Rodei o PostgreSQL 17 direto no Windows, num cluster novo criado com `initdb` na porta 5540, com a mesma configuração do `docker-compose.yml`. O caminho com Docker e o GitHub Actions ficam para validar no primeiro push.
- **`pg_ctl start` preso no terminal.** Pelo Git Bash, o comando não devolvia o prompt (o servidor herdava a saída do terminal). Pelo PowerShell com `Start-Process` funcionou.
- **Primeira rodada com 100 mil linhas: tudo funcionou, mas o caso 4 não fez o que eu esperava.** Depois do `UPDATE` em massa, eu esperava o Index Only Scan com `Heap Fetches` alto. O planejador trocou para Index Scan no índice simples. Ajustei o teste para aceitar os dois sinais.
- **Rodada com 5 milhões:** geração 17,5 s, carga com `COPY` 70,3 s. Benchmark completo em alguns minutos.
- **Caso 2 decepcionou.** O covering leu 6.450 → 2.097 blocos, mas o tempo foi de 149,9 ms para 132,1 ms, dentro da variação (o "depois" foi de 123 ms a 254 ms). Os dados estão gravados em ordem de horário, então o Index Scan já lia páginas vizinhas. Mantive o caso e escrevi isso no README.
- **Caso 4 com 5 milhões:** o Index Scan pós-`UPDATE` leu 536.758 blocos para 423.876 linhas. As versões novas das linhas de março foram gravadas no fim da tabela e a ordem física se perdeu. `VACUUM` zerou 1.670.871 linhas mortas e a tabela continuou com 629,4 MB.
- **Variação alta no notebook.** O "antes" do caso 3 foi de 3,56 s a 8,18 s. Passei a mostrar a faixa ao lado da mediana.
- **Formatação do relatório.** A primeira versão do `bench.md` mostrava o "depois" do caso 5 como `0.0 ms` (arredondamento) e usava ponto como separador decimal. Troquei para duas casas abaixo de 1 ms e formato brasileiro.
- **Índices no fim do benchmark:** 877 MB de índices para 629 MB de tabela, três deles começando por `iniciada_em`.
