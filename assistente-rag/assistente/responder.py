"""Responde uma pergunta. Por enquanto só o modo "contexto-completo" (Parte 3): a base inteira do
idioma vai no prompt, sem busca. É a linha de base para comparar com o RAG nas próximas partes.
"""

from dataclasses import dataclass, field

from assistente.base import ler_base
from assistente.chunking import dividir_por_secao
from assistente.gemini import RespostaModelo, gerar_resposta
from assistente.prompt import CANARIO, INSTRUCOES, TrechoNumerado, montar_entrada, numerar

MODOS = ("contexto-completo",)


@dataclass
class Resultado:
    pergunta: str
    idioma: str
    situacao: str                  # respondida, sem_informacao, fora_do_escopo, saida_invalida, erro_llm
    resposta: str
    fontes: list[TrechoNumerado] = field(default_factory=list)  # trechos citados que existem
    fontes_desconhecidas: list[str] = field(default_factory=list)  # ids citados que não existem
    trechos_enviados: int = 0
    tokens_entrada: int = 0
    tokens_saida: int = 0
    ms: int = 0
    erro: str = ""


def trechos_do_idioma(idioma: str) -> list[TrechoNumerado]:
    """Todos os trechos da base num idioma, já numerados (t1, t2...)."""
    documentos = [d for d in ler_base() if d.idioma == idioma]
    rotulos = {d.id: d.rotulo_fonte for d in documentos}
    trechos = [t for d in documentos for t in dividir_por_secao(d)]
    return numerar(trechos, rotulos)


def conferir(modelo: RespostaModelo, enviados: list[TrechoNumerado]) -> tuple[str, list, list]:
    """Conferências mínimas da Parte 3 (as completas entram na Parte 6).

    - código-canário na resposta: as instruções vazaram, a resposta é descartada;
    - separa as fontes citadas em válidas (existem entre os trechos enviados) e desconhecidas.
    """
    if CANARIO in modelo.bruto:
        return "saida_invalida", [], []
    por_id = {t.id: t for t in enviados}
    validas = [por_id[i] for i in dict.fromkeys(modelo.fontes) if i in por_id]
    desconhecidas = [i for i in modelo.fontes if i not in por_id]
    return modelo.situacao, validas, desconhecidas


def responder(pergunta: str, idioma: str = "pt", modo: str = "contexto-completo", cliente=None) -> Resultado:
    if modo not in MODOS:
        raise ValueError(f"modo '{modo}' ainda não existe. Modos: {', '.join(MODOS)}")
    enviados = trechos_do_idioma(idioma)
    entrada = montar_entrada(enviados, pergunta)
    try:
        modelo = gerar_resposta(INSTRUCOES, entrada, cliente)
    except Exception as erro:  # rede, cota (429), servidor (5xx), tempo esgotado...
        codigo = getattr(erro, "status_code", None)
        return Resultado(pergunta, idioma, "erro_llm", "", trechos_enviados=len(enviados),
                         erro=f"{type(erro).__name__}" + (f" (HTTP {codigo})" if codigo else ""))

    situacao, fontes, desconhecidas = conferir(modelo, enviados)
    return Resultado(
        pergunta=pergunta,
        idioma=idioma,
        situacao=situacao,
        resposta=modelo.resposta if situacao != "saida_invalida" else "",
        fontes=fontes,
        fontes_desconhecidas=desconhecidas,
        trechos_enviados=len(enviados),
        tokens_entrada=modelo.tokens_entrada,
        tokens_saida=modelo.tokens_saida,
        ms=modelo.ms,
    )
