"""Reconciliação: confere se origem e destino têm o mesmo conteúdo.

Uso: python -m cdc.reconciliar [--corrigir]

A replicação pode ficar "verde" e o dado estar errado: alguém escreve direto no
destino, uma linha é apagada à mão, uma tabela fica fora da publicação. Nada
disso gera erro. A reconciliação compara os dois lados em três passos:

1. Por faixa de 10 mil ids: contagem + md5 do texto das linhas. Barato, e uma
   faixa igual dos dois lados não precisa ser olhada de novo.
2. Faixa diferente é conferida outra vez depois de uma sonda (para descartar
   mudanças que ainda estavam a caminho).
3. Nas faixas que continuam diferentes, compara linha a linha e lista os ids.

--corrigir copia da origem para o destino as linhas que faltam ou divergem.
Linha que só existe no destino é apenas listada: apagar dado é decisão de gente.
"""
import argparse
import json

from cdc import sonda
from cdc.config import DESTINO, ORIGEM, TABELAS, conectar

TAMANHO_FAIXA = 10_000


def resumo_por_faixa(conn, tabela: str, faixas: list[int] | None = None) -> dict:
    filtro = "WHERE id / %(t)s = ANY(%(faixas)s)" if faixas is not None else ""
    linhas = conn.execute(f"""
        SELECT id / %(t)s AS faixa, count(*), md5(string_agg(t::text, '|' ORDER BY id))
        FROM {tabela} t {filtro}
        GROUP BY 1
    """, {"t": TAMANHO_FAIXA, "faixas": faixas}).fetchall()
    return {faixa: (contagem, hash_) for faixa, contagem, hash_ in linhas}


def faixas_divergentes(origem, destino, tabela: str, faixas: list[int] | None = None) -> list[int]:
    a = resumo_por_faixa(origem, tabela, faixas)
    b = resumo_por_faixa(destino, tabela, faixas)
    return sorted(f for f in set(a) | set(b) if a.get(f) != b.get(f))


def linhas_da_faixa(conn, tabela: str, faixa: int) -> dict:
    return dict(conn.execute(
        f"SELECT id, md5(t::text) FROM {tabela} t WHERE id / %s = %s",
        [TAMANHO_FAIXA, faixa]).fetchall())


def copiar_para_destino(origem, destino, tabela: str, ids: list[int]) -> None:
    """Upsert das linhas da origem no destino (INSERT ... ON CONFLICT DO UPDATE)."""
    with origem.cursor() as cur:
        cur.execute(f"SELECT * FROM {tabela} WHERE id = ANY(%s)", [ids])
        colunas = [d.name for d in cur.description]
        linhas = cur.fetchall()
    atualizar = ", ".join(f"{c} = EXCLUDED.{c}" for c in colunas if c != "id")
    marcadores = ", ".join(["%s"] * len(colunas))
    with destino.transaction():
        with destino.cursor() as cur:
            cur.executemany(
                f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES ({marcadores}) "
                f"ON CONFLICT (id) DO UPDATE SET {atualizar}", linhas)


class ReplicacaoParada(Exception):
    pass


def reconciliar(origem, destino, corrigir: bool = False, tentativas: int = 3) -> dict:
    # Só reconcilio com a replicação andando. Se ela está parada, uma linha "faltando"
    # ainda vai chegar; copiá-la agora faria a replicação bater nela depois (chave duplicada).
    if sonda.sincronizar(origem, destino, limite_s=30) is None:
        raise ReplicacaoParada("a sonda não chegou ao destino em 30 s: confira `python -m cdc.monitor`")
    relatorio = {}
    for tabela in TABELAS:
        suspeitas = faixas_divergentes(origem, destino, tabela)
        for _ in range(tentativas - 1):
            if not suspeitas:
                break
            sonda.sincronizar(origem, destino)  # dá tempo para o que estava a caminho chegar
            suspeitas = faixas_divergentes(origem, destino, tabela, suspeitas)

        faltando, diferentes, sobrando = [], [], []
        for faixa in suspeitas:
            o, d = linhas_da_faixa(origem, tabela, faixa), linhas_da_faixa(destino, tabela, faixa)
            faltando += [i for i in o if i not in d]
            sobrando += [i for i in d if i not in o]
            diferentes += [i for i in o if i in d and o[i] != d[i]]

        if corrigir and (faltando or diferentes):
            copiar_para_destino(origem, destino, tabela, faltando + diferentes)
        relatorio[tabela] = {
            "faixas_divergentes": len(suspeitas),
            "faltando_no_destino": sorted(faltando),
            "diferentes": sorted(diferentes),
            "so_no_destino": sorted(sobrando),
            "corrigidas": len(faltando + diferentes) if corrigir else 0,
        }
    return relatorio


def total_divergencias(relatorio: dict) -> int:
    return sum(len(r["faltando_no_destino"]) + len(r["diferentes"]) + len(r["so_no_destino"])
               for r in relatorio.values())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--corrigir", action="store_true")
    args = parser.parse_args()
    with conectar(ORIGEM) as o, conectar(DESTINO) as d:
        rel = reconciliar(o, d, corrigir=args.corrigir)
    print(json.dumps(rel, ensure_ascii=False, indent=2))
    print(f"Divergências encontradas: {total_divergencias(rel)}")
