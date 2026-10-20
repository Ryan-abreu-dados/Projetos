"""Linha de comando do projeto.

  python -m pipeline gerar [--dias 30] [--estacoes 200] [--drift-a-partir 20]
  python -m pipeline rodar [--ate 2026-01-15] [--full-refresh]
  python -m pipeline medir
  python -m pipeline demo      (gerar + rodar duas vezes + medir: é o que o Docker roda)
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

from pipeline.gerar_extracoes import gerar
from pipeline.medir import medir
from pipeline.rodar import BANCO_PADRAO, FalhaNoPipeline, rodar


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # acentos no terminal do Windows
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="pipeline")
    sub = parser.add_subparsers(dest="comando", required=True)

    p_gerar = sub.add_parser("gerar")
    p_gerar.add_argument("--dias", type=int, default=30)
    p_gerar.add_argument("--estacoes", type=int, default=200)
    p_gerar.add_argument("--drift-a-partir", type=int, default=None)

    p_rodar = sub.add_parser("rodar")
    p_rodar.add_argument("--ate", type=date.fromisoformat, default=None)
    p_rodar.add_argument("--full-refresh", action="store_true")

    sub.add_parser("medir")
    sub.add_parser("demo")
    args = parser.parse_args()

    try:
        if args.comando == "gerar":
            g = gerar(args.dias, args.estacoes, drift_a_partir=args.drift_a_partir)
            print(json.dumps({k: v for k, v in g.items() if not isinstance(v, dict) or k == "injetado"},
                             ensure_ascii=False, indent=2))
        elif args.comando == "rodar":
            print(json.dumps(rodar(args.ate, args.full_refresh), ensure_ascii=False, indent=2))
        elif args.comando == "medir":
            medir()
        elif args.comando == "demo":
            for arquivo in (BANCO_PADRAO, Path(f"{BANCO_PADRAO}.wal")):
                arquivo.unlink(missing_ok=True)  # a demonstração sempre começa do zero
            gerar()
            print("1ª execução:", json.dumps(rodar(verbose=False), ensure_ascii=False))
            print("2ª execução:", json.dumps(rodar(verbose=False), ensure_ascii=False))
            medir()
    except FalhaNoPipeline as erro:
        print(f"Pipeline parou: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
