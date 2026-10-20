"""Testes da replicação: o caminho feliz, as falhas e os casos que travam."""
import time
from decimal import Decimal

from cdc import sonda
from cdc.config import ASSINATURA, TABELAS
from cdc.monitor import estado_destino, estado_origem
from cdc.reconciliar import reconciliar, total_divergencias
from cdc.simulador import Simulador


def contar(conn, tabela):
    return conn.execute(f"SELECT count(*) FROM {tabela}").fetchone()[0]


def test_copia_inicial_trouxe_tudo(ambiente):
    assert ambiente["origem"] == ambiente["destino"]


def test_insert_update_delete_chegam(origem, destino):
    cliente_id = origem.execute(
        "INSERT INTO clientes (nome, email) VALUES ('Teste', 't@exemplo.com') RETURNING id").fetchone()[0]
    origem.execute("UPDATE produtos SET preco = 123.45 WHERE id = 1")
    origem.execute("DELETE FROM pedidos WHERE id = 10")
    assert sonda.sincronizar(origem, destino) is not None

    assert destino.execute("SELECT nome FROM clientes WHERE id = %s", [cliente_id]).fetchone() == ("Teste",)
    assert destino.execute("SELECT preco FROM produtos WHERE id = 1").fetchone()[0] == Decimal("123.45")
    assert destino.execute("SELECT count(*) FROM pedidos WHERE id = 10").fetchone()[0] == 0
    # os itens do pedido saíram em cascata na origem e a exclusão deles também chegou
    assert destino.execute("SELECT count(*) FROM itens_pedido WHERE pedido_id = 10").fetchone()[0] == 0


def test_carga_continua_sem_divergencia(origem, destino):
    Simulador(taxa=300).rodar(segundos=3)
    assert total_divergencias(reconciliar(origem, destino)) == 0


def test_divergencia_silenciosa_e_achada_e_corrigida(origem, destino):
    # escrever no destino não gera erro nenhum: a replicação continua "verde"
    destino.execute("UPDATE clientes SET cidade = 'errada' WHERE id IN (5, 6)")
    destino.execute("DELETE FROM itens_pedido WHERE id = 7")
    assert sonda.sincronizar(origem, destino) is not None
    assert estado_destino(destino)["erros_ao_aplicar"] == 0

    relatorio = reconciliar(origem, destino, corrigir=True)
    assert relatorio["clientes"]["diferentes"] == [5, 6]
    assert relatorio["itens_pedido"]["faltando_no_destino"] == [7]
    assert total_divergencias(reconciliar(origem, destino)) == 0


def test_linha_que_so_existe_no_destino_e_listada_e_nao_apagada(origem, destino):
    destino.execute("INSERT INTO produtos (id, nome, categoria, preco, estoque) "
                    "VALUES (900001, 'Só no destino', 'casa', 1, 1)")
    relatorio = reconciliar(origem, destino, corrigir=True)
    assert relatorio["produtos"]["so_no_destino"] == [900001]
    assert contar(destino, "produtos WHERE id = 900001") == 1
    destino.execute("DELETE FROM produtos WHERE id = 900001")


def test_destino_parado_acumula_wal_e_alcanca_depois(origem, destino):
    destino.execute(f"ALTER SUBSCRIPTION {ASSINATURA} DISABLE")
    try:
        retido_antes = estado_origem(origem)["wal_retido_mb"]
        Simulador(taxa=300).rodar(segundos=4)
        assert estado_origem(origem)["wal_retido_mb"] > retido_antes  # a origem guarda o WAL para o destino
        assert contar(destino, "pedidos") < contar(origem, "pedidos")  # destino ficou para trás
    finally:
        destino.execute(f"ALTER SUBSCRIPTION {ASSINATURA} ENABLE")
    assert sonda.sincronizar(origem, destino, limite_s=120) is not None
    assert total_divergencias(reconciliar(origem, destino)) == 0


def test_conexao_derrubada_volta_sozinha(origem, destino):
    encerrados = origem.execute(
        "SELECT count(pg_terminate_backend(pid)) FROM pg_stat_replication WHERE application_name = %s",
        [ASSINATURA]).fetchone()[0]
    assert encerrados == 1
    assert sonda.sincronizar(origem, destino, limite_s=60) is not None


def test_conflito_de_chave_trava_ate_alguem_resolver(origem, destino):
    # alguém grava no destino uma linha com o mesmo id que a origem vai usar
    destino.execute("INSERT INTO clientes (id, nome, email) VALUES (800001, 'Intruso', 'x@exemplo.com')")
    origem.execute("INSERT INTO clientes (id, nome, email) VALUES (800001, 'Legítimo', 'y@exemplo.com')")

    assert sonda.sincronizar(origem, destino, limite_s=8) is None  # nada mais passa
    assert estado_destino(destino)["erros_ao_aplicar"] > 0

    destino.execute("DELETE FROM clientes WHERE id = 800001")  # a correção é manual
    assert sonda.sincronizar(origem, destino, limite_s=60) is not None
    assert destino.execute("SELECT nome FROM clientes WHERE id = 800001").fetchone() == ("Legítimo",)


def test_coluna_nova_na_origem_trava_ate_existir_no_destino(origem, destino):
    origem.execute("ALTER TABLE produtos ADD COLUMN cor text")
    origem.execute("UPDATE produtos SET cor = 'azul' WHERE id = 2")
    assert sonda.sincronizar(origem, destino, limite_s=8) is None

    destino.execute("ALTER TABLE produtos ADD COLUMN cor text")  # DDL não replica: faço à mão
    assert sonda.sincronizar(origem, destino, limite_s=60) is not None
    assert destino.execute("SELECT cor FROM produtos WHERE id = 2").fetchone() == ("azul",)


def test_tabela_fora_da_publicacao_nao_replica_ate_ser_incluida(origem, destino):
    for conn in (origem, destino):
        conn.execute("CREATE TABLE avaliacoes (id bigint PRIMARY KEY, nota int)")
    origem.execute("INSERT INTO avaliacoes VALUES (1, 5), (2, 4)")
    assert sonda.sincronizar(origem, destino) is not None
    assert contar(destino, "avaliacoes") == 0  # sem erro e sem dado

    origem.execute("ALTER PUBLICATION pub_loja ADD TABLE avaliacoes")
    destino.execute(f"ALTER SUBSCRIPTION {ASSINATURA} REFRESH PUBLICATION")  # copia o que já existe
    inicio = time.perf_counter()
    while contar(destino, "avaliacoes") < 2 and time.perf_counter() - inicio < 30:
        time.sleep(0.2)
    assert contar(destino, "avaliacoes") == 2


def test_tudo_igual_no_fim(origem, destino):
    assert total_divergencias(reconciliar(origem, destino)) == 0
    for tabela in TABELAS:
        assert contar(origem, tabela) == contar(destino, tabela)
