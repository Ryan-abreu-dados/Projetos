"""Chamada ao Gemini pela Interactions API, com saída estruturada (JSON).

Conferido no SDK google-genai 3.2 e em aistudio.google.com/docs/interactions-overview (12/11/2026):
- client.interactions.create(model=, input=, system_instruction=, store=, generation_config=,
  response_format=, timeout=)  -> o timeout é em segundos.
- O texto da resposta fica em interacao.output_text; os tokens, em interacao.usage
  (total_input_tokens, total_output_tokens).
- Erros HTTP sobem como exceções com o atributo status_code. O próprio SDK repete a chamada
  em 408, 409, 429 e 5xx; aqui limitamos a UMA nova tentativa (attempts=2), só em 429 e 5xx.
"""

import json
import time
from dataclasses import dataclass, field

from google import genai
from google.genai import types

from assistente.config import chave_gemini, config

SITUACOES = ("respondida", "sem_informacao", "fora_do_escopo")

# Formato que o modelo é obrigado a seguir. "situacao" vem primeiro de propósito:
# o modelo decide se sabe ANTES de escrever a resposta.
ESQUEMA_RESPOSTA = {
    "type": "object",
    "properties": {
        "situacao": {"type": "string", "enum": list(SITUACOES)},
        "resposta": {"type": "string"},
        "fontes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["situacao", "resposta", "fontes"],
}


@dataclass
class RespostaModelo:
    situacao: str                  # uma de SITUACOES, ou "saida_invalida"
    resposta: str
    fontes: list[str] = field(default_factory=list)   # ids como "t3"
    tokens_entrada: int = 0
    tokens_saida: int = 0
    ms: int = 0                    # tempo da chamada, em milissegundos
    bruto: str = ""                # o texto exatamente como veio do modelo


def criar_cliente() -> genai.Client:
    return genai.Client(
        api_key=chave_gemini(),
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(
                attempts=2,  # a chamada original + uma nova tentativa
                http_status_codes=[429, 500, 502, 503, 504],
            )
        ),
    )


def interpretar(texto: str) -> tuple[str, str, list[str]]:
    """Confere se o texto é um JSON no formato combinado. Se não for, devolve 'saida_invalida'."""
    try:
        dados = json.loads(texto)
    except (json.JSONDecodeError, TypeError):
        return "saida_invalida", "", []
    if not isinstance(dados, dict):
        return "saida_invalida", "", []
    situacao, resposta, fontes = dados.get("situacao"), dados.get("resposta"), dados.get("fontes")
    if situacao not in SITUACOES or not isinstance(resposta, str) or not isinstance(fontes, list):
        return "saida_invalida", "", []
    return situacao, resposta, [str(f) for f in fontes]


def gerar_resposta(instrucoes: str, entrada: str, cliente: genai.Client | None = None) -> RespostaModelo:
    """Envia as instruções e a entrada ao Gemini e devolve a resposta já interpretada."""
    cfg = config()["modelos"]
    cliente = cliente or criar_cliente()

    inicio = time.perf_counter()
    interacao = cliente.interactions.create(
        model=cfg["resposta"],
        store=False,                          # o Google não guarda a conversa
        system_instruction=instrucoes,
        input=entrada,
        generation_config={
            "thinking_level": cfg["raciocinio"],
            "max_output_tokens": cfg["max_tokens_saida"],
        },
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": ESQUEMA_RESPOSTA,
        },
        timeout=cfg["tempo_max_s"],
    )
    ms = round((time.perf_counter() - inicio) * 1000)

    texto = interacao.output_text or ""
    situacao, resposta, fontes = interpretar(texto)
    uso = interacao.usage
    return RespostaModelo(
        situacao=situacao,
        resposta=resposta,
        fontes=fontes,
        tokens_entrada=(uso.total_input_tokens or 0) if uso else 0,
        tokens_saida=(uso.total_output_tokens or 0) if uso else 0,
        ms=ms,
        bruto=texto,
    )
