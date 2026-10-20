"""Cada teste prova, pelo plano de execução, que a correção do caso funcionou."""
import hashlib

import psycopg

from scripts.casos import PASTA_CASOS, _consulta
from scripts.conexao import executar_arquivo
from scripts.gerar_dados import gerar

USA_INDICE_DE_DATA = ("Index Scan (idx_corridas_iniciada_em)",
                      "Bitmap Index Scan (idx_corridas_iniciada_em)",
                      "Index Only Scan (idx_corridas_iniciada_em)")


def test_caso1_intervalo_usa_o_indice(resultados):
    caso = resultados["01_funcao_no_filtro"]
    assert "Seq Scan (corridas)" in caso["antes"]["plano"]
    assert any(no in USA_INDICE_DE_DATA for no in caso["depois"]["plano"])
    # lê bem menos linhas: um dia de 365, e não a tabela toda
    assert caso["depois"]["linhas_lidas_corridas"] < caso["antes"]["linhas_lidas_corridas"] / 50


def test_caso1_so_o_indice_nao_basta(resultados):
    # com date(iniciada_em) no filtro, o índice existe mas não serve
    assert "Seq Scan (corridas)" in resultados["01_funcao_no_filtro"]["antes_com_indice"]["plano"]


def test_caso2_relatorio_sai_so_do_indice(resultados):
    depois = resultados["02_indice_covering"]["depois"]
    assert "Index Only Scan (idx_corridas_relatorio_mensal)" in depois["plano"]
    assert depois["heap_fetches"] == 0


def test_caso3_estimativa_errada_e_corrigida(resultados):
    caso = resultados["03_estatisticas_defasadas"]
    antes, depois = caso["estimativa_antes"], caso["estimativa_depois"]
    assert antes["estimadas"] <= 10 and antes["reais"] >= 1000  # esperava ~1, vieram milhares
    assert antes["reais"] / 2 <= depois["estimadas"] <= antes["reais"] * 2
    assert "Nested Loop" in caso["antes"]["plano"]
    assert "Hash Join" in caso["depois"]["plano"]


def test_caso4_vacuum_limpa_linhas_mortas(resultados):
    caso = resultados["04_update_em_massa_e_vacuum"]
    assert caso["metricas_antes"]["linhas_mortas"] > 0
    assert caso["metricas_depois"]["linhas_mortas"] == 0
    # depois do UPDATE o Index Only Scan some do plano ou precisa ir à tabela
    antes = caso["antes"]
    assert ("Index Only Scan (idx_corridas_relatorio_mensal)" not in antes["plano"]
            or antes["heap_fetches"] > 0)
    depois = caso["depois"]
    assert "Index Only Scan (idx_corridas_relatorio_mensal)" in depois["plano"]
    assert depois["heap_fetches"] == 0
    # VACUUM comum não devolve o espaço ao sistema operacional
    assert caso["metricas_depois"]["tabela_mb"] >= caso["metricas_antes"]["tabela_mb"] * 0.95


def test_caso5_keyset_le_so_uma_pagina(resultados):
    caso = resultados["05_paginacao_offset"]
    assert caso["depois"]["linhas_lidas_corridas"] == 50
    assert caso["antes"]["linhas_lidas_corridas"] > 1000


def test_caso5_offset_e_keyset_devolvem_a_mesma_pagina(conn):
    pasta = PASTA_CASOS / "05_paginacao_offset"
    params = executar_arquivo(conn, pasta / "parametros.sql")[0]
    paginas = []
    for arquivo in ("consulta_antes.sql", "consulta_depois.sql"):
        with psycopg.ClientCursor(conn) as cur:
            cur.execute(_consulta(pasta / arquivo), params)
            paginas.append([linha[0] for linha in cur.fetchall()])
    assert len(paginas[0]) == 50
    assert paginas[0] == paginas[1]


def test_gerador_e_reproduzivel(tmp_path):
    def hash_csv(pasta):
        return hashlib.md5((pasta / "corridas.csv").read_bytes()).hexdigest()

    assert hash_csv(gerar(2_000, tmp_path / "a")) == hash_csv(gerar(2_000, tmp_path / "b"))
