"""Atraso da origem ao destino com a loja em movimento.

Uso: python -m cdc.latencia [--amostras 300 --taxa 200]

A cada 100 ms grava uma sonda na origem e mede quanto tempo ela leva para
aparecer no destino (consultando a cada 2 ms). O número inclui o tempo do
próprio INSERT e a granularidade da consulta: é o atraso que um usuário do
banco analítico sentiria, não um número interno do PostgreSQL.
"""
import argparse
import statistics
import time

from cdc import sonda
from cdc.config import DESTINO, ORIGEM, conectar
from cdc.simulador import SimuladorEmSegundoPlano


def percentil(valores: list[float], p: float) -> float:
    ordenados = sorted(valores)
    return ordenados[min(len(ordenados) - 1, int(round(p / 100 * (len(ordenados) - 1))))]


def medir(amostras: int = 300, taxa: float = 200, intervalo_s: float = 0.1) -> dict:
    atrasos_ms = []
    with conectar(ORIGEM) as origem, conectar(DESTINO) as destino:
        with SimuladorEmSegundoPlano(taxa) as sim:
            time.sleep(2)
            for _ in range(amostras):
                atraso = sonda.esperar(destino, sonda.enviar(origem), limite_s=10)
                if atraso is not None:
                    atrasos_ms.append(atraso * 1000)
                time.sleep(intervalo_s)
        taxa_real = sim.operacoes / sim.duracao_s
    return {
        "amostras": amostras,
        "perdidas": amostras - len(atrasos_ms),
        "taxa_alvo_ops_s": taxa,
        "taxa_real_ops_s": round(taxa_real, 1),
        "p50_ms": round(statistics.median(atrasos_ms), 1),
        "p95_ms": round(percentil(atrasos_ms, 95), 1),
        "p99_ms": round(percentil(atrasos_ms, 99), 1),
        "max_ms": round(max(atrasos_ms), 1),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--amostras", type=int, default=300)
    parser.add_argument("--taxa", type=float, default=200)
    args = parser.parse_args()
    print(medir(args.amostras, args.taxa))
