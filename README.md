```
 _       _                            _           _ _
| | __ _| |__   ___  _ __  _ __   ___| |__   ___ (_) |_ ___
| |/ _` | '_ \ / _ \| '_ \| '_ \ / _ \ '_ \ / _ \| | __/ _ \
| | (_| | |_) | (_) | | | | | | |  __/ |_) | (_) | | ||  __/
|_|\__,_|_.__/ \___/|_| |_|_| |_|\___|_.__/ \___/|_|\__\___|
```

# Présentation du projet

Quel est le canal le plus utilisé par les chercheurs d'emploi pour rechercher un emploi ?
...
Les offres d'emploi.

Quel est le canal le plus utilisé par les employeurs pour recruter ?
...
Les candidatures spontanées.

Selon [une enquête de l’INSEE](https://insee.fr/fr/statistiques/2901587), 7% des recrutements se font via des offres, contre **42%** via des candidatures spontanées. Le « marché caché » (qui n’est pas matérialisé dans des offres) est donc la première source de recrutement en France !

La Bonne Boite (LBB) est un service lancé par Pôle emploi pour permettre aux chercheurs d’emploi de cibler plus efficacement leurs candidatures spontanées : l'utilisateur accède à la liste des entreprises à « haut potentiel d'embauche ». Le « potentiel d'embauche » est un indicateur exclusif inventé par Pôle emploi pour prédire le nombre de recrutements (CDI et CDD de plus de un mois) d’une entreprise donnée dans les 6 prochains mois.

En contactant des entreprises à « haut potentiel d'embauche », le chercheur d'emploi concentre ses efforts uniquement sur les entreprises qui sont le plus susceptibles de l'embaucher. La Bonne Boite lui permet ainsi de réduire drastiquement le nombre d'entreprises à contacter et d'être plus efficace dans sa recherche.

Le « potentiel d'embauche » est un indicateur basé sur une technique d'intelligence artificielle (apprentissage automatique ou "machine learning"), en l'occurence un algorithme de régression. Pour calculer un potentiel d’embauche, La Bonne Boite analyse des millions de recrutements de toutes les entreprises de France depuis plusieurs années.

La Bonne Boite a été déployée en France avec des premiers résultats encourageants, et est en cours de développement pour d'autres pays (Luxembourg).

La Bonne Boite c’est un [site web](https://labonneboite.pole-emploi.fr) mais aussi une [API](https://www.emploi-store-dev.fr/portail-developpeur/detailapicatalogue/labonneboite)

La Bonne Boite, [on en parle dans la presse](https://labonneboite.pole-emploi.fr/espace-presse)

# Project overview

[A 2016 study by INSEE](https://insee.fr/fr/statistiques/2901587) states that 7% of recruitments come from job offers, whereas **42%** come from unsollicited applications. Thus the « hidden market » (not materialized in job offers) is the first source of recruitements in France!

La Bonne Boite (LBB) is a service launched by Pole Emploi (french national employment agency) to offer a new way for job seekers to look for a new job. Instead of searching for job offers, the job seeker can look directly for companies that have a high "hiring potential" and send them unsollicited applications. The "hiring potential" is an algorithm exclusivity created by Pole Emploi that estimates how many contracts a given company is likely to hire in the next 6 months.

By only contacting companies with a high "hiring potential", job seekers can focus their efforts only on companies that are likely to hire them. Instead of targeting every and any company that might potentially be interested by their profile, La Bonne Boite drastically reduces the number of companies a job seeker needs to have in mind when looking for a job.

The "hiring potential" is an indicator based on a machine learning model, in this case a regression. La Bonne Boite processes millions of recrutements of all french companies over years to compute this "hiring potential".

It has already been deployed in France with early results that are very promising. Early development is being made for new countries (Luxembourg).

La Bonne Boite is a [web site](https://labonneboite.pole-emploi.fr) and an [API](https://www.emploi-store-dev.fr/portail-developpeur/detailapicatalogue/labonneboite).

[Press Coverage on La Bonne Boite](https://labonneboite.pole-emploi.fr/espace-presse)

# Install a new development environment

- Install Ansible:

    - create an [isolated Python environment](https://virtualenv.pypa.io/) using [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/):

      ```
      $ mkvirtualenv --python=`which python2.7` lbb
      $ workon lbb
      $ pip install ansible
      ```

- Install [VirtualBox](https://www.virtualbox.org/wiki/Downloads)

- Install [Vagrant](https://www.vagrantup.com/downloads.html)

- Fetch labonneboite repository `git clone https://github.com/StartupsPoleEmploi/labonneboite.git`

    - ensure your ssh public key has been properly setup

    - note that you'll be using the user `git`, unlike other services which use nominative usernames

