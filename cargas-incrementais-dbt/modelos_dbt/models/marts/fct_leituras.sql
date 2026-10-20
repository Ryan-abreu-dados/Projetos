{#
  Fato de leituras: uma linha por (estação, hora medida), sem duplicata.

  Watermark pela data de CHEGADA (_extracao), não pela hora da medição.
  Uma leitura atrasada tem medido_em antigo mas chega numa extração nova; se o
  filtro fosse por medido_em, ela ficaria para trás sem erro nenhum.

  delete+insert pela chave: se a mesma leitura chega de novo (retransmissão ou
  correção), a linha antiga sai e a mais recente entra. Rodar duas vezes não duplica.
#}
{{ config(
    materialized='incremental',
    unique_key=['estacao_id', 'medido_em'],
    incremental_strategy='delete+insert'
) }}

with novas as (
    select * from {{ ref('stg_leituras') }}
    {% if is_incremental() %}
    where _extracao > (select coalesce(max(_extracao), date '1900-01-01') from {{ this }})
    {% endif %}
),

ultima_versao as (
    -- dentro do lote, vale o envio mais recente de cada leitura
    select * from novas
    qualify row_number() over (partition by estacao_id, medido_em order by _extracao desc) = 1
)

select
    l.estacao_id,
    l.medido_em,
    d.versao_id as estacao_versao_id,  -- a versão do cadastro que valia na hora da medição
    l.temperatura_c,
    l.chuva_mm,
    l._extracao
from ultima_versao l
left join {{ ref('dim_estacoes') }} d
    on d.estacao_id = l.estacao_id
   and l.medido_em >= d.valido_de
   and (d.valido_ate is null or l.medido_em < d.valido_ate)
where {{ leitura_valida() }}
