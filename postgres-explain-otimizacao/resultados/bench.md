# Resultados do benchmark (2026-10-20 10:27)

- Corridas geradas: 5.000.000
- Máquina: notebook Intel Core i5-8265U (4 núcleos, 8 threads), 16 GB RAM, SSD, Windows 11, PostgreSQL nativo
- PostgreSQL: server_version=17.10, shared_buffers=256MB, work_mem=16MB, max_parallel_workers_per_gather=2, random_page_cost=4, jit=off
- Tempo = mediana de 5 execuções de EXPLAIN ANALYZE com cache quente (a 1ª é descartada).

| Caso | Antes (mediana) | Depois (mediana) | Vezes mais rápido | Faixa antes | Faixa depois | Blocos lidos antes → depois |
|---|---|---|---|---|---|---|
| Função na coluna do filtro | 1,20 s | 3,9 ms | 304,7× | 930,9 ms a 1,54 s | 3,6 ms a 4,1 ms | 52.696 → 186 |
| Relatório mensal com índice covering | 149,9 ms | 132,1 ms | 1,1× | 134,9 ms a 172,2 ms | 123,0 ms a 254,2 ms | 6.450 → 2.097 |
| Estatísticas defasadas depois de carga em massa | 4,89 s | 864,0 ms | 5,7× | 3,56 s a 8,18 s | 798,5 ms a 891,4 ms | 3.062.950 → 63.330 |
| UPDATE em massa e VACUUM | 352,5 ms | 259,2 ms | 1,4× | 288,8 ms a 373,7 ms | 209,4 ms a 332,9 ms | 536.758 → 6.243 |
| Paginação com OFFSET x keyset | 1,35 s | 0,04 ms | 33.768,5× | 1,30 s a 1,64 s | 0,04 ms a 0,06 ms | 35.053 → 4 |

## Função na coluna do filtro

- Plano antes: Aggregate → Gather → Aggregate → Seq Scan (corridas)
- Plano depois: Aggregate → Index Scan (idx_corridas_iniciada_em)
- Linhas tocadas em corridas: 5.000.001 → 13.785
- Heap Fetches: 0 → 0
- Preparar o cenário levou 0,0 s; a correção levou 6,2 s.
- Índices da tabela: 107,1 MB → 211,7 MB.
- Tabela: 411,8 MB → 411,8 MB; linhas mortas: 0 → 0

## Relatório mensal com índice covering

- Plano antes: Sort → Aggregate → Gather Merge → Sort → Aggregate → Index Scan (idx_corridas_iniciada_em)
- Plano depois: Sort → Aggregate → Gather Merge → Sort → Aggregate → Index Only Scan (idx_corridas_relatorio_mensal)
- Linhas tocadas em corridas: 423.876 → 423.876
- Heap Fetches: 0 → 0
- Preparar o cenário levou 0,0 s; a correção levou 9,9 s.
- Índices da tabela: 211,7 MB → 403,8 MB.
- Tabela: 411,8 MB → 411,8 MB; linhas mortas: 0 → 0

## Estatísticas defasadas depois de carga em massa

- Plano antes: Aggregate → Sort → Nested Loop → Gather → Seq Scan (corridas) → Index Scan (motoristas_pkey)
- Plano depois: Aggregate → Gather Merge → Sort → Aggregate → Hash Join → Seq Scan (corridas) → Hash → Seq Scan (motoristas)
- Linhas tocadas em corridas: 6.000.000 → 6.000.000
- Heap Fetches: 0 → 0
- Preparar o cenário levou 36,9 s; a correção levou 0,4 s.
- Índices da tabela: 502,3 MB → 502,3 MB.
- Tabela: 492,0 MB → 492,0 MB; linhas mortas: 0 → 0
- Linhas estimadas x reais: antes 1 x 1.000.000; depois 1.010.351 x 1.000.000

## UPDATE em massa e VACUUM

- Plano antes: Sort → Aggregate → Gather Merge → Sort → Aggregate → Index Scan (idx_corridas_iniciada_em)
- Plano depois: Sort → Aggregate → Gather Merge → Sort → Aggregate → Index Only Scan (idx_corridas_relatorio_mensal)
- Linhas tocadas em corridas: 423.876 → 423.876
- Heap Fetches: 0 → 0
- Preparar o cenário levou 45,9 s; a correção levou 10,4 s.
- Índices da tabela: 696,4 MB → 696,4 MB.
- Tabela: 629,4 MB → 629,4 MB; linhas mortas: 1.670.871 → 0

## Paginação com OFFSET x keyset

- Plano antes: Limit → Index Scan (idx_corridas_paginacao)
- Plano depois: Limit → Index Scan (idx_corridas_paginacao)
- Linhas tocadas em corridas: 2.400.050 → 50
- Heap Fetches: 0 → 0
- Preparar o cenário levou 10,9 s; a correção levou 0,0 s.
- Índices da tabela: 876,7 MB → 876,7 MB.
- Tabela: 629,4 MB → 629,4 MB; linhas mortas: 0 → 0