- Create a settings file (see below)

- `make vagrant_start`

Go get coffee and look into the LBB code in the meantime, it's going to take a while.

Most likely, `vagrant up` **will throw some error and not finish the first time**, we need to finish the provisioning process by running:

- `make vagrant_provision`

until it does.

# Create a settings file

Create a `labonneboite/labonneboite/conf/local_settings.py` file with the following values (ask your colleagues for some sensitive values):

```
USER = 'labonneboite'
PASSWORD = 'labonneboite'
DB = 'labonneboite'
DEBUG = True

OFFICE_TABLE = 'etablissements'
MANDRILL_API_KEY = '<set it>'
LOCALE = 'fr_FR'

GLOBAL_STATIC_PATH = '/tmp'

FLASK_SECRET_KEY = 'bbbbbbbbbbbbbbbbbccccccccccccc'
ADMIN_EMAIL = '<set it>'
CONTACT_EMAIL = '<set it>'
FORM_EMAIL = '<set it>'
GMAIL_USER = '<set it>'
GMAIL_PASSWORD = '<set it>'

API_KEYS = {
    'labonneboite': '1234567890abcdef',
    'emploi_store_dev': '1234567890abcdef',
}

LOG_LEVEL = 'DEBUG'

PEAM_CLIENT_ID = '<set it>'
PEAM_CLIENT_SECRET = '<set it>'
PEAM_AUTH_BASE_URL = '<set it>'
PEAM_API_BASE_URL = '<set it>'
PEAM_USERINFO_URL = '<set it>'

VERSION_PRO_ALLOWED_IPS = ['<set it>', '<set it>', '<set it>']
VERSION_PRO_ALLOWED_EMAILS = ['<set it>', '<set it>', '<set it>']
VERSION_PRO_ALLOWED_EMAIL_SUFFIXES = ['<set it>', '<set it>', '<set it>']
VERSION_PRO_ALLOWED_EMAIL_REGEXPS = ['<set it>', '<set it>', '<set it>']

# Values below are *fake* and should be used in development and test environments only.
# The real values are confidential, stored outside of github repository
# and are only used in production+staging.
SCORE_50_HIRINGS = 10.0
SCORE_60_HIRINGS = 50.0
SCORE_80_HIRINGS = 100.0
SCORE_100_HIRINGS = 500.0
```

# Launch LBB web app

If your vagrant environment is not running, run:

    make vagrant_start

Then run:

    make serve_web_app

The app is available on port `8090` on host machine. Open a web browser,
load http://localhost:8090 and start browsing.

# Accessing your local MySQL

To access your local MySQL in your MySQL GUI, for example using Sequel Pro:

- new connection / select "SSH" tab
- MySQL host: `127.0.0.1`
- Username: `root`
- Password: leave empty
- Database: `labonneboite`
- SSH Host: `127.0.0.1`
- SSH User: `vagrant`
- SSH Password: `vagrant`
- SSH Port: `2222`

You can also access staging and production DBs using a similar way,
however with great power comes great responsiblity...

# Elasticsearch

- Version used: `1.7.x`
- Doc: https://www.elastic.co/guide/en/elasticsearch/reference/1.7/index.html
- Python binding: http://elasticsearch-py.readthedocs.io/en/1.6.0/

## Accessing your local Elasticsearch

Vagrant already forward port 9200 from your host to your guest VM.

Simply open http://localhost:9200 in your web browser, or, better, install the chrome extension "Sense".

You can also use `curl` to explore your cluster.

## Examples:

