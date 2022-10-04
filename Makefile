init: init-docs init-dev

init-docs:
	pip3 install mkdocs mkdocs-material

documentation: init-docs
	python3 -m mkdocs serve --dev-addr '127.0.0.1:9999'

develop: 
	docker-compose -f docker-compose.dev.yml down \
	docker-compose -f docker-compose.dev.yml build \
	&& docker-compose -f docker-compose.dev.yml up

test: 
	docker-compose -f docker-compose.testing.yml down \
	&& docker-compose -f docker-compose.testing.yml build \
	&& docker-compose -f docker-compose.testing.yml up --abort-on-container-exit --exit-code-from app

# PACKAGE_DIR = labonneboite
# LOCUST_HOST = http://localhost:5000

# DB_PORT = 3306
# DB_HOST = 127.0.0.1
# DB_USER = root
# DB_NAME = labonneboite
# MYSQL_PARAMS = -u ${DB_USER} --host ${DB_HOST} --port ${DB_PORT}
# MYSQL = mysql ${MYSQL_PARAMS}

# PYTHON = ${VIRTUAL_ENV}/bin/python
# export PYTHONPATH=.

# init: init-venv init-databases init-test-data

# init-databases: init-services data create-index

# init-services: services database-wait-mysql

# init-test-data: clear-data-test database-test populate-data-test

# init-venv:
# 	@test -n "${VENV}${VIRTUAL_ENV}" -a \( -e "${VENV}" -o -e "${VIRTUAL_ENV}" \) || (echo 'You are not in a virtual env. Continue ? ' && read r)
# 	pip install --upgrade pip
# 	pip install pip-tools
# 	${MAKE} requirements.dev.txt
# 	pip-sync requirements.dev.txt
# 	python setup.py develop

# # Requirements
# # ------------

# compile-requirements: requirements.txt
# compile-dev-requirements: requirements.dev.txt

# requirements.dev.txt: requirements.txt

# .SUFFIXES: .in .txt
# .in.txt:
# 	pip-compile -o $@ -v $<

# # Services and data
# # -----------------

# services:
# 	docker-compose up -d elasticsearch mysql

# database: databases
# databases: database-dev database-test

# database-wait-mysql:
# 	until mysqladmin ping -u ${DB_USER} --host ${DB_HOST} --port ${DB_PORT}; \
# 	do \
# 		echo wait 1; \
# 		sleep 1; \
# 	done

# database-dev: init-services
# 	$(MYSQL) -e 'CREATE DATABASE IF NOT EXISTS labonneboite DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;'
# 	$(MYSQL) -e 'GRANT ALL ON labonneboite.* TO "labonneboite"@"%" IDENTIFIED BY "labonneboite";'

# database-test: init-services
# 	$(MYSQL) -e 'CREATE DATABASE IF NOT EXISTS lbb_test DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;'
# 	$(MYSQL) -e 'GRANT ALL ON lbb_test.* TO "lbb_test"@"%" IDENTIFIED BY "";'

# data: databases alembic-migrate populate-data-dev

# populate-data-dev:
# 	$(MYSQL) -D ${DB_NAME} < ./labonneboite/alembic/sql/etablissements.sql
# 	LBB_ENV=development python ./labonneboite/scripts/create_index.py --full

# populate-data-test:
# 	LBB_ENV=test alembic upgrade head
# 	$(MYSQL) -D lbb_test < ./labonneboite/alembic/sql/etablissements.sql
# 	LBB_ENV=test python ./labonneboite/scripts/create_index.py --full

# populate-data-test-selenium:
# 	LBB_ENV=test alembic upgrade head
# 	$(MYSQL) -D lbb_test < ./labonneboite/alembic/sql/etablissements_tests_selenium.sql
# 	LBB_ENV=test SELENIUM_IS_SETUP=1 python ./labonneboite/scripts/create_index.py --full

# data-dev:
# 	echo "-- this script should only run in local development and AFTER all migrations have completed" >  ./labonneboite/alembic/sql/etablissements.sql
# 	echo "" >>  ./labonneboite/alembic/sql/etablissements.sql
# 	echo "-- this only injects data in existing table etablissements" >>  ./labonneboite/alembic/sql/etablissements.sql
# 	echo "" >>  ./labonneboite/alembic/sql/etablissements.sql
# 	mysqldump ${MYSQL_PARAMS} --no-create-info --column-statistics=0 --complete-insert ${DB_NAME} etablissements  | sed -r 's/LOCK TABLES (`[^`]+`) WRITE;/\0\nTRUNCATE TABLE \1;/g' | sed 's$$VALUES ($$VALUES\n    ($$g' | sed 's$$),($$),\n    ($$g' >> ./labonneboite/alembic/sql/etablissements.sql

