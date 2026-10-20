"""Testes do pipeline inteiro: geram extrações, rodam o pipeline e conferem o resultado."""
import csv
import json
import shutil
from datetime import date, timedelta

import duckdb
import pytest

import pipeline.carregar
import pipeline.rodar
from pipeline.checar_schema import CONFIG_PADRAO
from pipeline.gerar_extracoes import gerar
from pipeline.medir import contagens, impressao_digital
from pipeline.rodar import FalhaNoPipeline, rodar

from tests.conftest import DIAS, ESTACOES

INICIO = date(2026, 1, 1)


def consultar(banco, sql):
    con = duckdb.connect(str(banco), read_only=True)
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()


def test_resultado_bate_com_o_gabarito(dados, carga_completa):
    _, gabarito = dados
    banco, _, _ = carga_completa
    numeros = contagens(banco)
    assert numeros["linhas_na_fato"] == gabarito["leituras_validas_unicas"]
    assert numeros["rejeitadas"] == gabarito["leituras_rejeitadas"]
    # chegaram duplicatas e correções, mas a fato tem uma linha por leitura
    assert numeros["linhas_recebidas"] > numeros["linhas_na_fato"] + numeros["rejeitadas"]

    versoes = dict(consultar(banco, "SELECT estacao_id, count(*) FROM analitico.dim_estacoes GROUP BY 1"))
    assert versoes == gabarito["versoes_por_estacao"]

    # cada leitura corrigida ficou com o valor da última correção
    finais = {f"{e}|{m:%Y-%m-%d %H:%M:%S}": t for e, m, t in consultar(
        banco, "SELECT estacao_id, medido_em, temperatura_c FROM analitico.fct_leituras")}
    for chave, temperatura in gabarito["temperatura_final_das_corrigidas"].items():
        assert finais[chave] == temperatura


def test_watermark_pela_hora_da_medicao_perderia_linhas(carga_completa):
    banco, _, _ = carga_completa
    # o pipeline não perdeu nada (teste acima), mas nestes dados um filtro por medido_em perderia
    assert contagens(banco)["perdidas_com_watermark_por_medicao"] > 0


def test_rodar_de_novo_nao_muda_nada(dados, carga_completa):
    pasta, _ = dados
    banco, _, digital = carga_completa
    resumo = rodar(banco=banco, pasta_dados=pasta, verbose=False)
    assert resumo["extracoes_carregadas"] == []
    assert impressao_digital(banco) == digital


def test_carga_em_partes_igual_a_carga_completa(dados, carga_completa, tmp_path):
    pasta, _ = dados
    _, _, digital = carga_completa
    banco = tmp_path / "partes.duckdb"
    rodar(ate=INICIO + timedelta(days=2), banco=banco, pasta_dados=pasta, verbose=False)
    rodar(ate=INICIO + timedelta(days=6), banco=banco, pasta_dados=pasta, verbose=False)
    rodar(banco=banco, pasta_dados=pasta, verbose=False)
    assert impressao_digital(banco) == digital

    # e reconstruir tudo do zero dá o mesmo resultado
    rodar(full_refresh=True, banco=banco, pasta_dados=pasta, verbose=False)
    assert impressao_digital(banco) == digital


def test_queda_no_meio_da_carga_nao_deixa_lixo(dados, carga_completa, tmp_path, monkeypatch):
    pasta, _ = dados
    _, _, digital = carga_completa
    banco = tmp_path / "queda.duckdb"
    chamadas = {"leituras": 0}

    def cair_na_quinta_extracao(etapa):
        if etapa == "depois_de_leituras":
            chamadas["leituras"] += 1
            if chamadas["leituras"] == 5:
                raise RuntimeError("queda simulada no meio da extração")

    monkeypatch.setattr(pipeline.carregar, "_ponto_de_falha", cair_na_quinta_extracao)
    with pytest.raises(RuntimeError):
        rodar(banco=banco, pasta_dados=pasta, verbose=False)

    quinto_dia = INICIO + timedelta(days=4)
    assert consultar(banco, "SELECT max(data_extracao) FROM controle.cargas")[0][0] == quinto_dia - timedelta(days=1)
    for tabela in ("leituras", "estacoes"):
        assert consultar(banco, f"SELECT count(*) FROM raw.{tabela} WHERE _extracao = DATE '{quinto_dia}'")[0][0] == 0

    monkeypatch.undo()
    rodar(banco=banco, pasta_dados=pasta, verbose=False)  # retoma de onde parou
    assert impressao_digital(banco) == digital


def test_coluna_nova_para_a_carga_e_avisa(tmp_path, monkeypatch):
    pasta = tmp_path / "dados"
    gerar(dias=6, quantidade_estacoes=ESTACOES, drift_a_partir=4, pasta=pasta)
    alertas = []
    monkeypatch.setattr(pipeline.rodar, "enviar_alerta", lambda titulo, detalhe: alertas.append((titulo, detalhe)))
    banco = tmp_path / "drift.duckdb"

    with pytest.raises(FalhaNoPipeline):
        rodar(banco=banco, pasta_dados=pasta, verbose=False)
    assert alertas and alertas[0][0] == "Carga interrompida" and "umidade_pct" in alertas[0][1]
    # parou antes do dia 4: os dias 1 a 3 entraram, o 4 não
    assert consultar(banco, "SELECT max(data_extracao) FROM controle.cargas")[0][0] == INICIO + timedelta(days=2)

    # aceitar a coluna no contrato destrava a carga
    contrato = json.loads(CONFIG_PADRAO.read_text(encoding="utf-8"))
    contrato["leituras"]["opcionais"]["umidade_pct"] = "INTEGER"
    contrato_aceito = tmp_path / "schema_esperado.json"
    contrato_aceito.write_text(json.dumps(contrato), encoding="utf-8")
    resumo = rodar(banco=banco, pasta_dados=pasta, contrato_path=contrato_aceito, verbose=False)
    assert len(resumo["extracoes_carregadas"]) == 3
    assert consultar(banco, "SELECT count(umidade_pct) > 0 FROM raw.leituras")[0][0]


def test_teste_de_dados_reprova_e_avisa(dados, tmp_path, monkeypatch):
    pasta_original, _ = dados
    pasta = tmp_path / "dados"
    shutil.copytree(pasta_original, pasta)
    ultimo_dia = pasta / "extracoes" / (INICIO + timedelta(days=DIAS - 1)).isoformat() / "leituras.csv"
    with open(ultimo_dia, "a", newline="", encoding="utf-8") as f:
        # leitura válida de uma estação que não existe no cadastro
        csv.writer(f).writerow(["EST999", "2026-01-10 12:00:00", 25.0, 0.0])

    alertas = []
    monkeypatch.setattr(pipeline.rodar, "enviar_alerta", lambda titulo, detalhe: alertas.append((titulo, detalhe)))
    with pytest.raises(FalhaNoPipeline):
        rodar(banco=tmp_path / "reprova.duckdb", pasta_dados=pasta, verbose=False)
    assert alertas and alertas[0][0] == "dbt build reprovou"
    assert "estacao_versao_id" in alertas[0][1] or "relationships" in alertas[0][1]
