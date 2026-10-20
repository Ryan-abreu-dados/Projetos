"""Endereços dos dois bancos e funções de conexão.

Os padrões batem com o docker-compose.yml. A senha "postgres" só vale para os
bancos locais de teste: não existe segredo no repositório.

Atenção a ORIGEM_VISTA_PELO_DESTINO: quem abre a conexão de replicação é o
SERVIDOR de destino, não este script. Dentro do Docker ele enxerga a origem
pelo nome do serviço ("origem"), e não por localhost.
"""
import os

import psycopg
from psycopg.conninfo import make_conninfo

ORIGEM = os.getenv("ORIGEM_URL", "host=localhost port=5441 dbname=loja user=postgres password=postgres")
DESTINO = os.getenv("DESTINO_URL", "host=localhost port=5442 dbname=loja user=postgres password=postgres")
ORIGEM_VISTA_PELO_DESTINO = os.getenv(
    "ORIGEM_VISTA_PELO_DESTINO", "host=origem port=5432 dbname=loja user=postgres password=postgres")

PUBLICACAO = "pub_loja"
ASSINATURA = "sub_loja"
TABELAS = ["clientes", "produtos", "pedidos", "itens_pedido"]


def conectar(dsn: str) -> psycopg.Connection:
    # Fuso e formato de data fixos: a reconciliação compara o texto das linhas
    # dos dois lados, e timestamptz vira texto conforme o TimeZone da sessão.
    return psycopg.connect(dsn, autocommit=True, options="-c TimeZone=UTC -c DateStyle=ISO")


def garantir_banco(dsn: str) -> None:
    """Cria o banco "loja" se ainda não existir (útil fora do Docker)."""
    nome = psycopg.conninfo.conninfo_to_dict(dsn)["dbname"]
    with psycopg.connect(make_conninfo(dsn, dbname="postgres"), autocommit=True) as conn:
        if not conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", [nome]).fetchone():
            conn.execute(f'CREATE DATABASE "{nome}"')
