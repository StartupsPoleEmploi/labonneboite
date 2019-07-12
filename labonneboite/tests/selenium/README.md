# Functional tests (using Selenium)

Tests in this folder are very high-level: they mimic users behavior, clicking on buttons or doing searchs using forms.

Content:
- [Executing tests](#executing-tests)
- [Data](#data)
- [Debugging](#debugging)


## Executing tests

To run them, simply use this make command: `make services && make test-selenium`
This will do the following actions:
- start a database,
- clean existing data,
- create a new test database,
- populate it with dummy data,
- run Selenium tests without displaying a browser.

To execute only one set of tests, use this command: `LBB_ENV=test nosetests -s labonneboite/tests/selenium/test_whatever_you_want.py `.


## Data

We use an SQL script to populate data into the local database. It is located here: `labonneboite/alembic/sql/etablissements_test_selenium.sql`. Feel free to change or add any data but be careful to the following:
- ROME code has an impact on search results.
- office score should be high enough to ensure Elastic Search will index it. To be sure, just use a score of '98'.
- instead of using the zipcode (_code postal_), Elastic Search uses the town code (_code commune_). Make sure they match as they are not the same! [This website](http://code.postal.fr) may help recovering a town code from a zipcode.

To make sure data are retrievable using our search feature:
- inspect the database using a SQL GUI (or any tool of your convenience) and check if fields are ok. Every office should be present.
- have a look at Elastic Search and check if offices are indexed.

```

# Get indices
$ curl "localhost:9200/_cat/indices?v"
yellow open   labonneboite_unit_test-20190710114238-xnmxw   5   1      60736            2     41.5mb         41.5mb

# Find an office using its SIRET (which is also its ID)
# curl -X GET "localhost:9200/indice_name/document_type/document_id?pretty"
curl -X GET "localhost:9200/labonneboite_unit_test-20190710114238-xnmxw/office/10150000700329?pretty"
```


## Debugging

If you try to add a breaking point using PDB (or IPDB) anywhere in the project, it won't work as expected. In fact, it will break but you won't be able to interact with the program.

Better use loggers with a critical level to be make they pop up. For example:
```
from flask import current_app
current_app.logger.critical('HEY, SHOW ME!')
```

## Isochrone tests

They use custom backends to mock API calls: `ign_mock` and `navitia_mock`. Check that they are activated in your settings:

_conf/common/overrides/test.py_
```
TRAVEL_VENDOR_BACKENDS = {
    'isochrone': {
        'car': 'ign_mock',
        'public': 'navitia_mock',
    },
    'durations': {
        'car': 'dummy',
        'public': 'dummy',
    },
}
```

For the moment, we only test searches using commute duration.
Displaying commute time in individual office details is not tested.