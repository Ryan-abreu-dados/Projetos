"""Dados pequenos para os testes: 10 dias, 30 estações (cada execução do dbt leva alguns segundos)."""
import pytest

from pipeline.gerar_extracoes import gerar
from pipeline.medir import impressao_digital
from pipeline.rodar import rodar

DIAS = 10
ESTACOES = 30


@pytest.fixture(scope="session")
def dados(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("dados")
    gabarito = gerar(dias=DIAS, quantidade_estacoes=ESTACOES, pasta=pasta)
    return pasta, gabarito


@pytest.fixture(scope="session")
def carga_completa(dados, tmp_path_factory):
    """Uma carga completa de referência; outros testes comparam com ela."""
    pasta, _ = dados
    banco = tmp_path_factory.mktemp("bancos") / "completa.duckdb"
    resumo = rodar(banco=banco, pasta_dados=pasta, verbose=False)
    return banco, resumo, impressao_digital(banco)
