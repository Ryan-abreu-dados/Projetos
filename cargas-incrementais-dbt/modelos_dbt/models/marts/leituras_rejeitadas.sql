{#
  Leituras recusadas pela regra de validade, com o motivo. Ficam guardadas em vez
  de sumir: dá para contar, investigar o sensor e reprocessar se a regra mudar.
#}
{{ config(
    materialized='incremental',
    unique_key=['estacao_id', 'medido_em', '_extracao'],
    incremental_strategy='delete+insert'
) }}

with novas as (
    select * from {{ ref('stg_leituras') }}
    {% if is_incremental() %}
    where _extracao > (select coalesce(max(_extracao), date '1900-01-01') from {{ this }})
    {% endif %}
),

ultima_versao as (
    select * from novas
    qualify row_number() over (partition by estacao_id, medido_em order by _extracao desc) = 1
)

select
    estacao_id,
    medido_em,
    temperatura_c,
    chuva_mm,
    _extracao,
    case
        when temperatura_c is null or chuva_mm is null then 'valor nulo'
        when temperatura_c not between -40 and 60 then 'temperatura fora da faixa física'
        else 'chuva negativa ou acima de 500 mm'
    end as motivo
from ultima_versao
where not {{ leitura_valida() }}
