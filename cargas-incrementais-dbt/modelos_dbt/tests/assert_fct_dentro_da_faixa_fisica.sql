-- Reprova se uma leitura fora da faixa física passou para a fato.
select *
from {{ ref('fct_leituras') }}
where not {{ leitura_valida() }}
