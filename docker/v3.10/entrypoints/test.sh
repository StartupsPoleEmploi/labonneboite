# /bin/bash

set -ex

# alembic
poetry run alembic upgrade head 

# run custom sql scripts if any
echo 'Running sql scripts if any'
for i in `/bin/ls -1 /sql/*.sql`; do 
    echo $i
    mysql --user=$DB_USER \
        --password=$DB_PASSWORD \
        --host=$DB_HOST \
        --port=$DB_PORT \
        --database=$DB_NAME < $i
done

# create the index in elastic search
poetry run create_index --full

# run the tests
# -- lint
poetry run flake8 --output-file flake8.txt || echo "FAILED flake"
poetry run flake8_junit flake8.txt flake8.xml
rm flake8.txt

# -- unit test & coverage
# -- api
poetry run pytest --junitxml=pytest-web-api.xml --cov --html=pytest-web-api.html
poetry run coverage xml

# -- build package
poetry build

# prepare test results
echo "Moving test results file..."
mkdir -p testResults
mv *.xml  ./testResults
mv *.html  ./testResults
echo "Done"