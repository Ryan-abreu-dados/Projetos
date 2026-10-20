"""Simula o movimento de uma loja na origem: pedidos novos, mudança de status,
reajuste de preço, clientes novos e exclusão de pedidos cancelados.

Uso: python -m cdc.simulador --segundos 60 --taxa 200   (operações por segundo)

Cada operação é uma transação. O destino recebe só o que foi confirmado (commit).
"""
import argparse
import random
import threading
import time

from cdc.config import ORIGEM, conectar

STATUS = ["novo", "pago", "enviado", "entregue", "cancelado"]


class Simulador:
    def __init__(self, taxa: float = 200, semente: int = 7):
        self.taxa = taxa
        self.rng = random.Random(semente)
        self.operacoes = 0

    def _maximo(self, conn, tabela: str) -> int:
        return conn.execute(f"SELECT coalesce(max(id), 1) FROM {tabela}").fetchone()[0]

    def _uma_operacao(self, conn, limites: dict) -> None:
        r = self.rng.random()
        if r < 0.50:  # pedido novo com 1 a 4 itens
            with conn.transaction():
                pedido_id = conn.execute(
                    "INSERT INTO pedidos (cliente_id, status, total) VALUES (%s, 'novo', 0) RETURNING id",
                    [self.rng.randint(1, limites["clientes"])]).fetchone()[0]
                for _ in range(self.rng.randint(1, 4)):
                    conn.execute("""
                        INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario)
                        SELECT %s, id, %s, preco FROM produtos WHERE id = %s
                    """, [pedido_id, self.rng.randint(1, 3), self.rng.randint(1, limites["produtos"])])
                conn.execute("""
                    UPDATE pedidos SET total = (SELECT coalesce(sum(quantidade * preco_unitario), 0)
                                                FROM itens_pedido WHERE pedido_id = %s)
                    WHERE id = %s
                """, [pedido_id, pedido_id])
            limites["pedidos"] = pedido_id
        elif r < 0.75:  # pedido recente muda de status
            conn.execute("UPDATE pedidos SET status = %s, atualizado_em = now() WHERE id = %s",
                         [self.rng.choice(STATUS), self.rng.randint(max(1, limites["pedidos"] - 2000), limites["pedidos"])])
        elif r < 0.85:  # reajuste de preço e estoque
            conn.execute("""
                UPDATE produtos SET preco = round(preco * %s::numeric, 2), estoque = %s, atualizado_em = now()
                WHERE id = %s
            """, [self.rng.uniform(0.9, 1.1), self.rng.randint(0, 500), self.rng.randint(1, limites["produtos"])])
        elif r < 0.95:  # cliente novo
            limites["clientes"] = conn.execute(
                "INSERT INTO clientes (nome, email, cidade) VALUES (%s, %s, %s) RETURNING id",
                [f"Cliente novo {self.operacoes}", f"novo{self.operacoes}@exemplo.com", "São Paulo"]).fetchone()[0]
        else:  # pedido cancelado é apagado (os itens saem junto, em cascata)
            conn.execute("DELETE FROM pedidos WHERE id = %s AND status = 'cancelado'",
                         [self.rng.randint(1, limites["pedidos"])])

    def rodar(self, segundos: float | None = None, parar: threading.Event | None = None) -> int:
        """Roda até passar `segundos` ou até `parar` ser acionado. Devolve quantas operações fez."""
        with conectar(ORIGEM) as conn:
            limites = {t: self._maximo(conn, t) for t in ("clientes", "produtos", "pedidos")}
            inicio = proximo = time.perf_counter()
            while True:
                if segundos is not None and time.perf_counter() - inicio >= segundos:
                    break
                if parar is not None and parar.is_set():
                    break
                self._uma_operacao(conn, limites)
                self.operacoes += 1
                proximo += 1 / self.taxa
                espera = proximo - time.perf_counter()
                if espera > 0:
                    time.sleep(espera)
        return self.operacoes


class SimuladorEmSegundoPlano:
    """Roda o simulador numa thread: `with SimuladorEmSegundoPlano(200) as sim: ...`"""

    def __init__(self, taxa: float = 200):
        self.simulador = Simulador(taxa)
        self.parar = threading.Event()
        self.thread = threading.Thread(target=self.simulador.rodar, kwargs={"parar": self.parar}, daemon=True)

    def __enter__(self):
        self.inicio = time.perf_counter()
        self.thread.start()
        return self

    def __exit__(self, *erro):
        self.parar.set()
        self.thread.join()
        self.duracao_s = time.perf_counter() - self.inicio

    @property
    def operacoes(self) -> int:
        return self.simulador.operacoes


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--segundos", type=float, default=60)
    parser.add_argument("--taxa", type=float, default=200)
    args = parser.parse_args()
    feitas = Simulador(args.taxa).rodar(args.segundos)
    print(f"{feitas} operações em {args.segundos} s")
