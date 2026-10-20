# Resultados (2026-10-20 10:49)

Máquina: notebook Intel Core i5-8265U (4 núcleos, 8 threads), 16 GB RAM, SSD, Windows 11, dois PostgreSQL 17 nativos na mesma máquina.

| Medida | Valor |
|---|---|
| Linhas na carga inicial (4 tabelas) | 370.708 |
| Cópia inicial para o destino | 2,6 s |
| Carga simulada | 85,2 operações/s (alvo 200) |
| Atraso da origem ao destino, mediana | 0,3 ms |
| Atraso p95 / p99 / máximo | 3,1 / 3,3 / 26,7 ms |
| Sondas que não chegaram em 10 s | 0 de 300 |
| Destino parado | 30 s, com 2.736 operações na origem |
| WAL retido no slot: antes → fim da pausa | 1,77 MB → 3,39 MB |
| Tempo para o destino alcançar a origem depois de religado | 0,72 s |
| Volta depois de derrubar a conexão | 2,47 s |
| Divergências depois das falhas | 0 |
| Linhas alteradas direto no destino | 3 |
| Encontradas pela reconciliação | 3 (ids [101, 202, 303]) |
| Divergências depois de corrigir | 0 |