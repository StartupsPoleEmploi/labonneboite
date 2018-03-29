PACKAGE_DIR = labonneboite
LOCUST_HOST = http://localhost:5000

# Services and data
# -----------------

services:
	cd docker/ && docker-compose up -d

database: services
	mysql -u root --host 127.0.0.1 --port 3307 -e 'CREATE DATABASE IF NOT EXISTS labonneboite DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;'
	mysql -u root --host 127.0.0.1 --port 3307 -e 'CREATE DATABASE IF NOT EXISTS lbb_test DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;'
	mysql -u root --host 127.0.0.1 --port 3307 -e 'GRANT ALL ON labonneboite.* TO "labonneboite"@"%" IDENTIFIED BY "labonneboite";'
	mysql -u root --host 127.0.0.1 --port 3307 -e 'GRANT ALL ON lbb_test.* TO "lbb_test"@"%" IDENTIFIED BY "";'

data: database
	mysql -u root --host 127.0.0.1 --port 3307 labonneboite < ./labonneboite/alembic/sql/etablissements.sql
	LBB_ENV=development alembic upgrade head
	LBB_ENV=development python ./labonneboite/scripts/create_index.py --full

clear-data:
	mysql -u root --host 127.0.0.1 --port 3307 -e 'DROP DATABASE IF EXISTS labonneboite;'
	mysql -u root --host 127.0.0.1 --port 3307 -e 'DROP DATABASE IF EXISTS lbb_test;'

# Cleanup
# -------

.PHONY: clean clean_pyc

clean:
	find $(PACKAGE_DIR) "(" -name "*.pyc" -or -name "*.pyo" -or -name "*.mo" -or -name "*.so" ")" -delete
	find $(PACKAGE_DIR) -type d -empty -delete
	find $(PACKAGE_DIR) -name __pycache__ -delete

clean_pyc:
	find $(PACKAGE_DIR) "(" -name "*.pyc" ")" -delete

# Code quality
# ------------

.PHONY: pylint_all pylint

# Run pylint on the whole project.
pylint_all:
	pylint --rcfile=.pylintrc --reports=no --output-format=colorized $(PACKAGE_DIR) || true

# Run pylint on a specific file, e.g.:
# make pylint FILE=labonneboite/web/app.py
pylint:
	pylint --rcfile=.pylintrc --reports=no --output-format=colorized $(FILE) || true


# Local dev
# ---------

.PHONY: serve_web_app create_sitemap prepare_mailing_data create_index create_index_from_scratch
.PHONY: create_index_from_scratch_with_profiling create_index_from_scratch_with_profiling_on_staging
.PHONY: create_index_from_scratch_with_profiling_line_by_line
.PHONY: mysql_local_shell rebuild_importer_tests_compressed_files

serve_web_app:
	LBB_ENV=development python labonneboite/web/app.py

create_sitemap:
	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/create_sitemap.py sitemap

prepare_mailing_data:
	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/prepare_mailing_data.py

create_index:
	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/create_index.py

create_index_from_scratch:
	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/create_index.py --full

create_index_from_scratch_with_profiling:
	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/create_index.py --full --profile

