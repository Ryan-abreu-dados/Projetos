"""Carga da camada raw: copia cada extração nova para o DuckDB, uma de cada vez.

Watermark: controle.cargas guarda as extrações já carregadas. Na próxima execução
só entram as pastas com data maior que a última carregada. Rodar de novo sem
extração nova não faz nada.

Cada extração entra numa transação: ou entram os dois arquivos e o registro em
controle.cargas, ou não entra nada. Se o processo cair no meio, a próxima execução
recomeça daquela extração sem deixar linha pela metade.
"""
from datetime import date
from pathlib import Path

import duckdb

from pipeline.checar_schema import checar

TABELAS = ("estacoes", "leituras")


def preparar_banco(con: duckdb.DuckDBPyConnection, contrato: dict) -> None:
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute("CREATE SCHEMA IF NOT EXISTS controle")
    con.execute("""
        CREATE TABLE IF NOT EXISTS controle.cargas (
            data_extracao   DATE PRIMARY KEY,
            linhas_estacoes INTEGER,
            linhas_leituras INTEGER,
            carregado_em    TIMESTAMP
        )
    """)
    for tabela in TABELAS:
        colunas = ", ".join(f"{c} {t}" for c, t in contrato[tabela]["obrigatorias"].items())
        con.execute(f"CREATE TABLE IF NOT EXISTS raw.{tabela} ({colunas}, _extracao DATE)")
        # coluna opcional aceita no contrato vira coluna da raw
        for coluna, tipo in contrato[tabela].get("opcionais", {}).items():
            con.execute(f"ALTER TABLE raw.{tabela} ADD COLUMN IF NOT EXISTS {coluna} {tipo}")


def watermark(con: duckdb.DuckDBPyConnection) -> date | None:
    return con.execute("SELECT max(data_extracao) FROM controle.cargas").fetchone()[0]


def extracoes_pendentes(pasta_extracoes: Path, depois_de: date | None, ate: date | None) -> list[tuple[date, Path]]:
    pendentes = []
    for pasta in sorted(p for p in pasta_extracoes.iterdir() if p.is_dir()):
        dia = date.fromisoformat(pasta.name)
        if (depois_de is None or dia > depois_de) and (ate is None or dia <= ate):
            pendentes.append((dia, pasta))
    return pendentes


def _ponto_de_falha(etapa: str) -> None:
    """Não faz nada. Os testes trocam esta função para simular uma queda no meio da carga."""


def carregar_extracao(con: duckdb.DuckDBPyConnection, dia: date, pasta: Path, contrato: dict) -> dict:
    # Confere o contrato ANTES de abrir a transação: arquivo fora do padrão não entra
    tipos = {t: checar(pasta / f"{t}.csv", contrato[t]) for t in TABELAS}
    linhas = {}
    con.execute("BEGIN TRANSACTION")
    try:
        for tabela in TABELAS:
            arquivo = (pasta / f"{tabela}.csv").as_posix()
            colunas = "{" + ", ".join(f"'{c}': '{t}'" for c, t in tipos[tabela].items()) + "}"
            # Apaga o que houver desta extração antes de inserir: recarregar o mesmo dia
            # nunca duplica (delete + insert pela data da extração)
            con.execute(f"DELETE FROM raw.{tabela} WHERE _extracao = ?", [dia])
            con.execute(f"""
                INSERT INTO raw.{tabela} BY NAME
                SELECT *, DATE '{dia.isoformat()}' AS _extracao
                FROM read_csv('{arquivo}', header = true, columns = {colunas})
            """)
            linhas[tabela] = con.execute(
                f"SELECT count(*) FROM raw.{tabela} WHERE _extracao = ?", [dia]).fetchone()[0]
            _ponto_de_falha(f"depois_de_{tabela}")
        con.execute("DELETE FROM controle.cargas WHERE data_extracao = ?", [dia])
        con.execute("INSERT INTO controle.cargas VALUES (?, ?, ?, now())",
                    [dia, linhas["estacoes"], linhas["leituras"]])
        con.execute("COMMIT")
    except BaseException:
        con.execute("ROLLBACK")
        raise
    return linhas
