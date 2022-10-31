# /bin/bash

testReturn=0

failed() {
    testReturn=1
    echo "FAILED $1"
}

set -ex

# alembic
poetry run alembic -c labonneboite/alembic.ini upgrade head 

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
if ! poetry run flake8 --output-file flake8.txt; then
    failed "flake"
    poetry run flake8_junit flake8.txt flake8.xml && echo
rm flake8.txt
fi

# -- unit test & coverage
# -- api
if ! poetry run pytest --junitxml=pytest-web-api.xml --cov --html=pytest-web-api.html; then
    failed "pytest"
fi
poetry run coverage xml

# -- build package
if ! poetry build; then
    failed "build"
fi

# prepare test results
echo "Moving test results file..."
mkdir -p testResults
mv *.xml ./testResults
mv *.html ./testResults
echo "Done"

exit $testReturn
