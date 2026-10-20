-- Tabelas do projeto. Só as chaves primárias nascem com índice:
-- os outros índices aparecem como correção de cada caso.

DROP TABLE IF EXISTS corridas;
DROP TABLE IF EXISTS motoristas;
DROP TABLE IF EXISTS zonas;

CREATE TABLE zonas (
    id      smallint PRIMARY KEY,
    nome    text NOT NULL,
    regiao  text NOT NULL
);

CREATE TABLE motoristas (
    id             integer PRIMARY KEY,
    categoria      text NOT NULL,          -- comum, executivo, premium
    cadastrado_em  date NOT NULL
);

CREATE TABLE corridas (
    id               bigint PRIMARY KEY,
    motorista_id     integer NOT NULL,
    zona_origem_id   smallint NOT NULL,
    zona_destino_id  smallint NOT NULL,
    iniciada_em      timestamp NOT NULL,
    duracao_min      integer NOT NULL,
    distancia_km     numeric(6,2) NOT NULL,
    valor_total      numeric(10,2) NOT NULL,
    forma_pagamento  text NOT NULL,        -- cartao e dinheiro (pix chega no caso 3)
    avaliacao        smallint              -- 1 a 5, pode ser nula
);
