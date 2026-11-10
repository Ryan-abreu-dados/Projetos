from assistente.base import ler_base


def test_base_le_todos_os_documentos_pt():
    ids = [d.id for d in ler_base() if d.idioma == "pt"]
    assert "pt/sobre" in ids and "pt/contato" in ids


def test_nenhum_telefone_na_base():
    import re

    for d in ler_base():
        assert not re.search(r"\(?\d{2}\)?\s?9?\d{4}-?\d{4}", d.corpo), f"possível telefone em {d.id}"
