"""Pipeline completo: gera os dados, carrega, roda os 5 casos e grava os resultados.

Uso: python -m scripts.bench --linhas 5000000

Os casos mudam o banco em sequência (índices, carga, UPDATE), então o benchmark
sempre recomeça do zero: recria as tabelas e recarrega os CSVs.
Saída: resultados/bench.json (tudo) e resultados/bench.md (tabela para o README).
"""
import argparse
import json
import os
import platform
import time
from datetime import datetime
from pathlib import Path

from scripts.carregar import carregar
from scripts.casos import listar_casos, rodar_caso
from scripts.conexao import conectar
from scripts.gerar_dados import PASTA_PADRAO, gerar

PASTA_RESULTADOS = Path(__file__).resolve().parent.parent / "resultados"
CONFIGS = ["server_version", "shared_buffers", "work_mem", "max_parallel_workers_per_gather",
           "random_page_cost", "jit"]


def contar_linhas_csv(arquivo: Path) -> int:
    with open(arquivo, "rb") as f:
        return sum(1 for _ in f) - 1


def ambiente(conn, linhas: int) -> dict:
    return {
        "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "linhas_geradas": linhas,
        "maquina": os.getenv("MAQUINA", f"{platform.system()} {platform.release()}, {os.cpu_count()} CPUs lógicas"),
        "postgres": {c: conn.execute(f"SHOW {c}").fetchone()[0] for c in CONFIGS},
    }


def numero(valor: float, casas: int = 0) -> str:
    """Formata no padrão brasileiro: 1.234.567,89"""
    return f"{valor:,.{casas}f}".translate(str.maketrans(",.", ".,"))


def formatar_ms(ms: float) -> str:
    if ms >= 1000:
        return f"{numero(ms / 1000, 2)} s"
    return f"{numero(ms, 1 if ms >= 1 else 2)} ms"


def escrever_markdown(resultado: dict) -> str:
    amb = resultado["ambiente"]
    linhas = [
        f"# Resultados do benchmark ({amb['data']})",
        "",
        f"- Corridas geradas: {numero(amb['linhas_geradas'])}",
        f"- Máquina: {amb['maquina']}",
        "- PostgreSQL: " + ", ".join(f"{k}={v}" for k, v in amb["postgres"].items()),
        "- Tempo = mediana de 5 execuções de EXPLAIN ANALYZE com cache quente (a 1ª é descartada).",
        "",
        "| Caso | Antes (mediana) | Depois (mediana) | Vezes mais rápido | Faixa antes | Faixa depois | Blocos lidos antes → depois |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in resultado["casos"]:
        a, d = c["antes"], c["depois"]
        ganho = a["tempo_ms"] / d["tempo_ms"] if d["tempo_ms"] else float("inf")
        faixa_a = f"{formatar_ms(min(a['tempos_ms']))} a {formatar_ms(max(a['tempos_ms']))}"
        faixa_d = f"{formatar_ms(min(d['tempos_ms']))} a {formatar_ms(max(d['tempos_ms']))}"
        linhas.append(
            f"| {c['titulo']} | {formatar_ms(a['tempo_ms'])} | {formatar_ms(d['tempo_ms'])} "
            f"| {numero(ganho, 1)}× | {faixa_a} | {faixa_d} | {numero(a['blocos'])} → {numero(d['blocos'])} |"
        )
    linhas.append("")
    for c in resultado["casos"]:
        a, d = c["antes"], c["depois"]
        linhas += [
            f"## {c['titulo']}",
            "",
            f"- Plano antes: {' → '.join(a['plano'])}",
            f"- Plano depois: {' → '.join(d['plano'])}",
            f"- Linhas tocadas em corridas: {numero(a['linhas_lidas_corridas'])} → {numero(d['linhas_lidas_corridas'])}",
            f"- Heap Fetches: {numero(a['heap_fetches'])} → {numero(d['heap_fetches'])}",
            f"- Preparar o cenário levou {numero(c.get('preparar_s', 0), 1)} s; a correção levou {numero(c['correcao_s'], 1)} s.",
            f"- Índices da tabela: {numero(c['metricas_antes']['indices_mb'], 1)} MB → {numero(c['metricas_depois']['indices_mb'], 1)} MB.",
            f"- Tabela: {numero(c['metricas_antes']['tabela_mb'], 1)} MB → {numero(c['metricas_depois']['tabela_mb'], 1)} MB; "
            f"linhas mortas: {numero(c['metricas_antes']['linhas_mortas'])} → {numero(c['metricas_depois']['linhas_mortas'])}",
        ]
        if "estimativa_antes" in c:
            ea, ed = c["estimativa_antes"], c["estimativa_depois"]
            linhas.append(
                f"- Linhas estimadas x reais: antes {numero(ea['estimadas'])} x {numero(ea['reais'])}; "
                f"depois {numero(ed['estimadas'])} x {numero(ed['reais'])}"
            )
        linhas.append("")
    return "\n".join(linhas)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--linhas", type=int, default=int(os.getenv("LINHAS", "5000000")))
    parser.add_argument("--repeticoes", type=int, default=6)
    parser.add_argument("--so-markdown", action="store_true",
                        help="só reescreve bench.md a partir do bench.json existente")
    args = parser.parse_args()

    if args.so_markdown:
        resultado = json.loads((PASTA_RESULTADOS / "bench.json").read_text(encoding="utf-8"))
        (PASTA_RESULTADOS / "bench.md").write_text(escrever_markdown(resultado), encoding="utf-8")
        return

    csv = PASTA_PADRAO / "corridas.csv"
    if not csv.exists() or contar_linhas_csv(csv) != args.linhas:
        inicio = time.perf_counter()
        gerar(args.linhas)
        print(f"Dados gerados em {time.perf_counter() - inicio:.1f} s")

    with conectar() as conn:
        inicio = time.perf_counter()
        carregar(conn)
        print(f"Carga em {time.perf_counter() - inicio:.1f} s")
        resultado = {"ambiente": ambiente(conn, args.linhas), "casos": []}
        for pasta in listar_casos():
            print(f"Rodando {pasta.name}...", flush=True)
            caso = rodar_caso(conn, pasta, args.repeticoes)
            print(f"  antes {formatar_ms(caso['antes']['tempo_ms'])} | depois {formatar_ms(caso['depois']['tempo_ms'])}")
            resultado["casos"].append(caso)

    PASTA_RESULTADOS.mkdir(exist_ok=True)
    (PASTA_RESULTADOS / "bench.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (PASTA_RESULTADOS / "bench.md").write_text(escrever_markdown(resultado), encoding="utf-8")
    print("Resultados em resultados/bench.md")


if __name__ == "__main__":
    main()
