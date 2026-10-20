{#
  Dimensão de estações com histórico (SCD tipo 2): cada mudança de cadastro vira
  uma versão nova, com o período em que valeu (valido_de até valido_ate).

  Incremental: a cada execução entram só as extrações novas. Para saber se algo
  mudou, junto o que chegou com a versão vigente de cada estação e comparo cada
  dia com o anterior pelo hash dos atributos. Só sobra linha onde o hash mudou.

  Não usei `dbt snapshot` porque ele só enxerga o estado da origem no momento em
  que roda: carregar 30 dias de uma vez guardaria só o último. Aqui cada dia de
  extração conta, então recarregar o mês inteiro dá o mesmo histórico.
#}
{{ config(
    materialized='incremental',
    unique_key='versao_id',
    incremental_strategy='delete+insert'
) }}

with novas as (
    select estacao_id, nome, cidade, uf, altitude_m, status, _extracao as visto_em
    from {{ ref('stg_estacoes') }}
    {% if is_incremental() %}
    where _extracao > (select max(processado_ate) from {{ this }})
    {% endif %}
),

{% if is_incremental() %}
vigentes as (
    -- a versão atual de cada estação entra na comparação com o que chegou
    select estacao_id, nome, cidade, uf, altitude_m, status, valido_de as visto_em
    from {{ this }}
    where vigente
),
{% endif %}

historico as (
    select * from novas
    {% if is_incremental() %}
    union all
    select * from vigentes
    {% endif %}
),

com_hash as (
    select
        *,
        md5(concat_ws('|', nome, cidade, uf, cast(altitude_m as varchar), status)) as hash_atributos
    from historico
),

comparado as (
    select
        *,
        lag(hash_atributos) over (partition by estacao_id order by visto_em) as hash_anterior
    from com_hash
),

versoes as (
    select * from comparado
    where hash_anterior is null or hash_atributos <> hash_anterior
)

select
    md5(estacao_id || '|' || cast(visto_em as varchar)) as versao_id,
    estacao_id,
    nome,
    cidade,
    uf,
    altitude_m,
    status,
    visto_em as valido_de,
    lead(visto_em) over (partition by estacao_id order by visto_em) as valido_ate,
    lead(visto_em) over (partition by estacao_id order by visto_em) is null as vigente,
    -- watermark da dimensão: até qual extração ela já processou
    {% if is_incremental() %}
    coalesce((select max(visto_em) from novas), (select max(processado_ate) from {{ this }})) as processado_ate
    {% else %}
    (select max(visto_em) from novas) as processado_ate
    {% endif %}
from versoes
