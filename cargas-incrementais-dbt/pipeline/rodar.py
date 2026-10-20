"""Uma execução do pipeline: carrega as extrações pendentes e roda `dbt build`.

`dbt build` cria os modelos e roda os testes de dados na mesma passada. Se um
teste reprova, o comando termina com erro: o pipeline não segue como se
estivesse tudo bem.
"""
import os
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

import duckdb

from pipeline.alerta import enviar_alerta
from pipeline.carregar import carregar_extracao, extracoes_pendentes, preparar_banco, watermark
from pipeline.checar_schema import CONFIG_PADRAO, ErroDeSchema, carregar_contrato

RAIZ = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ / "dados"
BANCO_PADRAO = PASTA_DADOS / "estacoes.duckdb"
PASTA_DBT = RAIZ / "modelos_dbt"


class FalhaNoPipeline(Exception):
    pass


def executar_dbt(argumentos: list[str], banco: Path) -> subprocess.CompletedProcess:
    """Roda o dbt num processo separado: assim ele abre e fecha o arquivo do DuckDB sozinho."""
    ambiente = dict(os.environ, DUCKDB_PATH=str(Path(banco).resolve()))
    comando = [sys.executable, "-c", "from dbt.cli.main import cli; cli()", *argumentos,
               "--project-dir", str(PASTA_DBT), "--profiles-dir", str(PASTA_DBT)]
    return subprocess.run(comando, cwd=PASTA_DBT, env=ambiente, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def rodar(ate: date | None = None, full_refresh: bool = False, banco: Path = BANCO_PADRAO,
          pasta_dados: Path = PASTA_DADOS, contrato_path: Path = CONFIG_PADRAO, verbose: bool = True) -> dict:
    inicio = time.perf_counter()
    contrato = carregar_contrato(contrato_path)
    resumo = {"extracoes_carregadas": [], "linhas_leituras": 0}

    con = duckdb.connect(str(banco))
    try:
        preparar_banco(con, contrato)
        ultima = watermark(con)
        for dia, pasta in extracoes_pendentes(pasta_dados / "extracoes", ultima, ate):
            try:
                linhas = carregar_extracao(con, dia, pasta, contrato)
            except (ErroDeSchema, duckdb.Error) as erro:
                enviar_alerta("Carga interrompida", f"extração {dia}: {erro}")
                raise FalhaNoPipeline(str(erro)) from erro
            resumo["extracoes_carregadas"].append(dia.isoformat())
            resumo["linhas_leituras"] += linhas["leituras"]
        resumo["watermark"] = str(watermark(con))
    finally:
        con.close()
    resumo["carga_s"] = round(time.perf_counter() - inicio, 2)

    inicio_dbt = time.perf_counter()
    argumentos = ["build"] + (["--full-refresh"] if full_refresh else [])
    saida = executar_dbt(argumentos, banco)
    resumo["dbt_s"] = round(time.perf_counter() - inicio_dbt, 2)
    if verbose:
        print(saida.stdout[-3000:])
    if saida.returncode != 0:
        falhas = [l.strip() for l in saida.stdout.splitlines() if "FAIL" in l or "ERROR" in l]
        enviar_alerta("dbt build reprovou", "\n".join(falhas[-10:]) or saida.stderr[-1500:])
        raise FalhaNoPipeline("dbt build reprovou")

    resumo["total_s"] = round(time.perf_counter() - inicio, 2)
    return resumo
