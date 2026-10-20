"""Roda um caso: prepara, mede a consulta antes, aplica a correção e mede depois.

Cada caso é uma pasta em sql/casos/ com estes arquivos:
  preparar.sql         (opcional) monta o cenário: carga, UPDATE em massa, índice
  parametros.sql       (opcional) um SELECT cujas colunas viram parâmetros das consultas
  estimativa.sql       (opcional) consulta para comparar linhas estimadas x reais
  consulta_antes.sql   a consulta lenta
  correcao.sql         o que muda no banco (índice, ANALYZE, VACUUM...)
  consulta_depois.sql  a consulta depois da correção
"""
import json
import statistics
import time
from pathlib import Path

import psycopg

from scripts.conexao import comandos_do_arquivo, executar_arquivo

PASTA_CASOS = Path(__file__).resolve().parent.parent / "sql" / "casos"

TITULOS = {
    "01_funcao_no_filtro": "Função na coluna do filtro",
    "02_indice_covering": "Relatório mensal com índice covering",
    "03_estatisticas_defasadas": "Estatísticas defasadas depois de carga em massa",
    "04_update_em_massa_e_vacuum": "UPDATE em massa e VACUUM",
    "05_paginacao_offset": "Paginação com OFFSET x keyset",
}


def listar_casos() -> list[Path]:
    return sorted(p for p in PASTA_CASOS.iterdir() if p.is_dir())


def _consulta(arquivo: Path) -> str:
    """O último comando do arquivo, sem as linhas de comentário."""
    comando = comandos_do_arquivo(arquivo)[-1]
    return "\n".join(l for l in comando.splitlines() if not l.strip().startswith("--"))


def explicar(conn, arquivo: Path, params: dict | None = None, analisar: bool = True) -> dict:
    """Roda EXPLAIN (ANALYZE, BUFFERS) e devolve o plano em JSON."""
    opcoes = "ANALYZE, BUFFERS, FORMAT JSON" if analisar else "FORMAT JSON"
    with psycopg.ClientCursor(conn) as cur:
        cur.execute(f"EXPLAIN ({opcoes}) {_consulta(arquivo)}", params or None)
        saida = cur.fetchone()[0]
    if isinstance(saida, str):
        saida = json.loads(saida)
    return saida[0]


def nos(plano: dict):
    """Percorre todos os nós do plano, de cima para baixo."""
    yield plano
    for filho in plano.get("Plans", []):
        yield from nos(filho)


def resumir(explain: dict) -> dict:
    """Extrai do plano o que interessa para comparar antes e depois."""
    raiz = explain["Plan"]
    formato = []
    for no in nos(raiz):
        rotulo = no["Node Type"]
        if "Index Name" in no:
            rotulo += f" ({no['Index Name']})"
        elif "Relation Name" in no:
            rotulo += f" ({no['Relation Name']})"
        formato.append(rotulo)
    # linhas que o banco tocou na tabela corridas (devolvidas + descartadas pelo filtro)
    linhas_lidas = sum(
        (no.get("Actual Rows", 0) + no.get("Rows Removed by Filter", 0)) * no.get("Actual Loops", 1)
        for no in nos(raiz)
        if no.get("Relation Name") == "corridas"
    )
    return {
        "tempo_ms": round(explain["Execution Time"], 2),
        "planejamento_ms": round(explain["Planning Time"], 2),
        "blocos": raiz.get("Shared Hit Blocks", 0) + raiz.get("Shared Read Blocks", 0),
        "heap_fetches": sum(no.get("Heap Fetches", 0) for no in nos(raiz)),
        "linhas_lidas_corridas": round(linhas_lidas),
        "plano": formato,
    }


def medir(conn, arquivo: Path, params: dict | None, repeticoes: int) -> dict:
    """Roda a consulta várias vezes. A primeira esquenta o cache e é descartada."""
    execucoes = [resumir(explicar(conn, arquivo, params)) for _ in range(repeticoes)]
    validas = execucoes[1:] if repeticoes > 1 else execucoes
    resumo = dict(validas[-1])
    resumo["tempo_ms"] = round(statistics.median(e["tempo_ms"] for e in validas), 2)
    resumo["tempos_ms"] = [e["tempo_ms"] for e in validas]
    return resumo


def metricas_tabela(conn) -> dict:
    # Força o backend a publicar as estatísticas pendentes (linhas mortas do UPDATE)
    conn.execute("SELECT pg_stat_force_next_flush()")
    linha = conn.execute("""
        SELECT n_live_tup, n_dead_tup,
               pg_table_size('corridas')   AS bytes_tabela,
               pg_indexes_size('corridas') AS bytes_indices
        FROM pg_stat_user_tables WHERE relname = 'corridas'
    """).fetchone()
    return {
        "linhas_vivas": linha[0],
        "linhas_mortas": linha[1],
        "tabela_mb": round(linha[2] / 1024 / 1024, 1),
        "indices_mb": round(linha[3] / 1024 / 1024, 1),
    }


def estimativa(conn, arquivo: Path) -> dict:
    """Compara quantas linhas o planejador espera com quantas existem de fato."""
    plano = explicar(conn, arquivo, analisar=False)["Plan"]
    reais = conn.execute(f"SELECT count(*) FROM ({_consulta(arquivo).rstrip(';')}) q").fetchone()[0]
    return {"estimadas": plano["Plan Rows"], "reais": reais}


def rodar_caso(conn, pasta: Path, repeticoes: int = 6) -> dict:
    resultado = {"caso": pasta.name, "titulo": TITULOS.get(pasta.name, pasta.name)}

    if (pasta / "preparar.sql").exists():
        inicio = time.perf_counter()
        executar_arquivo(conn, pasta / "preparar.sql")
        resultado["preparar_s"] = round(time.perf_counter() - inicio, 1)

    params = None
    if (pasta / "parametros.sql").exists():
        params = executar_arquivo(conn, pasta / "parametros.sql")[0]
        resultado["parametros"] = {k: str(v) for k, v in params.items()}

    tem_estimativa = (pasta / "estimativa.sql").exists()
    resultado["metricas_antes"] = metricas_tabela(conn)
    if tem_estimativa:
        resultado["estimativa_antes"] = estimativa(conn, pasta / "estimativa.sql")
    resultado["antes"] = medir(conn, pasta / "consulta_antes.sql", params, repeticoes)

    inicio = time.perf_counter()
    executar_arquivo(conn, pasta / "correcao.sql")
    resultado["correcao_s"] = round(time.perf_counter() - inicio, 1)

    resultado["metricas_depois"] = metricas_tabela(conn)
    if tem_estimativa:
        resultado["estimativa_depois"] = estimativa(conn, pasta / "estimativa.sql")
    resultado["depois"] = medir(conn, pasta / "consulta_depois.sql", params, repeticoes)
    return resultado
