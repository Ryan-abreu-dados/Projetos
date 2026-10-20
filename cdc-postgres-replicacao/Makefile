# Atalhos. No Windows sem make, rode os comandos da direita direto (veja o README).

.PHONY: run test bancos monitor simular reconciliar down

run:            ## sobe tudo e roda o roteiro completo (resultados/resultados.md)
	docker compose up --build --abort-on-container-exit --exit-code-from demo

bancos:         ## só os dois bancos, para rodar os scripts da sua máquina
	docker compose up -d --wait origem destino

test: bancos    ## testes (recriam a base pequena a cada execução)
	python -m pytest -v

monitor:
	python -m cdc.monitor

simular:
	python -m cdc.simulador --segundos 60 --taxa 200

reconciliar:
	python -m cdc.reconciliar

down:
	docker compose down -v
