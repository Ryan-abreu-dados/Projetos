"""Confere as colunas de cada CSV contra o contrato em config/schema_esperado.json.

Se faltar coluna obrigatória ou aparecer coluna desconhecida, a carga PARA.
Preferi parar a seguir em frente ignorando a coluna: dado novo que ninguém
avisou costuma ser sinal de que a origem mudou, e vale uma pessoa olhar.
Mudança de tipo (texto onde era número) é pega depois, na leitura do CSV:
o DuckDB recusa o valor e a transação inteira volta.
"""
import csv
import json
from pathlib import Path

CONFIG_PADRAO = Path(__file__).resolve().parent.parent / "config" / "schema_esperado.json"


class ErroDeSchema(Exception):
    """A estrutura do arquivo não bate com o contrato."""


def carregar_contrato(caminho: Path = CONFIG_PADRAO) -> dict:
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def ler_cabecalho(arquivo: Path) -> list[str]:
    with open(arquivo, newline="", encoding="utf-8") as f:
        return next(csv.reader(f))


def checar(arquivo: Path, regra: dict) -> dict[str, str]:
    """Devolve {coluna: tipo} na ordem do arquivo, ou levanta ErroDeSchema."""
    cabecalho = ler_cabecalho(arquivo)
    conhecidas = {**regra["obrigatorias"], **regra.get("opcionais", {})}
    faltando = [c for c in regra["obrigatorias"] if c not in cabecalho]
    novas = [c for c in cabecalho if c not in conhecidas]

    problemas = []
    if faltando:
        problemas.append(f"faltam colunas obrigatórias {faltando}")
    if novas:
        problemas.append(f"colunas fora do contrato {novas} (se forem esperadas, "
                         f"adicione em config/schema_esperado.json, em 'opcionais')")
    if problemas:
        raise ErroDeSchema(f"{arquivo.parent.name}/{arquivo.name}: " + "; ".join(problemas))
    return {c: conhecidas[c] for c in cabecalho}
