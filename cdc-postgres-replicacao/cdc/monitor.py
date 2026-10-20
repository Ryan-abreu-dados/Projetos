"""Saúde da replicação, vista dos dois lados.

Uso: python -m cdc.monitor
"""
import json

from cdc.config import ASSINATURA, DESTINO, ORIGEM, conectar


def estado_origem(origem) -> dict:
    """O slot é o "marcador de leitura" do destino na origem.

    wal_retido_mb é quanto WAL a origem é obrigada a guardar porque o destino
    ainda não confirmou. Se o destino some, esse número cresce até encher o disco
    (ou até o limite max_slot_wal_keep_size, quando o slot é invalidado).
    """
    linha = origem.execute("""
        SELECT s.active,
               s.wal_status,
               pg_wal_lsn_diff(pg_current_wal_lsn(), s.restart_lsn)         AS wal_retido_bytes,
               pg_wal_lsn_diff(pg_current_wal_lsn(), s.confirmed_flush_lsn) AS atraso_confirmado_bytes,
               r.state AS envio
        FROM pg_replication_slots s
        LEFT JOIN pg_stat_replication r ON r.pid = s.active_pid
        WHERE s.slot_name = %s
    """, [ASSINATURA]).fetchone()
    if not linha:
        return {"slot": "não existe"}
    ativo, wal_status, retido, atraso, envio = linha
    return {
        "slot_ativo": ativo,
        "wal_status": wal_status,
        "wal_retido_mb": round(float(retido) / 1024 / 1024, 2),
        "atraso_confirmado_kb": round(float(atraso) / 1024, 1),
        "envio": envio,
    }


def estado_destino(destino) -> dict:
    linha = destino.execute("""
        SELECT s.subenabled,
               st.pid IS NOT NULL AS worker_rodando,
               coalesce(ss.apply_error_count, 0) AS erros_ao_aplicar,
               coalesce(ss.sync_error_count, 0)  AS erros_na_copia_inicial
        FROM pg_subscription s
        LEFT JOIN pg_stat_subscription st ON st.subid = s.oid AND st.relid IS NULL
        LEFT JOIN pg_stat_subscription_stats ss ON ss.subid = s.oid
        WHERE s.subname = %s
    """, [ASSINATURA]).fetchone()
    if not linha:
        return {"assinatura": "não existe"}
    return {"habilitada": linha[0], "worker_rodando": linha[1],
            "erros_ao_aplicar": linha[2], "erros_na_copia_inicial": linha[3]}


if __name__ == "__main__":
    with conectar(ORIGEM) as o, conectar(DESTINO) as d:
        print(json.dumps({"origem": estado_origem(o), "destino": estado_destino(d)}, ensure_ascii=False, indent=2))
