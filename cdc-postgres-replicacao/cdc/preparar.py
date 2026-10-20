"""Monta tudo do zero: schema nos dois bancos, dados na origem, publicação e assinatura.

Uso: python -m cdc.preparar [--clientes 20000 --produtos 1000 --pedidos 100000]

Pode rodar quantas vezes quiser: apaga assinatura, publicação, slot e tabelas
antes de recriar.
"""
import argparse
import random
import time
from pathlib import Path

from faker import Faker

from cdc.config import (ASSINATURA, DESTINO, ORIGEM, ORIGEM_VISTA_PELO_DESTINO, PUBLICACAO, TABELAS,
                        conectar, garantir_banco)

SCHEMA = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"
CATEGORIAS = ["livros", "eletrônicos", "casa", "esporte", "brinquedos", "moda", "mercado"]
STATUS = ["novo", "pago", "enviado", "entregue", "cancelado"]


def limpar(origem, destino) -> None:
    # A assinatura sai primeiro: ao ser apagada ela também apaga o slot na origem
    destino.execute(f"DROP SUBSCRIPTION IF EXISTS {ASSINATURA}")
    origem.execute(f"DROP PUBLICATION IF EXISTS {PUBLICACAO}")
    origem.execute("SELECT pg_drop_replication_slot(slot_name) FROM pg_replication_slots "
                   "WHERE slot_name = %s AND NOT active", [ASSINATURA])
    schema = SCHEMA.read_text(encoding="utf-8")
    origem.execute(schema)
    destino.execute(schema)


def popular_origem(origem, clientes: int, produtos: int, pedidos: int, semente: int = 42) -> None:
    """Dados sintéticos com Faker. Os ids vão explícitos e depois as sequências são acertadas."""
    rng = random.Random(semente)
    fake = Faker("pt_BR")
    Faker.seed(semente)

    with origem.cursor() as cur:
        with cur.copy("COPY clientes (id, nome, email, cidade) FROM STDIN") as copia:
            for i in range(1, clientes + 1):
                copia.write_row((i, fake.name(), f"cliente{i}@exemplo.com", fake.city()))

        precos = {}
        with cur.copy("COPY produtos (id, nome, categoria, preco, estoque) FROM STDIN") as copia:
            for i in range(1, produtos + 1):
                precos[i] = round(rng.uniform(5, 800), 2)
                copia.write_row((i, f"Produto {i:05d}", rng.choice(CATEGORIAS), precos[i], rng.randint(0, 500)))

        itens = []
        with cur.copy("COPY pedidos (id, cliente_id, status, total) FROM STDIN") as copia:
            for p in range(1, pedidos + 1):
                total = 0
                for _ in range(rng.randint(1, 4)):
                    produto = rng.randint(1, produtos)
                    quantidade = rng.randint(1, 3)
                    itens.append((p, produto, quantidade, precos[produto]))
                    total += quantidade * precos[produto]
                copia.write_row((p, rng.randint(1, clientes), rng.choice(STATUS), round(total, 2)))

        with cur.copy("COPY itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) FROM STDIN") as copia:
            for item in itens:
                copia.write_row(item)

        # Com ids explícitos a sequência fica parada no 1: acerto para o próximo id livre
        for tabela in TABELAS:
            cur.execute(f"SELECT setval(pg_get_serial_sequence('{tabela}', 'id'), (SELECT max(id) FROM {tabela}))")


def criar_replicacao(origem, destino) -> None:
    # Publicação com lista explícita de tabelas: tabela nova não entra sem alguém decidir
    origem.execute(f"CREATE PUBLICATION {PUBLICACAO} FOR TABLE {', '.join(TABELAS)}, sonda_latencia")
    # A assinatura cria o slot na origem, copia as tabelas (cópia inicial) e passa a
    # receber as mudanças. O endereço é o que o SERVIDOR de destino usa para chegar à origem.
    destino.execute(f"CREATE SUBSCRIPTION {ASSINATURA} CONNECTION '{ORIGEM_VISTA_PELO_DESTINO}' "
                    f"PUBLICATION {PUBLICACAO}")


def esperar_copia_inicial(destino, limite_s: float = 300) -> float:
    """Espera todas as tabelas saírem da cópia inicial (estado 'r' = pronta)."""
    inicio = time.perf_counter()
    while time.perf_counter() - inicio < limite_s:
        pendentes, total = destino.execute("""
            SELECT count(*) FILTER (WHERE srsubstate <> 'r'), count(*)
            FROM pg_subscription_rel
        """).fetchone()
        if total == len(TABELAS) + 1 and pendentes == 0:
            return time.perf_counter() - inicio
        time.sleep(0.2)
    raise TimeoutError("a cópia inicial não terminou no tempo limite")


def contar(conn) -> dict:
    return {t: conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in TABELAS}


def preparar(clientes: int = 20_000, produtos: int = 1_000, pedidos: int = 100_000) -> dict:
    garantir_banco(ORIGEM)
    garantir_banco(DESTINO)
    with conectar(ORIGEM) as origem, conectar(DESTINO) as destino:
        limpar(origem, destino)
        inicio = time.perf_counter()
        popular_origem(origem, clientes, produtos, pedidos)
        carga_s = time.perf_counter() - inicio
        criar_replicacao(origem, destino)
        copia_s = esperar_copia_inicial(destino)
        return {"carga_origem_s": round(carga_s, 1), "copia_inicial_s": round(copia_s, 1),
                "origem": contar(origem), "destino": contar(destino)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--clientes", type=int, default=20_000)
    parser.add_argument("--produtos", type=int, default=1_000)
    parser.add_argument("--pedidos", type=int, default=100_000)
    args = parser.parse_args()
    print(preparar(args.clientes, args.produtos, args.pedidos))
