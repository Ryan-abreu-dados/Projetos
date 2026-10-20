"""Prepara um banco de teste com 100 mil corridas e roda os 5 casos uma vez.

Os testes verificam o PLANO (tipo de nó, linhas lidas, estimativas), não o tempo:
tempo varia de máquina para máquina e no GitHub Actions oscila muito.
"""
import pytest

from scripts.carregar import carregar
from scripts.casos import explicar, listar_casos, resumir, rodar_caso
from scripts.conexao import conectar
from scripts.gerar_dados import gerar

BANCO_TESTE = "corridas_teste"
LINHAS_TESTE = 100_000


@pytest.fixture(scope="session")
def conn(tmp_path_factory):
    with conectar("postgres") as admin:
        admin.execute(f"DROP DATABASE IF EXISTS {BANCO_TESTE}")
        admin.execute(f"CREATE DATABASE {BANCO_TESTE}")
    pasta = gerar(LINHAS_TESTE, tmp_path_factory.mktemp("dados"))
    with conectar(BANCO_TESTE) as conexao:
        carregar(conexao, pasta)
        yield conexao


@pytest.fixture(scope="session")
def resultados(conn):
    saida = {}
    for pasta in listar_casos():
        saida[pasta.name] = rodar_caso(conn, pasta, repeticoes=1)
        if pasta.name == "01_funcao_no_filtro":
            # a consulta antiga, agora com o índice já criado
            saida[pasta.name]["antes_com_indice"] = resumir(explicar(conn, pasta / "consulta_antes.sql"))
    return saida
