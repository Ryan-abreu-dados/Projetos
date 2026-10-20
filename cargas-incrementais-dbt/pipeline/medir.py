"""Mede o pipeline e grava resultados/resultados.json e resultados/resultados.md.

O que é medido, sempre sobre as extrações que estão em dados/extracoes:
  1. carga completa do zero (todas as extrações) e o tempo
  2. a mesma execução de novo, sem extração nova: o conteúdo tem de ficar idêntico
  3. carga até o penúltimo dia + incremental só do último dia: tem de dar o mesmo
     conteúdo da carga completa
  4. --full-refresh (reconstrói tudo do zero): tem de dar o mesmo conteúdo
  5. quantas linhas um watermark pela hora da medição teria perdido nestes dados
"""
import json
import time
from datetime import date
from pathlib import Path

import duckdb

from pipeline.alerta import enviar_alerta
from pipeline.rodar import PASTA_DADOS, FalhaNoPipeline, rodar

PASTA_RESULTADOS = Path(__file__).resolve().parent.parent / "resultados"

# Colunas de negócio de cada tabela final. Fica de fora processado_ate, que é
# controle interno da dimensão e muda conforme o tamanho de cada lote.
COLUNAS = {
    "analitico.fct_leituras": "estacao_id, medido_em, estacao_versao_id, temperatura_c, chuva_mm, _extracao",
    "analitico.dim_estacoes": "versao_id, estacao_id, nome, cidade, uf, altitude_m, status, valido_de, valido_ate, vigente",
    "analitico.leituras_rejeitadas": "estacao_id, medido_em, temperatura_c, chuva_mm, _extracao, motivo",
}


def impressao_digital(banco: Path) -> dict:
    """Contagem + md5 do conteúdo ordenado de cada tabela final."""
    con = duckdb.connect(str(banco), read_only=True)
    try:
        saida = {}
        for tabela, colunas in COLUNAS.items():
            linhas, hash_ = con.execute(f"""
                SELECT count(*), md5(string_agg(linha, '\n' ORDER BY linha))
                FROM (SELECT concat_ws('|', {colunas}) AS linha FROM {tabela})
            """).fetchone()
            saida[tabela] = {"linhas": linhas, "md5": hash_}
        return saida
    finally:
        con.close()


def contagens(banco: Path) -> dict:
    con = duckdb.connect(str(banco), read_only=True)
    try:
        def um(sql):
            return con.execute(sql).fetchone()[0]
        return {
            "linhas_recebidas": um("SELECT count(*) FROM raw.leituras"),
            "leituras_unicas_recebidas": um("SELECT count(*) FROM (SELECT DISTINCT estacao_id, medido_em FROM raw.leituras)"),
            "linhas_na_fato": um("SELECT count(*) FROM analitico.fct_leituras"),
            "rejeitadas": um("SELECT count(*) FROM analitico.leituras_rejeitadas"),
            "versoes_de_estacao": um("SELECT count(*) FROM analitico.dim_estacoes"),
            "estacoes_com_historico": um("""SELECT count(*) FROM (SELECT estacao_id FROM analitico.dim_estacoes
                                             GROUP BY 1 HAVING count(*) > 1)"""),
            # O que um watermark por medido_em perderia: em cada extração, as linhas medidas
            # antes (ou na mesma hora) da maior medição já vista nas extrações anteriores.
            "perdidas_com_watermark_por_medicao": um("""
                WITH por_extracao AS (
                    SELECT _extracao, max(medido_em) AS maior_medicao FROM raw.leituras GROUP BY 1
                ),
                marca AS (
                    SELECT _extracao,
                           max(maior_medicao) OVER (ORDER BY _extracao
                               ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS watermark
                    FROM por_extracao
                )
                SELECT count(*) FROM raw.leituras l JOIN marca m USING (_extracao)
                WHERE l.medido_em <= m.watermark
            """),
        }
    finally:
        con.close()


def _limpar(banco: Path):
    for arquivo in (banco, Path(f"{banco}.wal")):
        if arquivo.exists():
            arquivo.unlink()


