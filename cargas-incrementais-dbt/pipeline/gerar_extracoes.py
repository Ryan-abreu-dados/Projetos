"""Gera extrações diárias sintéticas de uma rede de estações meteorológicas.

Cada dia vira uma pasta dados/extracoes/AAAA-MM-DD/ com dois CSVs:
  estacoes.csv  cadastro completo das estações naquele dia (muda de vez em quando)
  leituras.csv  leituras horárias que CHEGARAM naquele dia

Os problemas que o pipeline precisa aguentar são colocados de propósito:
  - leituras atrasadas: medidas num dia, entregues de 1 a 5 dias depois
  - retransmissões: a mesma leitura enviada duas vezes, idêntica
  - correções: a mesma leitura reenviada depois com outro valor (vale a última)
  - leituras inválidas: sensor com defeito (999.9 °C ou chuva negativa)
  - cadastro que muda: estação renomeada, altitude corrigida, manutenção

O que o pipeline deveria produzir fica em dados/gabarito.json, calculado aqui
em Python, independente do SQL. Os testes comparam o resultado com ele.
"""
import argparse
import csv
import json
import math
import random
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ / "dados"

# Probabilidades por leitura. Mudar aqui muda o gabarito junto.
P_ATRASADA = 0.05     # entregue de 1 a 5 dias depois
P_DUPLICADA = 0.03    # enviada duas vezes, idêntica
P_CORRECAO = 0.01     # reenviada 1 ou 2 dias depois com outro valor
P_INVALIDA = 0.005    # sensor com defeito

CIDADES = [
    ("Manaus", "AM", 92, 27), ("Belém", "PA", 10, 27), ("Fortaleza", "CE", 21, 27),
    ("Recife", "PE", 4, 26), ("Salvador", "BA", 8, 26), ("Brasília", "DF", 1172, 21),
    ("Goiânia", "GO", 749, 24), ("Cuiabá", "MT", 165, 27), ("Belo Horizonte", "MG", 852, 22),
    ("Rio de Janeiro", "RJ", 5, 25), ("São Paulo", "SP", 760, 21), ("Curitiba", "PR", 934, 18),
    ("Florianópolis", "SC", 3, 22), ("Porto Alegre", "RS", 10, 21), ("Campo Grande", "MS", 532, 24),
    ("Natal", "RN", 30, 27), ("Teresina", "PI", 72, 28), ("Palmas", "TO", 230, 27),
    ("Porto Velho", "RO", 85, 26), ("Boa Vista", "RR", 85, 28),
]


def _estacoes_iniciais(rng: random.Random, quantidade: int) -> dict:
    estacoes = {}
    for i in range(1, quantidade + 1):
        cidade, uf, altitude, temp_media = CIDADES[(i - 1) % len(CIDADES)]
        estacoes[f"EST{i:03d}"] = {
            "estacao_id": f"EST{i:03d}",
            "nome": f"Estação {cidade} {(i - 1) // len(CIDADES) + 1:02d}",
            "cidade": cidade,
            "uf": uf,
            "altitude_m": altitude + rng.randint(-30, 30),
            "status": "ativa",
            "_temp_media": temp_media,  # só para gerar temperatura plausível, não vai pro CSV
        }
    return estacoes


def _mudar_cadastro(rng: random.Random, estacoes: dict, dia_idx: int, voltas: dict):
    """Aplica as mudanças de cadastro do dia. voltas guarda quando cada manutenção acaba."""
    for estacao_id, dia_volta in list(voltas.items()):
        if dia_volta == dia_idx:
            estacoes[estacao_id]["status"] = "ativa"
            del voltas[estacao_id]
    for _ in range(rng.choice([0, 1, 1, 2])):
        e = estacoes[rng.choice(sorted(estacoes))]
        if e["status"] != "ativa":
            continue
        tipo = rng.choice(["renomeada", "altitude", "manutencao"])
        if tipo == "renomeada":
            e["nome"] = f"Estação {e['cidade']} {rng.choice(['Aeroporto', 'Centro', 'Campus', 'Porto'])}"
        elif tipo == "altitude":
            e["altitude_m"] += rng.choice([-12, -5, 5, 12])
        else:
            e["status"] = "manutencao"
            voltas[e["estacao_id"]] = dia_idx + rng.randint(2, 4)


