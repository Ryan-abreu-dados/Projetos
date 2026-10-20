{#
  Regra de validade de uma leitura, num lugar só: a fato usa para aceitar e a
  tabela de rejeitadas usa para recusar. coalesce garante que valor nulo conta
  como inválido (sem ele, a linha não entraria em nenhuma das duas).
#}
{% macro leitura_valida() %}
    coalesce(temperatura_c between -40 and 60 and chuva_mm between 0 and 500, false)
{% endmacro %}
