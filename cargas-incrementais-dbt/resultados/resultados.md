# Resultados (2026-10-20 10:42)

Extrações processadas: 30 dias.

| Medida | Valor |
|---|---|
| Linhas de leitura recebidas | 148.139 |
| Leituras únicas recebidas | 142.631 |
| Linhas na fato | 141.884 |
| Rejeitadas pela regra de validade | 747 |
| Versões de estação (SCD2) | 243 |
| Estações com mais de uma versão | 32 |
| Linhas que um watermark pela hora da medição teria ignorado | 9.989 |

| Idempotência e conferência | Resultado |
|---|---|
| Rodar duas vezes dá o mesmo conteúdo | sim |
| Carga em duas partes (todos os dias menos o último, depois o último) = carga completa | sim |
| --full-refresh = incremental | sim |
| Fato bate com o gabarito do gerador | sim |
| Rejeitadas batem com o gabarito | sim |
| Versões batem com o gabarito | sim |

| Tempo (s) | Total | Só a carga raw |
|---|---|---|
| Carga completa | 14,7 | 3,7 |
| Incremental de 1 dia | 8,7 | 0,2 |
| Repetida sem extração nova | 8,5 | |
| --full-refresh | 7,9 | |

O total inclui a partida do dbt (alguns segundos fixos por execução).