# dev-replace-db:
# 	echo 'DROP DATABASE IF EXISTS ${DEST_DB};' | mysql ${MYSQL_PARAMS};
# 	mysqladmin ${MYSQL_PARAMS} create ${DEST_DB};
# 	mysqldump ${MYSQL_PARAMS} --column-statistics=0 ${SOURCE_DB} | mysql ${MYSQL_PARAMS} ${DEST_DB};


# dev-create-backup:
# 	$(MAKE) dev-replace-db DEST_DB=labonneboite_backup SOURCE_DB=${DB_NAME}

# dev-restore-backup:
# 	$(MAKE) dev-replace-db DEST_DB=${DB_NAME} SOURCE_DB=labonneboite_backup

# clear-data: clear-data-dev clear-data-test

# clear-data-dev: services
# 	$(MYSQL) -e 'DROP DATABASE IF EXISTS labonneboite;'

# clear-data-test: services
# 	$(MYSQL) -e 'DROP DATABASE IF EXISTS lbb_test;'
# 	$(MAKE) database-test

# rebuild-data-dev : clear-data-dev database-dev alembic-migrate populate-data-dev

# rebuild-data-test : clear-data-test database-test

# rebuild-data: rebuild-data-test rebuild-data-dev

# stop-services:
# 	docker-compose stop

# # Cleanup
# # -------

# clean:
# 	find $(PACKAGE_DIR) "(" -name "*.pyc" -or -name "*.pyo" -or -name "*.mo" -or -name "*.so" ")" -delete
# 	find $(PACKAGE_DIR) -type d -empty -delete
# 	find $(PACKAGE_DIR) -name __pycache__ -delete

# clean-pyc:
# 	find $(PACKAGE_DIR) "(" -name "*.pyc" ")" -delete

# clean-services: stop-services ## Delete containers and attached volumes
# 	docker-compose rm --force -v

# # Code quality
# # ------------
# LINT_FILES ?= labonneboite

# lint: lint-flake8 lint-mypy  ## Lint and type check the project

# lint-flake8:
# 	${PYTHON_ENV} ${PYTHON} -m flake8 ${LINT_FILES}


# lint-mypy:
# 	${PYTHON_ENV} ${PYTHON} -m mypy --config-file=setup.cfg ${LINT_FILES}

# # Run pylint on the whole project.
# pylint-all:
# 	pylint --rcfile=.pylintrc --reports=no --output-format=colorized $(PACKAGE_DIR) || true

# # Run pylint on a specific file, e.g.:
# # make pylint FILE=labonneboite/web/app.py
# pylint:
# 	pylint --rcfile=.pylintrc --reports=no --output-format=colorized $(FILE) || true


# # Local dev
# # ---------

# serve-web-app: services
# 	LBB_ENV=development python labonneboite/web/app.py

# create-sitemap:
# 	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/create_sitemap.py sitemap

# prepare-mailing-data:
# 	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/prepare_mailing_data.py

# create-index:
# 	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/create_index.py

# create-index-from-scratch:
# 	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/create_index.py --full

# create-index-from-scratch-with-profiling:
# 	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/create_index.py --full --profile

# create-index-from-scratch-with-profiling-on-staging:
# 	ssh deploy@lbbstaging -t 'bash -c "\
#         cd && source /home/deploy/config/labonneboite/bin/activate && \
#         export LBB_ENV=staging && export LBB_SETTINGS=/home/deploy/config/lbb_staging_settings.py && \
#         cd /home/deploy/code/current/labonneboite/labonneboite && \
#         time python scripts/create_index.py --full --profile"' && \
#     scp deploy@lbbstaging:/home/deploy/code/current/labonneboite/labonneboite/scripts/profiling_results/*.kgrind \
#     	labonneboite/scripts/profiling_results/staging/

# create-index-from-scratch-with-profiling-single-job:
# 	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/create_index.py --partial --profile

# create-index-from-scratch-with-profiling-line-by-line:
# 	export LBB_ENV=development && cd $(PACKAGE_DIR) && kernprof -v -l scripts/create_index.py --partial --profile

# mysql-local-shell:
# 	$(MYSQL) -D ${DB_NAME}

# rebuild-simplified-rome-naf-mapping:
# 	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/rebuild_simplified_rome_naf_mapping.py

# update_metiers_tension:
# 	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/update_metiers_tension.py

# maj_rome:
# 	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/maj_rome.py


# # Load testing
# # ------------

# start-locust-against-localhost:
# 	echo "Please open locust web interface at http://localhost:8089"
# 	export LBB_ENV=development && cd $(PACKAGE_DIR) && locust --locustfile=scripts/loadtesting.py --host=$(LOCUST_HOST) --loglevel=WARNING --slave &
# 	export LBB_ENV=development && cd $(PACKAGE_DIR) && locust --locustfile=scripts/loadtesting.py --host=$(LOCUST_HOST) --loglevel=WARNING --slave &
# 	export LBB_ENV=development && cd $(PACKAGE_DIR) && locust --locustfile=scripts/loadtesting.py --host=$(LOCUST_HOST) --loglevel=WARNING --slave &
# 	export LBB_ENV=development && cd $(PACKAGE_DIR) && locust --locustfile=scripts/loadtesting.py --host=$(LOCUST_HOST) --loglevel=WARNING --slave &
# 	export LBB_ENV=development && cd $(PACKAGE_DIR) && locust --locustfile=scripts/loadtesting.py --host=$(LOCUST_HOST) --loglevel=WARNING --master

