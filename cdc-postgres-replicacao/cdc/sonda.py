"""Sonda: grava uma linha na origem e espera ela aparecer no destino."""
import time

import psycopg


def enviar(origem: psycopg.Connection) -> int:
    return origem.execute("INSERT INTO sonda_latencia DEFAULT VALUES RETURNING id").fetchone()[0]


def esperar(destino: psycopg.Connection, sonda_id: int, limite_s: float = 30.0,
            intervalo_s: float = 0.002) -> float | None:
    """Segundos até a sonda chegar ao destino, ou None se passar do limite."""
    inicio = time.perf_counter()
    while time.perf_counter() - inicio < limite_s:
        if destino.execute("SELECT 1 FROM sonda_latencia WHERE id = %s", [sonda_id]).fetchone():
            return time.perf_counter() - inicio
        time.sleep(intervalo_s)
    return None


def sincronizar(origem: psycopg.Connection, destino: psycopg.Connection, limite_s: float = 30.0) -> float | None:
    """Espera o destino alcançar tudo o que a origem gravou até agora."""
    return esperar(destino, enviar(origem), limite_s)
