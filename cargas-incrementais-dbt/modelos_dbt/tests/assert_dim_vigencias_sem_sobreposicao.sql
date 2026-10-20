-- Reprova se duas versões da mesma estação valem ao mesmo tempo
-- (o período de uma começa antes do fim da outra).
select a.estacao_id, a.valido_de, b.valido_de as outra_valido_de
from {{ ref('dim_estacoes') }} a
join {{ ref('dim_estacoes') }} b
  on a.estacao_id = b.estacao_id
 and a.versao_id <> b.versao_id
 and a.valido_de <= b.valido_de
 and (a.valido_ate is null or a.valido_ate > b.valido_de)
