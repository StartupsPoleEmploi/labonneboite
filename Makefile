PACKAGE_DIR = labonneboite
LOCUST_HOST = http://localhost:5000

# Requirements
# ------------

compile-requirements:
	pip-compile -o requirements.txt requirements.in

# Services and data
# -----------------

services:
	cd docker/ && docker-compose up -d

# Launch services and wait until mysql is ready.
# Wait only if /var/lib/mysql folder is not present yet.
init-services: services
	cd docker && docker-compose run mysql stat /var/lib/mysql >/dev/null || until docker-compose logs mysql | grep "MySQL init process done. Ready for start up."; do echo "waiting for mysql initialization..."; sleep 4; done

database: database-dev database-test

database-dev: services
	mysql -u root --host 127.0.0.1 --port 3307 -e 'CREATE DATABASE IF NOT EXISTS labonneboite DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;'
	mysql -u root --host 127.0.0.1 --port 3307 -e 'GRANT ALL ON labonneboite.* TO "labonneboite"@"%" IDENTIFIED BY "labonneboite";'

database-test: services
	mysql -u root --host 127.0.0.1 --port 3307 -e 'CREATE DATABASE IF NOT EXISTS lbb_test DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;'
	mysql -u root --host 127.0.0.1 --port 3307 -e 'GRANT ALL ON lbb_test.* TO "lbb_test"@"%" IDENTIFIED BY "";'

data: database alembic-migrate populate-data-dev

populate-data-dev:
	mysql -u root --host 127.0.0.1 --port 3307 labonneboite < ./labonneboite/alembic/sql/etablissements.sql
	LBB_ENV=development python ./labonneboite/scripts/create_index.py --full

populate-data-test:
	LBB_ENV=test alembic upgrade head
	mysql -u root --host 127.0.0.1 --port 3307 lbb_test < ./labonneboite/alembic/sql/etablissements.sql
	LBB_ENV=test python ./labonneboite/scripts/create_index.py --full

populate-data-test-selenium:
	LBB_ENV=test alembic upgrade head
	mysql -u root --host 127.0.0.1 --port 3307 lbb_test < ./labonneboite/alembic/sql/etablissements_tests_selenium.sql
	LBB_ENV=test python ./labonneboite/scripts/create_index.py --full

clear-data: clear-data-dev clear-data-test

clear-data-dev: services
	mysql -u root --host 127.0.0.1 --port 3307 -e 'DROP DATABASE IF EXISTS labonneboite;'

clear-data-test: services
	mysql -u root --host 127.0.0.1 --port 3307 -e 'DROP DATABASE IF EXISTS lbb_test;'

rebuild-data-dev : clear-data-dev database-dev alembic-migrate populate-data-dev

rebuild-data-test : clear-data-test database-test

rebuild-data: rebuild-data-test rebuild-data-dev

stop-services:
	cd docker/ && docker-compose stop

consume-tasks:
	huey_consumer --workers=32 --worker-type=thread labonneboite.common.maps.precompute.huey
consume-tasks-dev:
	LBB_ENV=development $(MAKE) consume-tasks

# Cleanup
# -------

clean:
	find $(PACKAGE_DIR) "(" -name "*.pyc" -or -name "*.pyo" -or -name "*.mo" -or -name "*.so" ")" -delete
	find $(PACKAGE_DIR) -type d -empty -delete
	find $(PACKAGE_DIR) -name __pycache__ -delete

clean-pyc:
	find $(PACKAGE_DIR) "(" -name "*.pyc" ")" -delete

clean-services: stop-services ## Delete containers and attached volumes
	cd docker && docker-compose rm --force -v

# Code quality
# ------------

# Run pylint on the whole project.
pylint-all:
	pylint --rcfile=.pylintrc --reports=no --output-format=colorized $(PACKAGE_DIR) || true

# Run pylint on a specific file, e.g.:
# make pylint FILE=labonneboite/web/app.py
pylint:
	pylint --rcfile=.pylintrc --reports=no --output-format=colorized $(FILE) || true


# Local dev
# ---------

