"""Gera os dados sintéticos de corridas de táxi com DuckDB e grava em CSV.

Uso: python -m scripts.gerar_dados --linhas 5000000

DuckDB aqui é só o gerador: escreve milhões de linhas em segundos usando SQL.
Com uma thread e semente fixa, a mesma quantidade de linhas gera os mesmos dados.
"""
import argparse
import time
from pathlib import Path

import duckdb

PASTA_PADRAO = Path(__file__).resolve().parent.parent / "dados"


def gerar(linhas: int, pasta: Path = PASTA_PADRAO, semente: float = 0.42) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("SET threads = 1")  # random() só é reproduzível com uma thread
    con.execute(f"SELECT setseed({semente})")

    # 260 zonas, cada uma numa região
    con.execute(f"""
        COPY (
            SELECT z AS id,
                   'Zona ' || lpad(z::VARCHAR, 3, '0') AS nome,
                   ['Centro', 'Norte', 'Sul', 'Leste', 'Oeste'][1 + z % 5] AS regiao
            FROM range(1, 261) t(z)
        ) TO '{(pasta / "zonas.csv").as_posix()}' (HEADER)
    """)

    # 20 mil motoristas, a maioria na categoria comum
    con.execute(f"""
        COPY (
            SELECT m AS id,
                   CASE WHEN r < 0.75 THEN 'comum' WHEN r < 0.95 THEN 'executivo' ELSE 'premium' END AS categoria,
                   DATE '2020-01-01' + CAST(floor(random() * 1800) AS INTEGER) AS cadastrado_em
            FROM (SELECT m, random() AS r FROM range(1, 20001) t(m))
        ) TO '{(pasta / "motoristas.csv").as_posix()}' (HEADER)
    """)

    # Corridas de 2025. Poucas zonas concentram muitas corridas (pow enviesa o sorteio),
    # 70% das corridas caem em horário comercial e a duração tem cauda longa.
    # Ordeno por horário porque numa base real as corridas chegam em ordem de tempo.
    con.execute(f"""
        COPY (
            WITH base AS (
                SELECT
                    1 + CAST(floor(random() * 20000) AS INTEGER) AS motorista_id,
                    1 + CAST(floor(pow(random(), 2.5) * 260) AS INTEGER) AS zona_origem_id,
                    1 + CAST(floor(pow(random(), 2.5) * 260) AS INTEGER) AS zona_destino_id,
                    TIMESTAMP '2025-01-01'
                      + to_days(CAST(floor(random() * 365) AS INTEGER))
                      + to_hours(CASE WHEN random() < 0.7 THEN 7 + CAST(floor(random() * 13) AS INTEGER)
                                      ELSE CAST(floor(random() * 24) AS INTEGER) END)
                      + to_seconds(CAST(floor(random() * 3600) AS INTEGER)) AS iniciada_em,
                    greatest(3, CAST(round(exp(2.3 + random() * 1.4)) AS INTEGER)) AS duracao_min,
                    random() AS r_dist,
                    random() AS r_pag,
                    random() AS r_aval
                FROM range({int(linhas)})
            ),
            com_distancia AS (
                SELECT *, round(duracao_min * 0.45 * (0.6 + r_dist * 0.8), 2) AS distancia_km
                FROM base
            )
            SELECT
                row_number() OVER (ORDER BY iniciada_em, motorista_id, zona_origem_id, r_dist) AS id,
                motorista_id, zona_origem_id, zona_destino_id, iniciada_em, duracao_min,
                distancia_km,
                round(5 + distancia_km * 2.5 + duracao_min * 0.4, 2) AS valor_total,
                CASE WHEN r_pag < 0.72 THEN 'cartao' ELSE 'dinheiro' END AS forma_pagamento,
                CASE WHEN r_aval < 0.2 THEN NULL ELSE 1 + CAST(floor(r_aval * 5) AS INTEGER) % 5 END AS avaliacao
            FROM com_distancia
            ORDER BY id
        ) TO '{(pasta / "corridas.csv").as_posix()}' (HEADER)
    """)
    con.close()
    return pasta


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--linhas", type=int, default=5_000_000)
    args = parser.parse_args()
    inicio = time.perf_counter()
    gerar(args.linhas)
    print(f"{args.linhas:,} corridas geradas em {time.perf_counter() - inicio:.1f} s")
