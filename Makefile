init: init-docs init-dev

init-docs:
	pip3 install mkdocs mkdocs-material

documentation: init-docs
	python3 -m mkdocs serve --dev-addr '127.0.0.1:9999'

init-dev:
	pip3 install poetry
	poetry install --no-root

test: init-dev test-lint test-coverage test-package test-results

test-lint: 
	# lint
	poetry run flake8 --output-file flake8.txt || echo "FAILED flake"
	poetry run flake8_junit flake8.txt flake8.xml
	rm flake8.txt

test-coverage:
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
