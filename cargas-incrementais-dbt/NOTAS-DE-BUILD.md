# Notas de build

Registro do que aconteceu enquanto eu construía e rodava o projeto. É a fonte da seção "o que deu errado" do README.

## 20/10/2026

- **Gerador, revisão antes de rodar.** Uma correção podia ser entregue no mesmo dia de uma retransmissão da mesma leitura, com valores diferentes. Dentro da extração não haveria como saber qual vale, e o resultado mudaria entre execuções. Mudei para a correção chegar sempre depois do último envio daquela leitura.
- **Primeira execução completa:** 30 extrações, 148.139 linhas, `dbt build` com 19 nós (5 modelos e 14 testes de dados), todos verdes.
- **`python -m dbt.cli.main` dava `RuntimeWarning`** do `runpy`. Troquei para `python -c "from dbt.cli.main import cli; cli()"`, num processo separado. O processo separado também evita o pipeline e o dbt disputarem o arquivo do DuckDB.
- **Medição:** idempotência, carga em partes, `--full-refresh` e gabarito, tudo "sim" na primeira rodada.
- **12 testes passaram de primeira.** Desconfiei e fiz um teste de mutação: troquei o filtro incremental da fato para `medido_em > max(medido_em)`. Só `test_carga_em_partes_igual_a_carga_completa` reprovou. Os testes de carga completa passam mesmo com o filtro errado, porque um lote só não tem atraso. Voltei o filtro.
- **Tempo:** a partida do dbt custa uns 8 s por execução nesta máquina. Carga completa 14,7 s, incremental de 1 dia 8,7 s; só a parte da raw, 3,7 s contra 0,2 s.
- **Terminal do Windows mostrava acentos quebrados** nas mensagens. Configurei a saída para UTF-8 no `__main__`.
- **Cenário de coluna nova** rodado à mão: a carga parou no dia 20 com a mensagem `colunas fora do contrato ['umidade_pct']`, e os dias 1 a 19 ficaram carregados.
