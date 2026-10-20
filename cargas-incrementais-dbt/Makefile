# Atalhos. No Windows sem make, rode os comandos da direita direto (veja o README).

.PHONY: run test gerar rodar medir drift

run:            ## tudo dentro do Docker: gera, roda 2 vezes, mede
	docker compose up --build --abort-on-container-exit

test:           ## testes do pipeline inteiro (10 dias, 30 estações)
	python -m pytest -v

gerar:
	python -m pipeline gerar --dias 30 --estacoes 200

rodar:
	python -m pipeline rodar

medir:
	python -m pipeline medir

drift:          ## demonstração: coluna nova aparece no dia 20 e a carga para
	python -m pipeline gerar --dias 30 --estacoes 200 --drift-a-partir 20
	rm -f dados/estacoes.duckdb
	python -m pipeline rodar
