PACKAGE = labonneboite
PACKAGE_SRC_DIR = $(PACKAGE)

VAGRANT_ACTIVATE_VENV = source /home/vagrant/venvs/labonneboite/bin/activate
VAGRANT_PYLINT_RC = /srv/lbb/.pylintrc

VAGRANT_PACKAGE_SRC_PATH = /srv/lbb/
VAGRANT_PACKAGE_SRC_DIR = $(VAGRANT_PACKAGE_SRC_PATH)$(PACKAGE)

# Cleanup
# -------

.PHONY: clean clean_pyc

clean:
	find $(PACKAGE_SRC_DIR) "(" -name "*.pyc" -or -name "*.pyo" -or -name "*.mo" -or -name "*.so" ")" -delete
	find $(PACKAGE_SRC_DIR) -type d -empty -delete
	find $(PACKAGE_SRC_DIR) -name __pycache__ -delete

clean_pyc:
	find $(PACKAGE_SRC_DIR) "(" -name "*.pyc" ")" -delete

# Code quality
# ------------

.PHONY: pylint

# Run pylint on the whole project.
pylint_all:
	cd vagrant; \
	vagrant ssh -c '$(VAGRANT_ACTIVATE_VENV) && \
	pylint --rcfile=$(VAGRANT_PYLINT_RC) --reports=no \
		--output-format=colorized $(VAGRANT_PACKAGE_SRC_DIR) || \
	true';

# Run pylint on a specific file, e.g.:
# make pylint FILE=labonneboite/web/app.py
pylint:
	cd vagrant; \
	vagrant ssh -c '$(VAGRANT_ACTIVATE_VENV) && \
	pylint --rcfile=$(VAGRANT_PYLINT_RC) --reports=no \
		--output-format=colorized $(VAGRANT_PACKAGE_SRC_PATH)$(FILE) || \
	true';


# Vagrant
# -------

.PHONY: vagrant_start vagrant_stop vagrant_ssh_dev vagrant_ssh_test vagrant_reload

vagrant_start:
	cd vagrant && vagrant up --provision;

vagrant_stop:
	cd vagrant && vagrant halt;

vagrant_ssh_dev:
	cd vagrant && vagrant ssh --command '$(VAGRANT_ACTIVATE_VENV) && export LBB_ENV=development && \
	cd /srv/lbb && bash';

vagrant_ssh_test:
	cd vagrant && vagrant ssh --command '$(VAGRANT_ACTIVATE_VENV) && export LBB_ENV=test && \
	cd /srv/lbb && bash';

# Reload Vagrant and Vagrantfile quickly.
vagrant_reload:
	cd vagrant && vagrant reload --provision;

# Local dev
# ---------

.PHONY: serve_web_app create_sitemap create_index create_index_from_scratch
.PHONY: create_index_from_scratch_with_profiling create_index_from_scratch_with_profiling_on_staging
.PHONY: create_index_from_scratch_with_profiling_line_by_line
.PHONY: mysql_local_shell rebuild_importer_tests_compressed_files

serve_web_app:
	cd vagrant && vagrant ssh --command '$(VAGRANT_ACTIVATE_VENV) && export LBB_ENV=development && \
	python /srv/lbb/labonneboite/web/app.py';

create_sitemap:
	cd vagrant && vagrant ssh --command '$(VAGRANT_ACTIVATE_VENV) && export LBB_ENV=development && \
	cd /srv/lbb/labonneboite && python scripts/create_sitemap.py sitemap';

create_index:
	cd vagrant && vagrant ssh --command '$(VAGRANT_ACTIVATE_VENV) && export LBB_ENV=development && \
	cd /srv/lbb/labonneboite && python scripts/create_index.py';

create_index_from_scratch:
	cd vagrant && vagrant ssh --command '$(VAGRANT_ACTIVATE_VENV) && export LBB_ENV=development && \
	cd /srv/lbb/labonneboite && python scripts/create_index.py -d 1';

create_index_from_scratch_with_profiling:
	cd vagrant && vagrant ssh --command '$(VAGRANT_ACTIVATE_VENV) && export LBB_ENV=development && \
	cd /srv/lbb/labonneboite && python scripts/create_index.py -d 1 -p 1';