Locally:

    # Cluster health check.
    curl 'localhost:9200/_cat/health?v'

    # List of nodes in the cluster.
    curl 'localhost:9200/_cat/nodes?v'

    # List of all indexes (indices).
    curl 'localhost:9200/_cat/indices?v'

    # Get information about one index.
    curl 'http://localhost:9200/labonneboite/?pretty'

    # Retrieve mapping definitions for an index or type.
    curl 'http://localhost:9200/labonneboite/_mapping/?pretty'
    curl 'http://localhost:9200/labonneboite/_mapping/office?pretty'

    # Search explicitly for documents of a given type within the labonneboite index.
    curl 'http://localhost:9200/labonneboite/office/_search?pretty'
    curl 'http://localhost:9200/labonneboite/ogr/_search?pretty'
    curl 'http://localhost:9200/labonneboite/location/_search?pretty'

# DB content in the development environment

Note that we only have data in Metz region.

Any search on another region than Metz will give zero results.

# Running tests

We are using [Nose](https://nose.readthedocs.io/).

Tests which can run in development:

    $ make test_importer
    $ make test_app
    $ make test_api
    $ make test_integration
    $ make test_selenium
    $ make test_scripts
    $ make test_integration

You can run all tests with:

    $ make test_all

About selenium tests: note that your local server must be running for them to pass.

# Running scripts

For example `create_index`:

    $ make vagrant_ssh
    $ python /srv/lbb/labonneboite/scripts/create_index.py

# Running pylint

You can run [pylint](https://www.pylint.org) on the whole project:

    $ make pylint_all

Or on a specific python file:

    $ make pylint ARGS=labonneboite/web/app.py

We recommend you use a pylint git pre-commit hook:

    $ pip install git-pylint-commit-hook
    $ vim .git/hooks/pre-commit
    #!/bin/bash
    # (...) previous content which was already present (e.g. nosetests)
    # add the following line at the end of your pre-commit hook file
    git-pylint-commit-hook

# Debugging

    # anywhere in the code
    logger.info("message")

    # for an interactive debugger, use one of these,
    # depending on which place of the code you are

    # if you are inside the web app code
    raise # then you can use the console on the error page web interface

    # if you are inside a test code
    from nose.tools import set_trace; set_trace()

    # if you are inside a script code (e.g. scripts/create_city_file.py)
    # also works inside the web app code
    from IPython import embed; embed()
    # and/or
    import ipdb; ipdb.set_trace()

# Importer

The importer jobs are designed to recreate from scratch a complete dataset of offices.

Here is their normal workflow:

`check_etab` => `extract_etab` => `check_dpae` => `extract_dpae` => `compute_scores` => `validate_scores` => `geocode` => `populate_flags`

Use `make run_importer_jobs` to run all these jobs in local environment.

# Single-ROME vs Multi-ROME search

The company search on the frontend only allows searching for a single ROME (a.k.a. rome_code). However, historically the API allowed for multi-ROME search. This is no longer the case as of mid-2017, and the three reasons why we dropped support for multi-ROME search are:
- so that frontend and API behaviors are as similar as possible.
- tailoring search results to the requested rome_code adds some complexity and would be quite difficult to generalize to a multi-ROME search.
- nobody was actually using API multi-ROME search anyway.

# Load testing (API+Frontend)

We use the Locust framework (http://locust.io/). Here is how to run load testing against your local environment only. For instructions about how to run load testing against production, please see `README.md` in our private repository.

The load testing is designed to run directly from your vagrant VM using 4 cores (feel free to adjust this to your own number of CPUs). It runs in distributed mode (4 locust slaves and 1 master running the web interface).

- First double check your vagrant VM settings directly in VirtualBox interface. You should ensure that your VM uses 4 CPUs and not the default 1 CPU only. You have to make this change once, and you'll most likely need to reboot the VM to do it. Without this change, your VM CPU usage might quickly become the bottleneck of the load testing.
- Read `labonneboite/scripts/loadtesting.py` script and adjust values to your load testing scenario.
- Start your local server `make serve_web_app`
- Start your locust instance `make start_locust_against_localhost`
- Load the locust web interface in your browser: http://localhost:8089
- Start your swarm with for example 1 user then increase slowly and observe what happens.
- As long as your observed RPS stays coherent with your number of users, it means the app behaves correctly. As soon as the RPS is less than it shoud be and/or you get many 500 errors (check your logs) it means the load is too high.

# Profiling

Here is how to profile the `create_index.py` script and its (long) reindexing of all elasticsearch data. This script is the first we had to do some profiling on, but the idea is that all techniques below should be easily reusable for future profilings of other parts of the code.

## Requirements

Most libraries needed are already in `requirements.txt`, however you need to install a kgrind file visualizer. Kgrind files store the detailed results of a profiling.
- For Mac OS install and use QCacheGrind: `brew update && brew install qcachegrind`
- For other OSes: install and use [KCacheGrind](https://kcachegrind.github.io/html/Home.html)

## Notes

- Part of this script heavily relies on parallel computing (using `multiprocessing` library). However profiling and parallel computing do not go very well together. Profiling the main process will give zero information about what happens inside each parallel job. This is why we also profile from within each job.

## Profiling the full script in local

Reminder: the local database has only a small part of the data .i.e data of only 1 of 96 departements, namely the departement 57. Thus profiling on this dataset is not exactly relevant. Let's still explain the details though.
- `make create_index_from_scratch_with_profiling`

Visualize the results (for Mac OS):
- `qcachegrind labonneboite/scripts/profiling_results/create_index_run.kgrind`
  - you will visualize the big picture of the profiling, however you cannot see there the profiling from within any of the parrallel jobs. 
  
![](https://www.evernote.com/l/ABKrdnXchbJNA6D_tl_PtEYUUezIhiz5DUcB/image.png)  

- `qcachegrind labonneboite/scripts/profiling_results/create_index_dpt57.kgrind`
  - you will visualize the profiling from within the single job reindexing data of departement 57.
  
![](https://www.evernote.com/l/ABLptykQ5cNP7LzMtHOsC9wMVPdnK-wYErYB/image.png)

## Profiling the full script in staging

*Warning: in order to do this, you need to have ssh access to our staging server.*

The full dataset (all 96 departements) is in staging which makes it a very good environment to run the full profiling to get a big picture.
- `make create_index_from_scratch_with_profiling_on_staging`

Visualize the results (for Mac OS):
- `qcachegrind labonneboite/scripts/profiling_results/staging/create_index_run.kgrind`
  - you will visualize the big picture of the profiling, and as you have the full dataset, you will get the correct big picture about the time ratio between high-level methods:

![](https://www.evernote.com/l/ABIF2kbcoFtJCqDkThppsj98o8K1B7B__LUB/image.png)

- `qcachegrind labonneboite/scripts/profiling_results/staging/create_index_dpt57.kgrind`
  - you will visualize the profiling from within the single job reindexing data of departement 57.

![](https://www.evernote.com/l/ABKoq_-DZw1GlqbPyISsH_-MbQbxVyy9WoAB/image.png)

## Profiling a single job in local

Former profiling methods are good to get a big picture however they take quite some time to compute, and sometimes you want a quick profiling in local in order to quickly see the result of some changes. Here is how to do that:
- `make create_index_from_scratch_with_profiling_single_job`

This variant disables parallel computation, skips all tasks but office reindexing, and runs only a single job (departement 57). This makes the result very fast and easy to profile:
- `qcachegrind labonneboite/scripts/profiling_results/create_index_run.kgrind`

![](https://www.evernote.com/l/ABJT1VAV0_xI26HSnAHBP5a7JRSar7CnMjcB/image.png)

## Surgical profiling line by line

Profiling techniques above can give you a good idea of the performance big picture, but sometimes you really want to dig deeper into very specific and critical methods. For example above we really want to investigate what happens within the `get_scores_by_rome` method which seems critical for performance.

Let's do a line by line profiling using https://github.com/rkern/line_profiler.

Simply add a `@profile` decorator to any method you would like to profile line by line e.g.

```
@profile
def get_scores_by_rome(office, office_to_update=None):
```

You can perfectly profile methods in other parts of the code than `create_index.py`.

Here is an example of output:

![](https://www.evernote.com/l/ABJdN3iVDEJFgLeH2HgHyYOVMjOYK0a30e4B/image.png)





