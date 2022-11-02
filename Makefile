COMPOSE_FILE=docker-compose.testing.yml:docker-compose.dev.yml
MAXFAIL=1000

help:
	poetry install --only help
	poetry run mkdocs serve --dev-addr '127.0.0.1:9999'

develop: 
	docker-compose -f docker-compose.dev.yml down \
	&& docker-compose -f docker-compose.dev.yml up --build

test: test-init test-run

test-init:
	docker-compose -f docker-compose.testing.yml up --build --no-start

test-run:
	MAXFAIL=${MAXFAIL} docker-compose -f docker-compose.testing.yml up --no-build --abort-on-container-exit --exit-code-from app; \
	  r=$$?; \
	  exit $$r
