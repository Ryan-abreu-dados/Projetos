-- Staging: só nomeia e tipa. Nenhuma regra de negócio aqui.
select
    estacao_id,
    medido_em,
    temperatura_c,
    chuva_mm,
    _extracao
from {{ source('raw', 'leituras') }}
