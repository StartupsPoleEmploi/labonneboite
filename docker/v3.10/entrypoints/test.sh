# /bin/bash

testReturn=0

failed() {
    testReturn=1
    echo "FAILED $1"
}

set -ex

# alembic
poetry run alembic -c labonneboite/alembic.ini upgrade head

# run the tests
# -- lint
if ! poetry run flake8 --output-file flake8.txt; then
    failed "flake"
    poetry run flake8_junit flake8.txt flake8.xml && echo
    rm flake8.txt
fi

# -- unit test & coverage
# -- api
if ! poetry run pytest --junitxml=pytest-web-api.xml --cov --html=pytest-web-api.html --maxfail=${MAXFAIL:-1000}; then
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
