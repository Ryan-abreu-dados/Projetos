select
    estacao_id,
    nome,
    cidade,
    uf,
    altitude_m,
    status,
    _extracao
from {{ source('raw', 'estacoes') }}
