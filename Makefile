COMPOSE_FILE=docker-compose.testing.yml:docker-compose.dev.yml
MAXFAIL=1000

help:
	poetry install --only help
	poetry run mkdocs serve --dev-addr '127.0.0.1:9999'

develop: 
	docker-compose --profile dev down \
	&& docker-compose --profile dev up --build

test: test-init test-run

test-init:
	docker volume create --name=testResults
	docker-compose --profile test up --build --no-start

test-run:
	MAXFAIL=${MAXFAIL} docker-compose --profile test up --no-build --abort-on-container-exit --exit-code-from app; \
	  r=$$?; \
	  docker run --rm -v testResults:/testResults -v $$(pwd):/backup busybox tar -zcvf /backup/testResults.tar.gz /testResults; \
	  exit $$r
