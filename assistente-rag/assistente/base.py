"""Leitura da base de conhecimento: os arquivos Markdown de conhecimento/."""

from dataclasses import dataclass
from pathlib import Path

import yaml

PASTA = Path(__file__).resolve().parent.parent / "conhecimento"
OBRIGATORIOS = ("fonte", "titulo", "rotulo_fonte", "atualizado")
FONTES = ("curriculo", "site", "rh", "documento")


@dataclass(frozen=True)
class Documento:
    id: str            # ex.: "pt/projetos"
    idioma: str        # "pt" ou "en"
    fonte: str
    titulo: str
    rotulo_fonte: str  # o que aparece embaixo da resposta
    url: str | None
    privado: bool      # True quando veio de conhecimento/privado/
    corpo: str         # o texto depois do cabeçalho


def ler_documento(caminho: Path, idioma: str, privado: bool = False) -> Documento:
    """Lê um arquivo Markdown com cabeçalho YAML entre linhas '---'."""
    texto = caminho.read_text(encoding="utf-8")
    if not texto.startswith("---\n"):
        raise ValueError(f"{caminho}: falta o cabeçalho (---) no começo do arquivo")
    _, cabecalho, corpo = texto.split("---\n", 2)
    dados = yaml.safe_load(cabecalho) or {}

    faltando = [c for c in OBRIGATORIOS if not dados.get(c)]
    if faltando:
        raise ValueError(f"{caminho}: faltam os campos {', '.join(faltando)}")
    if dados["fonte"] not in FONTES:
        raise ValueError(f"{caminho}: fonte '{dados['fonte']}' não é uma de {FONTES}")

    return Documento(
        id=f"{idioma}/{caminho.stem}",
        idioma=idioma,
        fonte=dados["fonte"],
        titulo=dados["titulo"],
        rotulo_fonte=dados["rotulo_fonte"],
        url=dados.get("url"),
        privado=privado,
        corpo=corpo.strip(),
    )


def ler_base(pasta: Path = PASTA) -> list[Documento]:
    """Lê todos os documentos de pt/, en/ e, se existir, privado/pt e privado/en."""
    documentos = []
    for idioma in ("pt", "en"):
        for caminho in sorted((pasta / idioma).glob("*.md")):
            documentos.append(ler_documento(caminho, idioma))
        for caminho in sorted((pasta / "privado" / idioma).glob("*.md")):
            documentos.append(ler_documento(caminho, idioma, privado=True))
    return documentos
