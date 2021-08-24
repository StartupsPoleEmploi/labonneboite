#! /bin/sh
mysql -u travis -e 'CREATE DATABASE IF NOT EXISTS lbb_test DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;'
echo GREPME started initial install
sudo locale-gen fr_FR
sudo update-locale
curl -O https://download.elastic.co/elasticsearch/elasticsearch/elasticsearch-1.7.4.deb && sudo dpkg -i --force-confnew elasticsearch-1.7.4.deb && sudo service elasticsearch restart
pip install -r requirements.txt
python setup.py develop
echo GREPME completed initial install

echo GREPME started app tests
nosetests --nologcapture labonneboite/tests/app
echo GREPME started web tests
nosetests --nologcapture labonneboite/tests/web
echo GREPME started scripts tests
nosetests --nologcapture labonneboite/tests/scripts
echo GREPME started importer tests
nosetests -v --nologcapture labonneboite/tests/importer
Integration
echo GREPME started recreating database for integration tests
mysql -u travis -e 'DROP DATABASE IF EXISTS lbb_test;'
mysql -u travis -e 'CREATE DATABASE IF NOT EXISTS lbb_test DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;'
echo GREPME started migrating database for integration tests
alembic upgrade head
echo GREPME started populating database for integration tests
mysql -u travis lbb_test < ./labonneboite/alembic/sql/etablissements.sql
echo GREPME started indexing data for integration tests
create_index --full > /dev/null 2>&1  # avoid spamming travis logs
echo GREPME started integration tests
nosetests labonneboite/tests/integration
Selenium
echo GREPME started recreating database for selenium tests
mysql -u travis -e 'DROP DATABASE IF EXISTS lbb_test;'
mysql -u travis -e 'CREATE DATABASE IF NOT EXISTS lbb_test DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;'
echo GREPME started migrating database for selenium tests
alembic upgrade head
echo GREPME started populating database for selenium tests
mysql -u travis lbb_test < ./labonneboite/alembic/sql/etablissements_tests_selenium.sql
echo GREPME started indexing data for selenium tests
create_index --full > /dev/null 2>&1  # avoid spamming travis logs
echo GREPME started selenium tests
nosetests labonneboite/tests/selenium
Test that building the docker image does not fail
echo GREPME started building docker image
docker build .
