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

    Testes em tests/test_chunking.py. Rode com:  uv run pytest -q
    """
    # 1) Ler linha por linha e separar as seções.
    secoes = []                      # lista de (nome da seção, texto da seção)
    nome_atual = SECAO_SEM_TITULO    # antes do primeiro "##", a seção é a "Visão geral"
    linhas_atuais = []               # linhas da seção que estamos lendo agora

    for linha in documento.corpo.splitlines():
        if linha.startswith("## "):
            # Achou um título: a seção anterior acabou. Guarda ela e começa uma nova.
            secoes.append((nome_atual, "\n".join(linhas_atuais)))
            nome_atual = linha[3:].strip()   # tira os 3 caracteres "## " do começo
            linhas_atuais = []
        else:
            linhas_atuais.append(linha)

    secoes.append((nome_atual, "\n".join(linhas_atuais)))  # a última seção ainda não foi guardada

    # 2) Transformar cada seção em um ou mais trechos.
    trechos = []
    ordem = 0
    for nome, texto in secoes:
        texto = texto.strip()
        if not texto:                # seção vazia: pula
            continue
        for pedaco in _cortar_em_pedacos(texto):
            ordem += 1
            trechos.append(
                Trecho(
                    documento_id=documento.id,
                    ordem=ordem,
                    secao=nome,
                    texto=pedaco,
                    titulo_documento=documento.titulo,
                )
            )
    return trechos


def _cortar_em_pedacos(texto: str) -> list[str]:
    """Corta um texto longo em pedaços de até MAX_CARACTERES, sempre entre parágrafos."""
    paragrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
    pedacos = []
    atual = ""
    for p in paragrafos:
        junto = p if not atual else atual + "\n\n" + p
        if len(junto) <= MAX_CARACTERES:
            atual = junto            # ainda cabe: junta no pedaço atual
        else:
            if atual:
                pedacos.append(atual)  # não cabe: fecha o pedaço atual
            atual = p                  # e começa outro com este parágrafo
    if atual:
        pedacos.append(atual)
    return pedacos