create_index_from_scratch_with_profiling_on_staging:
	ssh deploy@lbbstaging -t 'bash -c "\
        cd && source /home/deploy/config/labonneboite/bin/activate && \
        export LBB_ENV=staging && export LBB_SETTINGS=/home/deploy/config/lbb_staging_settings.py && \
        cd /home/deploy/code/current/labonneboite/labonneboite && \
        time python scripts/create_index.py --full --profile"' && \
    scp deploy@lbbstaging:/home/deploy/code/current/labonneboite/labonneboite/scripts/profiling_results/*.kgrind \
    	labonneboite/scripts/profiling_results/staging/

create_index_from_scratch_with_profiling_single_job:
	export LBB_ENV=development && cd $(PACKAGE_DIR) && python scripts/create_index.py --partial --profile

create_index_from_scratch_with_profiling_line_by_line:
	export LBB_ENV=development && cd $(PACKAGE_DIR) && kernprof -v -l scripts/create_index.py --partial --profile

mysql_local_shell:
	mysql -u root --host 127.0.0.1 --port 3307 labonneboite

rebuild_importer_tests_compressed_files:
	cd labonneboite/tests/importer/data && \
	rm LBB_XDPDPA_DPAE_20151010_20161110_20161110_174915.csv.gz && \
	gzip --keep LBB_XDPDPA_DPAE_20151010_20161110_20161110_174915.csv && \
	rm LBB_XDPDPA_DPAE_20151010_20161110_20161110_174915.csv.bz2 && \
	bzip2 --keep LBB_XDPDPA_DPAE_20151010_20161110_20161110_174915.csv

# Load testing
# ------------

.PHONY: start_locust_against_localhost

start_locust_against_localhost:
	echo "Please open locust web interface at http://localhost:8089"
	export LBB_ENV=development && cd $(PACKAGE_DIR) && locust --locustfile=scripts/loadtesting.py --host=$(LOCUST_HOST) --loglevel=WARNING --slave &
	export LBB_ENV=development && cd $(PACKAGE_DIR) && locust --locustfile=scripts/loadtesting.py --host=$(LOCUST_HOST) --loglevel=WARNING --slave &
	export LBB_ENV=development && cd $(PACKAGE_DIR) && locust --locustfile=scripts/loadtesting.py --host=$(LOCUST_HOST) --loglevel=WARNING --slave &
	export LBB_ENV=development && cd $(PACKAGE_DIR) && locust --locustfile=scripts/loadtesting.py --host=$(LOCUST_HOST) --loglevel=WARNING --slave &
	export LBB_ENV=development && cd $(PACKAGE_DIR) && locust --locustfile=scripts/loadtesting.py --host=$(LOCUST_HOST) --loglevel=WARNING --master

# Tests
# -----

.PHONY: test_all test_unit test_app test_importer test_api test_front test_scripts test_selenium

test_unit: clean_pyc test_app test_web test_scripts test_importer

test_all: test_unit test_selenium

test_app:
	LBB_ENV=test nosetests -s labonneboite/tests/app

test_importer:
	LBB_ENV=test nosetests -s labonneboite/tests/importer

test_api:
	LBB_ENV=test nosetests -s labonneboite/tests/web/api

test_front:
	LBB_ENV=test nosetests -s labonneboite/tests/web/front

test_web: test_api test_front

test_scripts:
	LBB_ENV=test nosetests -s labonneboite/tests/scripts

# Selenium and integration tests are run against the full database (not the
# test one) as of now: we use LBB_ENV=development.
test_integration:
	LBB_ENV=development nosetests -s labonneboite/tests/integration
test_selenium:
	LBB_ENV=development nosetests -s labonneboite/tests/selenium

# Convenient reminder about how to run a specific test manually.
test_custom:
	@echo "To run a specific test, run for example:"
	@echo
	@echo "    $$ nosetests -s labonneboite/tests/web/api/test_api.py"
	@echo
	@echo "and you can even run a specific method:"
	@echo
	@echo "    $$ nosetests -s labonneboite/tests/web/api/test_api.py:ApiCompanyListTest.test_query_returns_scores_adjusted_to_rome_code_context"

# Alembic migrations
# ------------------

alembic_migrate:
	LBB_ENV=development alembic upgrade head

alembic_rollback:
	LBB_ENV=development alembic downgrade -1

# FIXME something is still wrong with this one
# upgrade and downgrade methods should be swapped in resulting migration
alembic_autogenerate_migration_for_all_existing_tables:
	LBB_ENV=development alembic revision --autogenerate

alembic_generate_single_migration:
	@echo "Run for example:"
	@echo 
	@echo "    $$ alembic revision -m 'create account table'"

# Importer jobs
# -------------

run_importer_jobs:
	make run_importer_job_00_prepare_all && \
	make run_importer_job_01_check_etablissements && \
	make run_importer_job_02_extract_etablissements && \
	make run_importer_job_03_check_dpae && \
	make run_importer_job_04_extract_dpae && \
	make run_importer_job_05_compute_scores && \
	make run_importer_job_06_validate_scores && \
	make run_importer_job_07_geocode && \
	make run_importer_job_08_populate_flags && \
	echo "all importer jobs completed successfully."

run_importer_job_00_prepare_all:  # FIXME DNRY table names
	export LBB_ENV=development && \
		cd labonneboite/importer && \
		echo delete from import_tasks              | mysql -u root -D labonneboite --host 127.0.0.1 --port 3307 && \
		echo delete from etablissements_raw        | mysql -u root -D labonneboite --host 127.0.0.1 --port 3307 && \
		echo delete from etablissements_backoffice | mysql -u root -D labonneboite --host 127.0.0.1 --port 3307 && \
		echo delete from etablissements_exportable | mysql -u root -D labonneboite --host 127.0.0.1 --port 3307 && \
		echo delete from geolocations              | mysql -u root -D labonneboite --host 127.0.0.1 --port 3307 && \
		echo delete from dpae_statistics           | mysql -u root -D labonneboite --host 127.0.0.1 --port 3307 && \
		rm data/*.csv jenkins/*.jenkins output/*.bz2 output/*.gz ; \
		cp ../tests/importer/data/LBB_XDPDPA_DPAE_20151010_20161110_20161110_174915.csv data/ && \
		cp ../tests/importer/data/LBB_EGCEMP_ENTREPRISE_20151119_20161219_20161219_153447.csv data/ && \
		echo "completed importer run preparation."

run_importer_job_01_check_etablissements:
	export LBB_ENV=development && cd labonneboite/importer && python jobs/check_etablissements.py

run_importer_job_02_extract_etablissements:
	export LBB_ENV=development && cd labonneboite/importer && python jobs/extract_etablissements.py

run_importer_job_03_check_dpae:
	export LBB_ENV=development && cd labonneboite/importer && python jobs/check_dpae.py

run_importer_job_04_extract_dpae:
	export LBB_ENV=development && cd labonneboite/importer && python jobs/extract_dpae.py

run_importer_job_05_compute_scores:
	export LBB_ENV=development && cd labonneboite/importer && python jobs/compute_scores.py

run_importer_job_06_validate_scores:
	export LBB_ENV=development && cd labonneboite/importer && python jobs/validate_scores.py

run_importer_job_07_geocode:
	export LBB_ENV=development && cd labonneboite/importer && python jobs/geocode.py

run_importer_job_08_populate_flags:
	export LBB_ENV=development && cd labonneboite/importer && python jobs/populate_flags.py
