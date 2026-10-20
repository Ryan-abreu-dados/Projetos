-- Reprova se alguma estação tem zero ou mais de uma versão vigente.
select estacao_id, count(*) filter (where vigente) as vigentes
from {{ ref('dim_estacoes') }}
group by estacao_id
having count(*) filter (where vigente) <> 1
