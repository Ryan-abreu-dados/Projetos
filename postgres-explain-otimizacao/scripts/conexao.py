"""Conexão com o PostgreSQL e execução de arquivos .sql.

A configuração vem das mesmas variáveis de ambiente que o psql usa, com
padrões que batem com o docker-compose.yml. A senha "postgres" só vale
para o banco local de teste: não existe segredo no repositório.
"""
import os
from pathlib import Path

import psycopg


def conectar(banco: str | None = None) -> psycopg.Connection:
    # autocommit=True porque VACUUM e CREATE DATABASE não rodam dentro de transação
    return psycopg.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5433"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres"),
        dbname=banco or os.getenv("PGDATABASE", "corridas"),
        autocommit=True,
    )


def comandos_do_arquivo(caminho: Path) -> list[str]:
    """Separa um .sql em comandos, cortando no ';' de fim de linha.

    Preciso rodar um comando por vez porque VACUUM não aceita ir junto com
    outros numa string só. Os arquivos do projeto são simples (sem funções
    com $$), então esse corte basta.
    """
    texto = Path(caminho).read_text(encoding="utf-8").replace("\r\n", "\n")
    comandos = []
    for pedaco in texto.split(";\n"):
        uteis = [l for l in pedaco.splitlines() if l.strip() and not l.strip().startswith("--")]
        if uteis:
            comandos.append(pedaco.strip().rstrip(";"))
    return comandos


def executar_arquivo(conn: psycopg.Connection, caminho: Path, params: dict | None = None):
    """Executa o arquivo e devolve as linhas do último comando que retornou dados."""
    resultado = None
    for comando in comandos_do_arquivo(caminho):
        # ClientCursor monta a consulta no cliente: o EXPLAIN recebe valores literais,
        # como uma consulta escrita à mão.
        with psycopg.ClientCursor(conn) as cur:
            cur.execute(comando, params or None)
            if cur.description:
                colunas = [d.name for d in cur.description]
                resultado = [dict(zip(colunas, linha)) for linha in cur.fetchall()]
    return resultado