create_index_from_scratch_with_profiling_on_staging:
	ssh deploy@lbbstaging -t 'bash -c "\
        cd && source /home/deploy/config/labonneboite/bin/activate && \
        export LBB_ENV=staging && export LBB_SETTINGS=/home/deploy/config/lbb_staging_settings.py && \
        cd /home/deploy/code/current/labonneboite/labonneboite && \
        time python scripts/create_index.py -d 1 -p 1"' && \
    scp deploy@lbbstaging:/home/deploy/code/current/labonneboite/labonneboite/scripts/profiling_results/*.kgrind \
    	labonneboite/scripts/profiling_results/staging/;

create_index_from_scratch_with_profiling_single_job:
	cd vagrant && vagrant ssh --command '$(VAGRANT_ACTIVATE_VENV) && export LBB_ENV=development && \
	cd /srv/lbb/labonneboite && python scripts/create_index.py -d 1 -p 1 -s 1';

create_index_from_scratch_with_profiling_line_by_line:
	cd vagrant && vagrant ssh --command '$(VAGRANT_ACTIVATE_VENV) && export LBB_ENV=development && \
	cd /srv/lbb/labonneboite && kernprof -v -l scripts/create_index.py -d 1 -p 1 -s 1';

mysql_local_shell:
	cd vagrant && vagrant ssh --command 'mysql -u root -D labonneboite --host 127.0.0.1';

rebuild_importer_tests_compressed_files:
	cd labonneboite/importer/tests/data && \
	rm LBB_XDPDPA_DPAE_20151010_20161110_20161110_174915.csv.gz && \
	gzip --keep LBB_XDPDPA_DPAE_20151010_20161110_20161110_174915.csv && \
	rm LBB_XDPDPA_DPAE_20151010_20161110_20161110_174915.csv.bz2 && \
	bzip2 --keep LBB_XDPDPA_DPAE_20151010_20161110_20161110_174915.csv

# Load testing
# ------------

.PHONY: start_locust_against_localhost

start_locust_against_localhost:
	cd vagrant && vagrant ssh --command '\
	$(VAGRANT_ACTIVATE_VENV) && export LBB_ENV=development && cd /srv/lbb/labonneboite \
	&& echo -e && echo -e \
	&& echo "Please open locust web interface at http://localhost:8089" \
	&& echo -e && echo -e \
	&& locust --locustfile=scripts/loadtesting.py --host=http://localhost:5000 --slave & \
		$(VAGRANT_ACTIVATE_VENV) && export LBB_ENV=development && cd /srv/lbb/labonneboite \
	&& locust --locustfile=scripts/loadtesting.py --host=http://localhost:5000 --slave & \
		$(VAGRANT_ACTIVATE_VENV) && export LBB_ENV=development && cd /srv/lbb/labonneboite \
	&& locust --locustfile=scripts/loadtesting.py --host=http://localhost:5000 --slave & \
		$(VAGRANT_ACTIVATE_VENV) && export LBB_ENV=development && cd /srv/lbb/labonneboite \
	&& locust --locustfile=scripts/loadtesting.py --host=http://localhost:5000 --slave & \
		$(VAGRANT_ACTIVATE_VENV) && export LBB_ENV=development && cd /srv/lbb/labonneboite \
	&& locust --locustfile=scripts/loadtesting.py --host=http://localhost:5000 --master';

# Tests
# -----

.PHONY: test_all test_app test_importer test_api test_integration test_scripts test_selenium

test_all: clean_pyc test_app test_importer test_api test_integration test_scripts test_selenium

test_app:
	cd vagrant; \
	vagrant ssh --command '$(VAGRANT_ACTIVATE_VENV) \
	&& export LBB_ENV=test \
	&& nosetests -s /srv/lbb/labonneboite/tests/app';

test_importer:
	cd vagrant; \
	vagrant ssh --command '$(VAGRANT_ACTIVATE_VENV) \
	&& export LBB_ENV=test \
	&& nosetests -s /srv/lbb/labonneboite/importer/tests';

test_api:
	cd vagrant; \
	vagrant ssh --command '$(VAGRANT_ACTIVATE_VENV) \
	&& export LBB_ENV=test \
	&& nosetests -s /srv/lbb/labonneboite/tests/web/api';

test_integration:
	cd vagrant; \
	vagrant ssh --command '$(VAGRANT_ACTIVATE_VENV) \
	&& export LBB_ENV=test \
	&& nosetests -s /srv/lbb/labonneboite/tests/web/integration';

test_scripts:
	cd vagrant; \
	vagrant ssh --command '$(VAGRANT_ACTIVATE_VENV) \
	&& export LBB_ENV=test \
	&& nosetests -s /srv/lbb/labonneboite/tests/scripts';

# Selenium tests are run against the full database (not the test one)
# as of now: we use LBB_ENV=development.
test_selenium:
	cd vagrant; \
	vagrant ssh --command '$(VAGRANT_ACTIVATE_VENV) \
	&& export LBB_ENV=development \
	&& nosetests -s /srv/lbb/labonneboite/tests/web/selenium';

# Importer jobs
# -------------

run_importer_jobs:
	make run_importer_job_00_reset_all && \
	make run_importer_job_01_check_etablissements && \
	make run_importer_job_02_extract_etablissements && \
	make run_importer_job_03_check_dpae && \
	make run_importer_job_04_extract_dpae && \
	echo done

run_importer_job_00_reset_all:
	cd vagrant && vagrant ssh --command '$(VAGRANT_ACTIVATE_VENV) && export LBB_ENV=development && \
		cd /srv/lbb/labonneboite && cd importer && \
		rm data/*.csv ; \
		rm jenkins/*.jenkins ; \
		echo delete from import_tasks | mysql -u root -D labonneboite --host 127.0.0.1 && \
		echo delete from etablissements_importer | mysql -u root -D labonneboite --host 127.0.0.1 && \
		echo delete from dpae_statistics | mysql -u root -D labonneboite --host 127.0.0.1 && \
		echo done';

run_importer_job_01_check_etablissements:
	cd vagrant && vagrant ssh --command '$(VAGRANT_ACTIVATE_VENV) && export LBB_ENV=development && \
		cd /srv/lbb/labonneboite && cd importer && \
		cp tests/data/LBB_EGCEMP_ENTREPRISE_20151119_20161219_20161219_153447.csv data/ && \
		python jobs/check_etablissements.py';

run_importer_job_02_extract_etablissements:
	cd vagrant && vagrant ssh --command '$(VAGRANT_ACTIVATE_VENV) && export LBB_ENV=development && \
		cd /srv/lbb/labonneboite && cd importer && \
		python jobs/extract_etablissements.py';

run_importer_job_03_check_dpae:
	cd vagrant && vagrant ssh --command '$(VAGRANT_ACTIVATE_VENV) && export LBB_ENV=development && \
		cd /srv/lbb/labonneboite && cd importer && \
		cp tests/data/LBB_XDPDPA_DPAE_20151110_20161210_20161210_094110.csv data/ && \
		python jobs/check_dpae.py';

run_importer_job_04_extract_dpae:
	cd vagrant && vagrant ssh --command '$(VAGRANT_ACTIVATE_VENV) && export LBB_ENV=development && \
		cd /srv/lbb/labonneboite && cd importer && \
		python jobs/extract_dpae.py';

