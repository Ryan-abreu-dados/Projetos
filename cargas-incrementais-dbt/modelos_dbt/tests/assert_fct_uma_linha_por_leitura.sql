-- Reprova se alguma leitura (estação + hora) aparece mais de uma vez na fato.
select estacao_id, medido_em, count(*) as vezes
from {{ ref('fct_leituras') }}
group by estacao_id, medido_em
having count(*) > 1
