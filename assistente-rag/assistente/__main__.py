"""Comandos:  uv run python -m assistente <comando>

  listar-trechos   mostra os trechos da base, com documento, seção e tamanho
"""

import sys

from assistente.base import ler_base
from assistente.chunking import dividir_por_secao

MINIMO_CARACTERES = 40


def listar_trechos() -> None:
    total = 0
    for doc in ler_base():
        marca = " (privado)" if doc.privado else ""
        print(f"\n{doc.id}{marca} · {doc.titulo}")
        for t in dividir_por_secao(doc):
            total += 1
            aviso = "  ⚠ trecho curto" if len(t.texto) < MINIMO_CARACTERES else ""
            inicio = t.texto[:70].replace("\n", " ")
            print(f"  {t.ordem:>2}. {t.secao} [{len(t.texto)} car.]{aviso}\n      {inicio}...")
    print(f"\nTotal: {total} trechos")


def main() -> None:
    comandos = {"listar-trechos": listar_trechos}
    if len(sys.argv) < 2 or sys.argv[1] not in comandos:
        print(__doc__)
        sys.exit(1)
    comandos[sys.argv[1]]()


if __name__ == "__main__":
    main()
