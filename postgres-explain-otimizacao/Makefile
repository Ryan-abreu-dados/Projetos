# Atalhos. No Windows sem make, rode os comandos da direita direto (veja o README).

.PHONY: run bench test down

run:            ## sobe tudo e roda o benchmark de 5 milhões de linhas
	docker compose up --build --abort-on-container-exit --exit-code-from bench

bench:          ## benchmark contra um banco já no ar (padrão: localhost:5433)
	python -m scripts.bench --linhas 5000000

test:           ## testes com 100 mil linhas (precisa do banco no ar)
	docker compose up -d --wait db
	python -m pytest -v

down:
	docker compose down -v
