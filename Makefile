init: init-docs init-dev

init-docs:
	pip3 install mkdocs mkdocs-material

documentation: init-docs
	python3 -m mkdocs serve --dev-addr '127.0.0.1:9999'

init-dev:
	pip3 install poetry
	poetry install

test: database-test init-dev test-lint test-coverage test-package test-results

test-lint: 
	# lint
	poetry run flake8 --output-file flake8.txt || echo "FAILED flake"
	poetry run flake8_junit flake8.txt flake8.xml
	rm flake8.txt

test-coverage: database-alembic
	# unit test & coverage
	poetry run pytest --verbose --junitxml=pytest.xml --cov
	poetry run coverage xml
	
test-package:
	# build the package
	poetry build

test-results:
	# prepare test results
	mkdir -p testResults
	mv *.xml  ./testResults

# setting database 
database:
	docker-compose -f labonneboite/tests/docker-compose.db.yml up -d

database-alembic: 
	# update database with model
	cd labonneboite && LBB_ENV=test alembic upgrade head 
	
	# sytt: attempt at importing the sql files in db : --sql > tests/sql/00-alembic.sql || echo alembic done!
	


database-test:
	docker-compose -f labonneboite/tests/docker-compose.db.yml down
	docker-compose -f labonneboite/tests/docker-compose.db.yml up -d

populate-data-test:
	LBB_ENV=test alembic upgrade head --sql > migration.sql
	# alembic upgrade ae1027a6acf --sql > migration.sql
	$(MYSQL) -D lbb_test < ./labonneboite/alembic/sql/etablissements.sql
	LBB_ENV=test python ./labonneboite/scripts/create_index.py --full