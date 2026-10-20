"""Os testes precisam dos dois bancos no ar (docker compose up -d --wait origem destino).

Cada sessão de testes recria tudo com uma base pequena.
"""
import pytest

from cdc.config import DESTINO, ORIGEM, conectar
from cdc.preparar import preparar


@pytest.fixture(scope="session", autouse=True)
def ambiente():
    return preparar(clientes=1_000, produtos=100, pedidos=3_000)


@pytest.fixture
def origem():
    with conectar(ORIGEM) as conn:
        yield conn


@pytest.fixture
def destino():
    with conectar(DESTINO) as conn:
        yield conn
