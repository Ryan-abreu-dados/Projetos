"""Testes rápidos, sem dbt: contrato de colunas, alerta por webhook e gerador."""
import hashlib
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from pipeline.alerta import enviar_alerta
from pipeline.checar_schema import ErroDeSchema, checar
from pipeline.gerar_extracoes import gerar

REGRA = {"obrigatorias": {"a": "VARCHAR", "b": "INTEGER"}, "opcionais": {"c": "DOUBLE"}}


def escrever(tmp_path, cabecalho):
    arquivo = tmp_path / "arquivo.csv"
    arquivo.write_text(",".join(cabecalho) + "\n", encoding="utf-8")
    return arquivo


def test_contrato_aceita_colunas_conhecidas_na_ordem_do_arquivo(tmp_path):
    assert list(checar(escrever(tmp_path, ["b", "a", "c"]), REGRA)) == ["b", "a", "c"]


def test_contrato_recusa_coluna_faltando(tmp_path):
    with pytest.raises(ErroDeSchema, match="faltam"):
        checar(escrever(tmp_path, ["a"]), REGRA)


def test_contrato_recusa_coluna_nova(tmp_path):
    with pytest.raises(ErroDeSchema, match="fora do contrato"):
        checar(escrever(tmp_path, ["a", "b", "x"]), REGRA)


def test_alerta_chega_no_webhook(monkeypatch):
    recebidos = []

    class Receptor(BaseHTTPRequestHandler):
        def do_POST(self):
            recebidos.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(204)
            self.end_headers()

        def log_message(self, *args):
            pass

    servidor = HTTPServer(("127.0.0.1", 0), Receptor)
    threading.Thread(target=servidor.handle_request, daemon=True).start()
    monkeypatch.setenv("ALERTA_WEBHOOK_URL", f"http://127.0.0.1:{servidor.server_port}/")
    enviar_alerta("Teste", "detalhe")
    servidor.server_close()
    assert recebidos and "Teste" in recebidos[0]["text"]


def test_gerador_e_reproduzivel(tmp_path):
    def hash_pasta(pasta):
        h = hashlib.md5()
        for arquivo in sorted((pasta / "extracoes").rglob("*.csv")):
            h.update(arquivo.read_bytes())
        return h.hexdigest()

    gerar(dias=3, quantidade_estacoes=5, pasta=tmp_path / "a")
    gerar(dias=3, quantidade_estacoes=5, pasta=tmp_path / "b")
    assert hash_pasta(tmp_path / "a") == hash_pasta(tmp_path / "b")