def gerar(dias: int = 30, quantidade_estacoes: int = 200, inicio: date = date(2026, 1, 1),
          drift_a_partir: int | None = None, pasta: Path = PASTA_DADOS, semente: int = 42) -> dict:
    rng = random.Random(semente)
    pasta_extracoes = pasta / "extracoes"
    if pasta_extracoes.exists():
        shutil.rmtree(pasta_extracoes)
    datas = [inicio + timedelta(days=i) for i in range(dias)]

    estacoes = _estacoes_iniciais(rng, quantidade_estacoes)
    voltas: dict = {}
    cadastros = []                               # cadastro de cada dia
    entregas = {i: [] for i in range(dias)}      # dia de chegada -> linhas de leitura
    gabarito_chaves = {}                         # (estacao, medido_em) -> lista de (dia_chegada, linha)
    contagem = {"atrasadas": 0, "duplicadas": 0, "correcoes": 0, "invalidas": 0}

    for d, dia in enumerate(datas):
        if d > 0:
            _mudar_cadastro(rng, estacoes, d, voltas)
        cadastros.append([{k: v for k, v in e.items() if not k.startswith("_")} for e in estacoes.values()])

        for e in estacoes.values():
            if e["status"] != "ativa":
                continue  # estação em manutenção não manda leitura
            for hora in range(24):
                medido_em = datetime.combine(dia, datetime.min.time()) + timedelta(hours=hora)
                temperatura = round(e["_temp_media"] + 5 * math.sin((hora - 9) / 24 * 2 * math.pi)
                                    + rng.gauss(0, 1.5), 1)
                chuva = round(max(0.0, rng.gauss(-2, 4)), 1)
                linha = {"estacao_id": e["estacao_id"], "medido_em": medido_em.isoformat(sep=" "),
                         "temperatura_c": temperatura, "chuva_mm": chuva}
                chave = (e["estacao_id"], linha["medido_em"])
                envios = []

                if rng.random() < P_INVALIDA:
                    contagem["invalidas"] += 1
                    if rng.random() < 0.5:
                        linha["temperatura_c"] = 999.9
                    else:
                        linha["chuva_mm"] = -1.0
                    envios.append((d, linha))
                else:
                    chegada = d + rng.randint(1, 5) if rng.random() < P_ATRASADA else d
                    if chegada != d:
                        contagem["atrasadas"] += 1
                    envios.append((chegada, linha))
                    if rng.random() < P_DUPLICADA:
                        contagem["duplicadas"] += 1
                        envios.append((chegada + rng.randint(0, 1), dict(linha)))
                    if rng.random() < P_CORRECAO:
                        contagem["correcoes"] += 1
                        corrigida = dict(linha, temperatura_c=round(temperatura + rng.choice([-2.0, -1.5, 1.5, 2.0]), 1))
                        # a correção sempre chega depois de qualquer outro envio da mesma leitura
                        ultimo_envio = max(dia_envio for dia_envio, _ in envios)
                        envios.append((ultimo_envio + rng.randint(1, 2), corrigida))

                for dia_chegada, linha_enviada in envios:
                    if dia_chegada < dias:  # o que chegaria depois do último dia fica fora do período
                        entregas[dia_chegada].append(linha_enviada)
                        gabarito_chaves.setdefault(chave, []).append((dia_chegada, linha_enviada))

    # Grava os arquivos de cada dia
    for d, dia in enumerate(datas):
        destino = pasta_extracoes / dia.isoformat()
        destino.mkdir(parents=True)
        colunas_cad = ["estacao_id", "nome", "cidade", "uf", "altitude_m", "status"]
        with open(destino / "estacoes.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=colunas_cad)
            w.writeheader()
            w.writerows(cadastros[d])

        linhas = entregas[d]
        rng.shuffle(linhas)  # a ordem de chegada não é a ordem da medição
        colunas = ["estacao_id", "medido_em", "temperatura_c", "chuva_mm"]
        if drift_a_partir is not None and d + 1 >= drift_a_partir:
            colunas.append("umidade_pct")  # coluna nova que ninguém avisou
            linhas = [dict(l, umidade_pct=rng.randint(30, 100)) for l in linhas]
        with open(destino / "leituras.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=colunas)
            w.writeheader()
            w.writerows(linhas)

    gabarito = _calcular_gabarito(cadastros, gabarito_chaves, entregas, contagem)
    (pasta / "gabarito.json").write_text(json.dumps(gabarito, ensure_ascii=False, indent=2), encoding="utf-8")
    return gabarito


def _valida(linha: dict) -> bool:
    return -40 <= linha["temperatura_c"] <= 60 and 0 <= linha["chuva_mm"] <= 500


def _calcular_gabarito(cadastros, chaves, entregas, contagem) -> dict:
    # Versões de cadastro: uma nova sempre que algum atributo muda de um dia para o outro
    versoes = {}
    anterior = {}
    for cadastro in cadastros:
        for e in cadastro:
            if anterior.get(e["estacao_id"]) != e:
                versoes[e["estacao_id"]] = versoes.get(e["estacao_id"], 0) + 1
            anterior[e["estacao_id"]] = e

    # Para cada leitura vale o último envio que chegou; se ele é inválido, vai para rejeitadas
    validas, invalidas, valor_final = 0, 0, {}
    for chave, envios in chaves.items():
        ultimo = max(envios, key=lambda x: x[0])[1]
        if _valida(ultimo):
            validas += 1
            valor_final[f"{chave[0]}|{chave[1]}"] = ultimo["temperatura_c"]
        else:
            invalidas += 1

    corrigidas = {k: v for k, v in valor_final.items()
                  if len({e[1]["temperatura_c"] for e in chaves[tuple(k.split("|"))]}) > 1}
    return {
        "linhas_enviadas": sum(len(v) for v in entregas.values()),
        "leituras_validas_unicas": validas,
        "leituras_rejeitadas": invalidas,
        "versoes_por_estacao": versoes,
        "total_versoes": sum(versoes.values()),
        "temperatura_final_das_corrigidas": corrigidas,
        "injetado": contagem,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dias", type=int, default=30)
    parser.add_argument("--estacoes", type=int, default=200)
    parser.add_argument("--drift-a-partir", type=int, default=None,
                        help="dia (1, 2, ...) em que a coluna nova umidade_pct aparece")
    args = parser.parse_args()
    g = gerar(args.dias, args.estacoes, drift_a_partir=args.drift_a_partir)
    print(f"{args.dias} extrações geradas: {g['linhas_enviadas']:,} linhas de leitura, "
          f"{g['leituras_validas_unicas']:,} leituras válidas únicas")