serve-web-app:
	LBB_ENV=development python labonneboite/web/app.py

create-sitemap:
	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/create_sitemap.py sitemap

prepare-mailing-data:
	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/prepare_mailing_data.py

create-index:
	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/create_index.py

create-index-from-scratch:
	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/create_index.py --full

create-index-from-scratch-with-profiling:
	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/create_index.py --full --profile

create-index-from-scratch-with-profiling-on-staging:
	ssh deploy@lbbstaging -t 'bash -c "\
        cd && source /home/deploy/config/labonneboite/bin/activate && \
        export LBB_ENV=staging && export LBB_SETTINGS=/home/deploy/config/lbb_staging_settings.py && \
        cd /home/deploy/code/current/labonneboite/labonneboite && \
        time python scripts/create_index.py --full --profile"' && \
    scp deploy@lbbstaging:/home/deploy/code/current/labonneboite/labonneboite/scripts/profiling_results/*.kgrind \
    	labonneboite/scripts/profiling_results/staging/

create-index-from-scratch-with-profiling-single-job:
	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/create_index.py --partial --profile

create-index-from-scratch-with-profiling-line-by-line:
	export LBB_ENV=development && cd $(PACKAGE_DIR) && kernprof -v -l scripts/create_index.py --partial --profile

mysql-local-shell:
	mysql -u root --host 127.0.0.1 --port 3307 labonneboite

rebuild-simplified-rome-naf-mapping:
	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/rebuild_simplified_rome_naf_mapping.py

rebuild-importer-tests-compressed-files:
	cd labonneboite/tests/importer/data && \
	rm -f lbb_xdpdpae_delta_201611102200.csv.gz && \
	gzip --keep lbb_xdpdpae_delta_201611102200.csv && \
	rm -f lbb_xdpdpae_delta_201611102200.csv.bz2 && \
	bzip2 --keep lbb_xdpdpae_delta_201611102200.csv

rebuild-city-codes:
	export LBB_ENV=development && cd $(PACKAGE_DIR) && python importer/scripts/clean_csv_city_codes.py

update_metiers_tension:
	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/update_metiers_tension.py

# Load testing
# ------------

start-locust-against-localhost:
	echo "Please open locust web interface at http://localhost:8089"
	export LBB_ENV=development && cd $(PACKAGE_DIR) && locust --locustfile=scripts/loadtesting.py --host=$(LOCUST_HOST) --loglevel=WARNING --slave &
	export LBB_ENV=development && cd $(PACKAGE_DIR) && locust --locustfile=scripts/loadtesting.py --host=$(LOCUST_HOST) --loglevel=WARNING --slave &
	export LBB_ENV=development && cd $(PACKAGE_DIR) && locust --locustfile=scripts/loadtesting.py --host=$(LOCUST_HOST) --loglevel=WARNING --slave &
	export LBB_ENV=development && cd $(PACKAGE_DIR) && locust --locustfile=scripts/loadtesting.py --host=$(LOCUST_HOST) --loglevel=WARNING --slave &
	export LBB_ENV=development && cd $(PACKAGE_DIR) && locust --locustfile=scripts/loadtesting.py --host=$(LOCUST_HOST) --loglevel=WARNING --master

# Tests
# -----

NOSETESTS = nosetests -s $(NOSETESTS_OPTS)

test-unit: clean-pyc
	LBB_ENV=test $(NOSETESTS) \
			labonneboite/tests/app/ \
			labonneboite/tests/web/ \
			labonneboite/tests/scripts/ \
			labonneboite/tests/importer/

test-all: test-unit test-selenium test-integration

check-all: test-all run-importer-jobs

test-app:
	LBB_ENV=test $(NOSETESTS) labonneboite/tests/app

test-importer:
	LBB_ENV=test $(NOSETESTS) labonneboite/tests/importer

# convenient shortcut when working on the importer
check-importer: test-importer run-importer-jobs

test-api:
	LBB_ENV=test $(NOSETESTS) labonneboite/tests/web/api

test-front:
	LBB_ENV=test $(NOSETESTS) labonneboite/tests/web/front

test-web: test-api test-front test-web-integration

test-scripts:
	LBB_ENV=test $(NOSETESTS) labonneboite/tests/scripts

test-integration: clear-data-test database-test populate-data-test
	LBB_ENV=test $(NOSETESTS) labonneboite/tests/integration

test-selenium: clear-data-test database-test populate-data-test-selenium
	LBB_ENV=test $(NOSETESTS) labonneboite/tests/selenium

# Convenient reminder about how to run a specific test manually.
test-custom:
	@echo "To run a specific test, run for example:"
	@echo
	@echo "    $$ LBB_ENV=test nosetests -s labonneboite/tests/web/api/test_api.py"
	@echo
	@echo "and you can even run a specific method, here are several examples:"
	@echo
	@echo "    $$ LBB_ENV=test nosetests -s labonneboite/tests/web/api/test_api.py:ApiCompanyListTest.test_query_returns_scores_adjusted_to_rome_code_context"
	@echo "    $$ LBB_ENV=test nosetests -s labonneboite/tests/web/api/test_api.py:ApiOffersOfficesListTest"
	@echo "    $$ LBB_ENV=test nosetests -s labonneboite/tests/web/front/test_routes.py"
	@echo "    $$ LBB_ENV=test nosetests -s labonneboite/tests/app/test_suggest_locations.py"
	@echo "    $$ LBB_ENV=test nosetests -s labonneboite/tests/scripts/test_create_index.py:DeleteOfficeAdminTest.test_office_admin_add"
	@echo "    $$ LBB_ENV=test nosetests -s labonneboite/tests/selenium/test_search_selecting_car.py:TestSearchSelectingCar.test_commute_time_is_displayed"
	@echo
	@echo "Note that you can set the env var `NOSE_NOCAPTURE=1` to keep logs in the console

# Alembic migrations
# ------------------

alembic-migrate:
	LBB_ENV=development alembic upgrade head

alembic-rollback:
	LBB_ENV=development alembic downgrade -1

alembic-generate-migration:
	@echo "Run for example:"
	@echo
	@echo "    $$ alembic revision -m 'create account table'"

# Impact retour à l'emploi
# ------------------------
daily-json-activity-parser:
	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/impact_retour_emploi/daily_json_activity_parser.py

join-activity-logs-and-dpae:
	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/impact_retour_emploi/join_activity_logs_dpae.py

clean-activity-logs-and-dpae:
	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/impact_retour_emploi/clean_activity_logs_dpae.py

make-report:
	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/impact_retour_emploi/make_report.py

run-impact-retour-emploi-jobs:
	make join_activity_logs_and_dpae && \
	make clean_activity_logs_and_dpae && \
	make make_report && \
	echo "The new report has been built successfully."

# Importer jobs
# -------------

run-importer-jobs:
	make run-importer-job-00-prepare-all && \
	make run-importer-job-01-check-etablissements && \
	make run-importer-job-02-extract-etablissements && \
	make run-importer-job-03-check-dpae && \
	make run-importer-job-04-extract-dpae && \
	make run-importer-job-04hack-create-fake-alternance-hirings && \
	make run-importer-job-05-compute-scores && \
	make run-importer-job-06-validate-scores && \
	make run-importer-job-07-geocode && \
	make run-importer-job-08-populate-flags && \
	echo "all importer jobs completed successfully."

run-importer-job-00-prepare-all: alembic-migrate
	export LBB_ENV=development && \
		cd labonneboite/importer && \
		echo delete from hirings                   | mysql -u root -D labonneboite --host 127.0.0.1 --port 3307 && \
		echo delete from import_tasks              | mysql -u root -D labonneboite --host 127.0.0.1 --port 3307 && \
		echo delete from etablissements_raw        | mysql -u root -D labonneboite --host 127.0.0.1 --port 3307 && \
		echo delete from etablissements_backoffice | mysql -u root -D labonneboite --host 127.0.0.1 --port 3307 && \
		echo delete from etablissements_exportable | mysql -u root -D labonneboite --host 127.0.0.1 --port 3307 && \
		echo delete from geolocations              | mysql -u root -D labonneboite --host 127.0.0.1 --port 3307 && \
		echo delete from dpae_statistics           | mysql -u root -D labonneboite --host 127.0.0.1 --port 3307 && \
		rm data/*.csv jenkins/*.jenkins output/*.bz2 output/*.gz ; \
		cp ../tests/importer/data/lbb_xdpdpae_delta_201611102200.csv data/ && \
		cp ../tests/importer/data/lbb_etablissement_full_201612192300.csv data/ && \
		echo "completed importer run preparation."

run-importer-job-01-check-etablissements:
	export LBB_ENV=development && cd labonneboite/importer && python jobs/check_etablissements.py

run-importer-job-02-extract-etablissements:
	export LBB_ENV=development && cd labonneboite/importer && python jobs/extract_etablissements.py

run-importer-job-03-check-dpae:
	export LBB_ENV=development && cd labonneboite/importer && python jobs/check_dpae.py

run-importer-job-04-extract-dpae:
	export LBB_ENV=development && cd labonneboite/importer && python jobs/extract_dpae.py

run-importer-job-04hack-create-fake-alternance-hirings:
	export LBB_ENV=development && \
		cd labonneboite/importer && \
		cat scripts/create_fake_alternance_hirings.sql | mysql -u root -D labonneboite --host 127.0.0.1 --port 3307

run-importer-job-05-compute-scores:
	export LBB_ENV=development && cd labonneboite/importer && python jobs/compute_scores.py

run-importer-job-06-validate-scores:
	export LBB_ENV=development && cd labonneboite/importer && python jobs/validate_scores.py

run-importer-job-07-geocode:
	export LBB_ENV=development && cd labonneboite/importer && python jobs/geocode.py

run-importer-job-08-populate-flags:
	export LBB_ENV=development && cd labonneboite/importer && python jobs/populate_flags.py


# Redis useful commands
# -----

REDIS_DOCKER_COMPOSE = docker-compose -f docker/docker-compose.yml run redis bash -c
REDIS_CONNECT = redis-cli -h redis -p 6389

redis-get-key:
	# Eg: $ redis-get-key KEY="huey.results.huey"
	$(REDIS_DOCKER_COMPOSE) "$(REDIS_CONNECT) get '$(KEY)'"

redis-count-keys:
	$(REDIS_DOCKER_COMPOSE) "$(REDIS_CONNECT) --scan --pattern '$(PATTERN)' | wc -l"

redis-show-keys:
	$(REDIS_DOCKER_COMPOSE) "$(REDIS_CONNECT) --scan --pattern '$(PATTERN)' | head -10"

redis-delete-keys:
	# Eg: $ redis-delete-keys PATTERN='"mypattern"'
	$(REDIS_DOCKER_COMPOSE) "$(REDIS_CONNECT) --scan --pattern '$(PATTERN)' | tr '\n' '\0' | xargs -L1 -0 $(REDIS_CONNECT) del"

clean-car-isochrone-cache:
	@echo '###### Total keys to be deleted \#######'
	PATTERN='*isochrone**car*' $(MAKE) redis-count-keys
	@echo '###### EXTERMINATE ISOCHRONE CACHE! \######'
	$(REDIS_DOCKER_COMPOSE) "$(REDIS_CONNECT) --scan --pattern '*isochrone**car*' | tr '\n' '\0' | xargs -L1 -0 $(REDIS_CONNECT) del"

clean-car-isochrone-and-durations-cache: clean-car-isochrone-cache
	@echo '###### Total keys to be deleted \#######'
	PATTERN='*durations**car*' $(MAKE) redis-count-keys
	@echo '###### EXTERMINATE DURATIONS! \######'
	$(REDIS_DOCKER_COMPOSE) "$(REDIS_CONNECT) --scan --pattern '*durations**car*' | tr '\n' '\0' | xargs -L1 -0 $(REDIS_CONNECT) del"

delete-unused-redis-containers:
	docker ps -f status=restarting -f name=redis --format "{{.ID}}" \
    | xargs docker rm -f
