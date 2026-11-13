"""Comandos:  uv run python -m assistente <comando>

  listar-trechos   mostra os trechos da base, com documento, seção e tamanho
  perguntar "..." [--modo contexto-completo] [--idioma pt|en]
                   faz uma pergunta ao Gemini e mostra situação, resposta, fontes e tokens
  avaliar [--modo contexto-completo] [--so <tipo>]
                   roda avaliacao/perguntas.yaml e grava o resultado em resultados/
"""

import argparse
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


def perguntar(args: list[str]) -> None:
    from assistente.responder import MODOS, responder

    leitor = argparse.ArgumentParser(prog="python -m assistente perguntar")
    leitor.add_argument("pergunta")
    leitor.add_argument("--modo", choices=MODOS, default="contexto-completo")
    leitor.add_argument("--idioma", choices=("pt", "en"), default="pt")
    a = leitor.parse_args(args)

    r = responder(a.pergunta, a.idioma, a.modo)
    print(f"Situação: {r.situacao}" + (f"  ({r.erro})" if r.erro else ""))
    print(f"Resposta: {r.resposta or '—'}")
    print("Fontes:   " + (", ".join(f"{f.id} {f.rotulo}" for f in r.fontes) or "—"))
    if r.fontes_desconhecidas:
        print(f"          ids citados que não existem: {', '.join(r.fontes_desconhecidas)}")
    print(f"Tokens:   {r.tokens_entrada} de entrada, {r.tokens_saida} de saída "
          f"({r.trechos_enviados} trechos enviados)")
    print(f"Tempo:    {r.ms} ms")


def avaliar(args: list[str]) -> None:
    from assistente.avaliacao import TIPOS, avaliar as rodar
    from assistente.responder import MODOS

    leitor = argparse.ArgumentParser(prog="python -m assistente avaliar")
    leitor.add_argument("--modo", choices=MODOS, default="contexto-completo")
    leitor.add_argument("--so", choices=list(TIPOS), help="roda só um tipo de pergunta")
    a = leitor.parse_args(args)
    print(f"\nResultado em {rodar(a.modo, a.so)}")


def main() -> None:
    comandos = {
        "listar-trechos": lambda _: listar_trechos(),
        "perguntar": perguntar,
        "avaliar": avaliar,
    }
    if len(sys.argv) < 2 or sys.argv[1] not in comandos:
        print(__doc__)
        sys.exit(1)
    comandos[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    main()