def medir() -> dict:
    gabarito = json.loads((PASTA_DADOS / "gabarito.json").read_text(encoding="utf-8"))
    dias = sorted(p.name for p in (PASTA_DADOS / "extracoes").iterdir() if p.is_dir())
    banco_a = PASTA_DADOS / "medicao_completa.duckdb"
    banco_b = PASTA_DADOS / "medicao_incremental.duckdb"
    _limpar(banco_a)
    _limpar(banco_b)

    completa = rodar(banco=banco_a, verbose=False)
    digital_completa = impressao_digital(banco_a)

    repetida = rodar(banco=banco_a, verbose=False)
    digital_repetida = impressao_digital(banco_a)

    rodar(ate=date.fromisoformat(dias[-2]), banco=banco_b, verbose=False)
    ultimo_dia = rodar(banco=banco_b, verbose=False)
    digital_incremental = impressao_digital(banco_b)

    refresh = rodar(full_refresh=True, banco=banco_b, verbose=False)
    digital_refresh = impressao_digital(banco_b)

    numeros = contagens(banco_a)
    resultado = {
        "data": time.strftime("%Y-%m-%d %H:%M"),
        "extracoes": len(dias),
        "gabarito": {k: gabarito[k] for k in ("linhas_enviadas", "leituras_validas_unicas",
                                              "leituras_rejeitadas", "total_versoes", "injetado")},
        "contagens": numeros,
        "tempos_s": {
            "carga_completa": completa["total_s"],
            "carga_completa_so_raw": completa["carga_s"],
            "repetida_sem_novidade": repetida["total_s"],
            "incremental_ultimo_dia": ultimo_dia["total_s"],
            "incremental_ultimo_dia_so_raw": ultimo_dia["carga_s"],
            "full_refresh": refresh["total_s"],
        },
        "idempotencia": {
            "rodar_duas_vezes_igual": digital_completa == digital_repetida,
            "incremental_igual_a_completa": digital_completa == digital_incremental,
            "full_refresh_igual_a_incremental": digital_refresh == digital_incremental,
        },
        "confere_com_gabarito": {
            "fato": numeros["linhas_na_fato"] == gabarito["leituras_validas_unicas"],
            "rejeitadas": numeros["rejeitadas"] == gabarito["leituras_rejeitadas"],
            "versoes": numeros["versoes_de_estacao"] == gabarito["total_versoes"],
        },
        "impressao_digital": digital_completa,
    }
    PASTA_RESULTADOS.mkdir(exist_ok=True)
    (PASTA_RESULTADOS / "resultados.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    (PASTA_RESULTADOS / "resultados.md").write_text(_markdown(resultado), encoding="utf-8")
    print((PASTA_RESULTADOS / "resultados.md").read_text(encoding="utf-8"))

    # Conferência que reprova de verdade: qualquer "não" vira erro e alerta
    falhas = [nome for grupo in ("idempotencia", "confere_com_gabarito")
              for nome, ok in resultado[grupo].items() if not ok]
    if falhas:
        enviar_alerta("Conferência reprovou", ", ".join(falhas))
        raise FalhaNoPipeline(f"conferência reprovou: {falhas}")
    return resultado


def _n(valor) -> str:
    if isinstance(valor, float):
        return f"{valor:,.1f}".translate(str.maketrans(",.", ".,"))
    return f"{valor:,}".replace(",", ".")


def _markdown(r: dict) -> str:
    c, t, i, g = r["contagens"], r["tempos_s"], r["idempotencia"], r["confere_com_gabarito"]
    sim = lambda b: "sim" if b else "**NÃO**"
    return "\n".join([
        f"# Resultados ({r['data']})",
        "",
        f"Extrações processadas: {r['extracoes']} dias.",
        "",
        "| Medida | Valor |",
        "|---|---|",
        f"| Linhas de leitura recebidas | {_n(c['linhas_recebidas'])} |",
        f"| Leituras únicas recebidas | {_n(c['leituras_unicas_recebidas'])} |",
        f"| Linhas na fato | {_n(c['linhas_na_fato'])} |",
        f"| Rejeitadas pela regra de validade | {_n(c['rejeitadas'])} |",
        f"| Versões de estação (SCD2) | {_n(c['versoes_de_estacao'])} |",
        f"| Estações com mais de uma versão | {_n(c['estacoes_com_historico'])} |",
        f"| Linhas que um watermark pela hora da medição teria ignorado | {_n(c['perdidas_com_watermark_por_medicao'])} |",
        "",
        "| Idempotência e conferência | Resultado |",
        "|---|---|",
        f"| Rodar duas vezes dá o mesmo conteúdo | {sim(i['rodar_duas_vezes_igual'])} |",
        f"| Carga em duas partes (todos os dias menos o último, depois o último) = carga completa | {sim(i['incremental_igual_a_completa'])} |",
        f"| --full-refresh = incremental | {sim(i['full_refresh_igual_a_incremental'])} |",
        f"| Fato bate com o gabarito do gerador | {sim(g['fato'])} |",
        f"| Rejeitadas batem com o gabarito | {sim(g['rejeitadas'])} |",
        f"| Versões batem com o gabarito | {sim(g['versoes'])} |",
        "",
        "| Tempo (s) | Total | Só a carga raw |",
        "|---|---|---|",
        f"| Carga completa | {_n(t['carga_completa'])} | {_n(t['carga_completa_so_raw'])} |",
        f"| Incremental de 1 dia | {_n(t['incremental_ultimo_dia'])} | {_n(t['incremental_ultimo_dia_so_raw'])} |",
        f"| Repetida sem extração nova | {_n(t['repetida_sem_novidade'])} | |",
        f"| --full-refresh | {_n(t['full_refresh'])} | |",
        "",
        "O total inclui a partida do dbt (alguns segundos fixos por execução).",
    ])
