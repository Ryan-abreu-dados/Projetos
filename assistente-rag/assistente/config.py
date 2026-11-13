"""Configuração: lê config/config.toml e as variáveis de ambiente (ou o arquivo .env).

Segredos (como GEMINI_API_KEY) nunca ficam no config.toml: vêm do ambiente ou do .env,
que está no .gitignore.
"""

import os
import tomllib
from functools import cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_CONFIG = RAIZ / "config" / "config.toml"
ARQUIVO_ENV = RAIZ / ".env"


@cache
def config() -> dict:
    """Devolve o config.toml como dicionário. Lê o arquivo uma vez só."""
    with open(ARQUIVO_CONFIG, "rb") as f:
        return tomllib.load(f)


def _ler_env(caminho: Path) -> dict[str, str]:
    """Lê um arquivo .env simples: linhas NOME=valor, comentários com #."""
    if not caminho.exists():
        return {}
    valores = {}
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        nome, valor = linha.split("=", 1)
        valores[nome.strip()] = valor.strip().strip('"').strip("'")
    return valores


def variavel(nome: str) -> str | None:
    """Procura primeiro no ambiente, depois no .env. Valor vazio conta como ausente."""
    valor = os.environ.get(nome) or _ler_env(ARQUIVO_ENV).get(nome)
    return valor or None


def chave_gemini() -> str:
    chave = variavel("GEMINI_API_KEY")
    if not chave:
        raise SystemExit(
            "Falta a chave do Gemini. Crie o arquivo .env (copie o .env.example) e preencha "
            "GEMINI_API_KEY, ou defina a variável de ambiente. Nunca cole a chave no código."
        )
    return chave
