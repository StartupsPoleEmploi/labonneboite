COMPOSE_FILE = docker-compose.testing.yml:docker-compose.dev.yml
MAXFAIL      = 1000
TEST_FILES   =
TEST_ARGS    = --build --abort-on-container-exit --exit-code-from

help:
	poetry install --only help
	poetry run mkdocs serve --dev-addr '127.0.0.1:9999'

develop: 
	docker-compose -f docker-compose.dev.yml up --build

test:
	MAXFAIL=${MAXFAIL} TEST_FILES=${TEST_FILES} docker-compose -f docker-compose.testing.yml up ${TEST_ARGS} app; \
	  r=$$?; \
	  exit $$r

test-run:
	$(MAKE) test TEST_ARGS=--no-build

changelog:
	conventional-changelog -p conventionalcommit --i CHANGELOG.md -s
