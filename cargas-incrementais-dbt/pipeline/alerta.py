"""Alerta de falha: sempre no log; e num webhook se ALERTA_WEBHOOK_URL estiver definida.

O webhook é opcional e fica fora do repositório (variável de ambiente ou secret
do GitHub). O corpo manda o texto em "text" (Slack) e em "content" (Discord).
"""
import json
import os
import sys
import urllib.request


def enviar_alerta(titulo: str, detalhe: str) -> None:
    print(f"[ALERTA] {titulo}: {detalhe}", file=sys.stderr, flush=True)
    url = os.getenv("ALERTA_WEBHOOK_URL")
    if not url:
        return
    mensagem = f"{titulo}\n{detalhe}"
    corpo = json.dumps({"text": mensagem, "content": mensagem[:1900]}).encode("utf-8")
    pedido = urllib.request.Request(url, data=corpo, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(pedido, timeout=10)
    except OSError as erro:  # falha no alerta não pode esconder a falha original
        print(f"[ALERTA] não consegui enviar o webhook: {erro}", file=sys.stderr)
