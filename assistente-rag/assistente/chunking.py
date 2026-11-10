"""Divide um documento em trechos (chunks). Regras em docs/assistente-rag/05-base-de-conhecimento.md."""

from dataclasses import dataclass

from assistente.base import Documento

MAX_CARACTERES = 1200
SECAO_SEM_TITULO = "Visão geral"


@dataclass(frozen=True)
class Trecho:
    documento_id: str
    ordem: int         # 1, 2, 3... sem repetir dentro do documento
    secao: str         # o título do "##", ou "Visão geral"
    texto: str         # só o texto, sem o "## título"
    titulo_documento: str


def dividir_por_secao(documento: Documento) -> list[Trecho]:
    """Divide o documento em trechos, um por seção "##".

    Regras:
    1. Cada linha que começa com "## " abre uma seção nova; o resto da linha é o nome da seção.
    2. Texto antes do primeiro "##" vira uma seção chamada SECAO_SEM_TITULO.
    3. Seção sem texto (só espaços ou linhas em branco) é ignorada.
    4. Seção com mais de MAX_CARACTERES é dividida em pedaços de até MAX_CARACTERES, cortando
       sempre entre parágrafos (uma linha em branco separa parágrafos). Todos os pedaços ficam
       com o mesmo nome de seção.
    5. "ordem" começa em 1 e conta todos os trechos do documento, na ordem em que aparecem.
    6. O texto de cada trecho vem sem espaços sobrando no começo e no fim.

    Dica: comece pelas regras 1, 2, 3 e 5. Os testes estão em tests/test_chunking.py.
    Rode com:  uv run pytest -q
    """
    raise NotImplementedError("Tarefa do Ryan (Parte 1)")
