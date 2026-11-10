"""Testes da divisão em trechos. A função a implementar está em assistente/chunking.py."""

from assistente.base import Documento
from assistente.chunking import MAX_CARACTERES, SECAO_SEM_TITULO, dividir_por_secao


def doc(corpo: str) -> Documento:
    return Documento(
        id="pt/teste", idioma="pt", fonte="rh", titulo="Teste", rotulo_fonte="Teste",
        url=None, privado=False, corpo=corpo,
    )


def test_uma_secao_por_titulo():
    trechos = dividir_por_secao(doc("## Um\nTexto um.\n\n## Dois\nTexto dois.\n\n## Três\nTexto três."))
    assert [t.secao for t in trechos] == ["Um", "Dois", "Três"]
    assert [t.texto for t in trechos] == ["Texto um.", "Texto dois.", "Texto três."]


def test_texto_antes_do_primeiro_titulo():
    trechos = dividir_por_secao(doc("Introdução.\n\n## Um\nTexto um."))
    assert trechos[0].secao == SECAO_SEM_TITULO
    assert trechos[0].texto == "Introdução."
    assert trechos[1].secao == "Um"


def test_secao_vazia_e_ignorada():
    trechos = dividir_por_secao(doc("## Vazia\n\n   \n## Cheia\nTem texto."))
    assert [t.secao for t in trechos] == ["Cheia"]


def test_ordem_comeca_em_um_e_nao_repete():
    trechos = dividir_por_secao(doc("## A\na\n## B\nb\n## C\nc"))
    assert [t.ordem for t in trechos] == [1, 2, 3]


def test_trecho_carrega_documento_e_titulo():
    trecho = dividir_por_secao(doc("## A\ntexto"))[0]
    assert trecho.documento_id == "pt/teste"
    assert trecho.titulo_documento == "Teste"


def test_secao_longa_e_cortada_entre_paragrafos():
    paragrafo = "Frase de teste com algumas palavras. " * 10  # ~370 caracteres
    corpo = "## Longa\n" + "\n\n".join([paragrafo.strip()] * 6)  # ~2.200 caracteres
    trechos = dividir_por_secao(doc(corpo))
    assert len(trechos) >= 2
    assert all(len(t.texto) <= MAX_CARACTERES for t in trechos)
    assert all(t.secao == "Longa" for t in trechos)
    # nenhum parágrafo foi cortado no meio: cada pedaço é feito de parágrafos inteiros
    for t in trechos:
        for p in t.texto.split("\n\n"):
            assert p == paragrafo.strip()
    assert [t.ordem for t in trechos] == list(range(1, len(trechos) + 1))


def test_base_real_tem_trechos_validos():
    from assistente.base import ler_base

    for d in ler_base():
        trechos = dividir_por_secao(d)
        assert trechos, f"{d.id} não gerou nenhum trecho"
        assert all(len(t.texto) <= MAX_CARACTERES for t in trechos), d.id