# # Tests
# # -----
# PYTEST_OPTS ?= -vx
# PYTEST = pytest $(PYTEST_OPTS)
# TESTS = 	labonneboite/tests/app/ \
# 			labonneboite/tests/web/ \
# 			labonneboite/tests/scripts/

# test-unit: clean-pyc rebuild-data-test
# 	LBB_ENV=test $(PYTEST) ${TESTS}

# test: test-unit test-selenium test-integration

# check-all: test-all

# test-app:
# 	LBB_ENV=test $(PYTEST) labonneboite/tests/app

# test-api:
# 	LBB_ENV=test $(PYTEST) labonneboite/tests/web/api

# test-front:
# 	LBB_ENV=test $(PYTEST) labonneboite/tests/web/front

# test-web: test-api test-front test-web-integration

# test-scripts:
# 	LBB_ENV=test $(PYTEST) labonneboite/tests/scripts

# test-integration: clear-data-test database-test populate-data-test
# 	LBB_ENV=test $(PYTEST) labonneboite/tests/integration

# test-selenium: clear-data-test database-test populate-data-test-selenium
# 	LBB_ENV=test SELENIUM_IS_SETUP=1 $(PYTEST) labonneboite/tests/selenium

# # Convenient reminder about how to run a specific test manually.
# test-custom:
# 	@echo "To run a specific test, run for example:"
# 	@echo
# 	@echo "    $$ LBB_ENV=test pytest -s labonneboite/tests/web/api/test_api.py"
# 	@echo
# 	@echo "and you can even run a specific method, here are several examples:"
# 	@echo
# 	@echo "    $$ LBB_ENV=test pytest -s labonneboite/tests/web/api/test_api.py:ApiCompanyListTest.test_query_returns_scores_adjusted_to_rome_code_context"
# 	@echo "    $$ LBB_ENV=test pytest -s labonneboite/tests/web/api/test_api.py:ApiOffersOfficesListTest"
# 	@echo "    $$ LBB_ENV=test pytest -s labonneboite/tests/web/front/test_routes.py"
# 	@echo "    $$ LBB_ENV=test pytest -s labonneboite/tests/app/test_suggest_locations.py"
# 	@echo "    $$ LBB_ENV=test pytest -s labonneboite/tests/scripts/test_create_index.py:DeleteOfficeAdminTest.test_office_admin_add"
# 	@echo "    $$ LBB_ENV=test pytest -s labonneboite/tests/selenium/test_search_selecting_car.py:TestSearchSelectingCar.test_commute_time_is_displayed"
# 	@echo
# 	@echo "Note that you can set the env var `NOSE_NOCAPTURE=1` to keep logs in the console"

# # Alembic migrations
# # ------------------

# alembic-migrate:
# 	LBB_ENV=development alembic upgrade head

# alembic-rollback:
# 	LBB_ENV=development alembic downgrade -1

# alembic-generate-migration:
# 	@echo "Run for example:"
# 	@echo
# 	@echo "    $$ alembic revision -m 'create account table'"

# # Test API with key
# # -----
# # Use:
# # make get-signed-api-url URL=https://labonneboite.beta.pole-emploi.fr/api/v1/offers/offices/\?commune_id\=68294\&user\=labonnealternance\&rome_codes\=I1606\&contract\=alternance\&page_size\=100\&distance\=3000

# get-signed-api-url:
# 	python labonneboite/scripts/get_signed_api_url.py $(URL)

# .PHONY: init init-databases init-services init-test-data init-venv compile-requirements compile-dev-requirements services database databases database-wait-mysql database-dev database-test data populate-data-dev populate-data-test populate-data-test-selenium data-dev clear-data clear-data-dev clear-data-test rebuild-data stop-services clean clean-pyc clean-services pylint-all pylint serve-web-app create-sitemap prepare-mailing-data create-index create-index-from-scratch create-index-from-scratch-with-profiling create-index-from-scratch-with-profiling-on-staging create-index-from-scratch-with-profiling-single-job create-index-from-scratch-with-profiling-line-by-line mysql-local-shell rebuild-simplified-rome-naf-mapping rebuild-city-codes update_metiers_tension maj_rome start-locust-against-localhost test-unit test check-all test-app test-api test-front test-web test-scripts test-integration test-selenium test-custom alembic-migrate alembic-rollback alembic-generate-migration get-signed-api-url