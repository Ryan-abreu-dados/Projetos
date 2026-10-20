"""Roteiro completo, o mesmo que o `docker compose up` roda:

  1. prepara os bancos e espera a cópia inicial
  2. mede o atraso com a loja em movimento
  3. desliga o destino por 30 s e mede a recuperação
  4. derruba a conexão de replicação e mede a volta
  5. reconcilia (tem de dar zero divergência)
  6. altera 3 linhas direto no destino, reconcilia, corrige e reconcilia de novo

Saída: resultados/resultados.json e resultados/resultados.md
"""
import json
import os
import platform
import time
from pathlib import Path

from cdc import falhas, latencia
from cdc.config import DESTINO, ORIGEM, conectar
from cdc.preparar import preparar
from cdc.reconciliar import reconciliar, total_divergencias

PASTA_RESULTADOS = Path(__file__).resolve().parent.parent / "resultados"


def divergencia_silenciosa(origem, destino) -> dict:
    """Escrever no destino não quebra a replicação: o dado só fica errado, em silêncio."""
    ids = [101, 202, 303]
    destino.execute("UPDATE clientes SET cidade = 'Cidade alterada no destino' WHERE id = ANY(%s)", [ids])
    antes = reconciliar(origem, destino)
    corrigido = reconciliar(origem, destino, corrigir=True)
    depois = reconciliar(origem, destino)
    return {
        "linhas_alteradas_no_destino": len(ids),
        "encontradas": antes["clientes"]["diferentes"],
        "corrigidas": corrigido["clientes"]["corrigidas"],
        "divergencias_depois": total_divergencias(depois),
    }


def main():
    resultado = {
        "data": time.strftime("%Y-%m-%d %H:%M"),
        "maquina": os.getenv("MAQUINA", f"{platform.system()} {platform.release()}, {os.cpu_count()} CPUs lógicas"),
    }
    print("1/6 preparando bancos e cópia inicial...", flush=True)
    resultado["preparo"] = preparar()
    print("2/6 medindo atraso com a loja em movimento...", flush=True)
    resultado["latencia"] = latencia.medir()
    print("3/6 destino parado por 30 s...", flush=True)
    resultado["destino_parado"] = falhas.destino_parado(30)
    print("4/6 conexão derrubada...", flush=True)
    resultado["conexao_derrubada"] = falhas.conexao_derrubada()
    with conectar(ORIGEM) as origem, conectar(DESTINO) as destino:
        print("5/6 reconciliando...", flush=True)
        resultado["divergencias_apos_falhas"] = total_divergencias(reconciliar(origem, destino))
        print("6/6 divergência silenciosa...", flush=True)
        resultado["divergencia_silenciosa"] = divergencia_silenciosa(origem, destino)
        resultado["linhas_finais"] = {
            t: destino.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
            for t in ("clientes", "produtos", "pedidos", "itens_pedido")}

    PASTA_RESULTADOS.mkdir(exist_ok=True)
    (PASTA_RESULTADOS / "resultados.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    (PASTA_RESULTADOS / "resultados.md").write_text(markdown(resultado), encoding="utf-8")
    print(markdown(resultado))


def n(valor, casas=1) -> str:
    if isinstance(valor, int):
        return f"{valor:,}".replace(",", ".")
    return f"{valor:,.{casas}f}".translate(str.maketrans(",.", ".,"))


def markdown(r: dict) -> str:
    p, l, dp, cd, ds = r["preparo"], r["latencia"], r["destino_parado"], r["conexao_derrubada"], r["divergencia_silenciosa"]
    linhas_origem = sum(p["origem"].values())
    return "\n".join([
        f"# Resultados ({r['data']})",
        "",
        f"Máquina: {r['maquina']}.",
        "",
        "| Medida | Valor |",
        "|---|---|",
        f"| Linhas na carga inicial (4 tabelas) | {n(linhas_origem)} |",
        f"| Cópia inicial para o destino | {n(p['copia_inicial_s'])} s |",
        f"| Carga simulada | {n(l['taxa_real_ops_s'])} operações/s (alvo {n(l['taxa_alvo_ops_s'], 0)}) |",
        f"| Atraso da origem ao destino, mediana | {n(l['p50_ms'])} ms |",
        f"| Atraso p95 / p99 / máximo | {n(l['p95_ms'])} / {n(l['p99_ms'])} / {n(l['max_ms'])} ms |",
        f"| Sondas que não chegaram em 10 s | {n(l['perdidas'])} de {n(l['amostras'])} |",
        f"| Destino parado | {n(dp['pausa_s'], 0)} s, com {n(dp['operacoes_durante_a_pausa'])} operações na origem |",
        f"| WAL retido no slot: antes → fim da pausa | {n(dp['wal_retido_antes_mb'], 2)} MB → {n(dp['wal_retido_no_fim_da_pausa_mb'], 2)} MB |",
        f"| Tempo para o destino alcançar a origem depois de religado | {n(dp['recuperacao_s'], 2)} s |",
        f"| Volta depois de derrubar a conexão | {n(cd['volta_s'], 2)} s |",
        f"| Divergências depois das falhas | {n(r['divergencias_apos_falhas'])} |",
        f"| Linhas alteradas direto no destino | {n(ds['linhas_alteradas_no_destino'])} |",
        f"| Encontradas pela reconciliação | {n(len(ds['encontradas']))} (ids {ds['encontradas']}) |",
        f"| Divergências depois de corrigir | {n(ds['divergencias_depois'])} |",
    ])


if __name__ == "__main__":
    main()
