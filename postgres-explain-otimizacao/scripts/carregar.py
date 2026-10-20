"""Cria as tabelas e carrega os CSVs no PostgreSQL com COPY.

Uso: python -m scripts.carregar
"""
import time
from pathlib import Path

from scripts.conexao import conectar, executar_arquivo
from scripts.gerar_dados import PASTA_PADRAO

RAIZ = Path(__file__).resolve().parent.parent


def copiar_csv(conn, tabela: str, arquivo: Path):
    # COPY FROM STDIN: o cliente manda o arquivo em pedaços e o servidor grava direto.
    # É muito mais rápido que um INSERT por linha.
    with conn.cursor() as cur:
        with cur.copy(f"COPY {tabela} FROM STDIN WITH (FORMAT csv, HEADER true)") as copia:
            with open(arquivo, "rb") as f:
                while bloco := f.read(1024 * 1024):
                    copia.write(bloco)


def carregar(conn, pasta: Path = PASTA_PADRAO):
    executar_arquivo(conn, RAIZ / "sql" / "schema.sql")
    for tabela in ("zonas", "motoristas", "corridas"):
        copiar_csv(conn, tabela, pasta / f"{tabela}.csv")
    # VACUUM marca as páginas como "todas visíveis" (o Index Only Scan depende disso)
    # e ANALYZE gera as estatísticas que o planejador usa para estimar quantas linhas vêm.
    for tabela in ("zonas", "motoristas", "corridas"):
        conn.execute(f"VACUUM (ANALYZE) {tabela}")


if __name__ == "__main__":
    inicio = time.perf_counter()
    with conectar() as conn:
        carregar(conn)
        total = conn.execute("SELECT count(*) FROM corridas").fetchone()[0]
    print(f"{total:,} corridas carregadas em {time.perf_counter() - inicio:.1f} s")
