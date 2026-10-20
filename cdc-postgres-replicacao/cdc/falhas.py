"""Cenários de falha medidos com a loja em movimento.

1. Destino parado: a assinatura é desligada por N segundos enquanto a origem
   continua recebendo pedidos. Mede o WAL retido no slot e quanto tempo o
   destino leva para alcançar a origem depois de religado.
2. Conexão derrubada: o processo que envia as mudanças na origem é encerrado.
   Mede quanto tempo a replicação leva para voltar sozinha.
"""
import time

from cdc import sonda
from cdc.config import ASSINATURA, DESTINO, ORIGEM, conectar
from cdc.monitor import estado_origem
from cdc.simulador import SimuladorEmSegundoPlano


def destino_parado(segundos: float = 30, taxa: float = 200) -> dict:
    with conectar(ORIGEM) as origem, conectar(DESTINO) as destino:
        with SimuladorEmSegundoPlano(taxa) as sim:
            time.sleep(2)
            retido_antes = estado_origem(origem)["wal_retido_mb"]
            destino.execute(f"ALTER SUBSCRIPTION {ASSINATURA} DISABLE")
            operacoes_antes = sim.operacoes
            time.sleep(segundos)
            operacoes_na_pausa = sim.operacoes - operacoes_antes
            retido_na_pausa = estado_origem(origem)["wal_retido_mb"]

            destino.execute(f"ALTER SUBSCRIPTION {ASSINATURA} ENABLE")
            recuperacao = sonda.sincronizar(origem, destino, limite_s=600)
    return {
        "pausa_s": segundos,
        "taxa_alvo_ops_s": taxa,
        "operacoes_durante_a_pausa": operacoes_na_pausa,
        "wal_retido_antes_mb": retido_antes,
        "wal_retido_no_fim_da_pausa_mb": retido_na_pausa,
        "recuperacao_s": None if recuperacao is None else round(recuperacao, 2),
    }


def conexao_derrubada(taxa: float = 200) -> dict:
    with conectar(ORIGEM) as origem, conectar(DESTINO) as destino:
        with SimuladorEmSegundoPlano(taxa):
            time.sleep(2)
            encerrados = origem.execute(
                "SELECT count(pg_terminate_backend(pid)) FROM pg_stat_replication WHERE application_name = %s",
                [ASSINATURA]).fetchone()[0]
            volta = sonda.sincronizar(origem, destino, limite_s=120)
    return {"processos_encerrados": encerrados, "volta_s": None if volta is None else round(volta, 2)}


if __name__ == "__main__":
    print(destino_parado())
    print(conexao_derrubada())
