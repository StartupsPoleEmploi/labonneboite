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

# Development

## Install


Clone labonneboite repository:

    $ git clone https://github.com/StartupsPoleEmploi/labonneboite.git

Create an [isolated Python environment](https://virtualenv.pypa.io/) using [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/):

    $ mkvirtualenv --python=`which python2.7` lbb
    $ workon lbb

Install OS requirements:

    # On Debian-based OS
    $ sudo apt-get install -y language-pack-fr git python python-dev python-virtualenv python-pip mysql-server libmysqlclient-dev libncurses5-dev build-essential python-numpy python-scipy python-mysqldb chromium-chromedriver xvfb graphviz htop libblas-dev liblapack-dev libatlas-base-dev gfortran

    # On other exotic OS:
    TODO

You will also need to install docker and docker-compose. Follow the instructions related to your particular OS from the [official Docker documentation](https://docs.docker.com/install/).

Install python requirements:

    $ pip install -r requirements.txt

Start required services (MySQL and Elasticsearch):

    $ make services

Create databases and import data:

    $ make data

## Launch web app

    make serve_web_app

The app is available on port `5000` on host machine. Open a web browser, load
http://localhost:5000 and start browsing.

## Running tests

We are using [Nose](https://nose.readthedocs.io/):

    $ make test_unit

About selenium tests: note that your local server must be running for them to pass.


# Debugging

## Accessing your local MySQL

To access your local MySQL in your MySQL GUI, for example using Sequel Pro:

- new connection / select "SSH" tab
- MySQL host: `127.0.0.1:3037`
- Username: `root`
- Password: leave empty
- Database: `labonneboite`

You can also access staging and production DBs using a similar way,
however with great power comes great responsiblity...

## Elasticsearch

- Version used: `1.7.x`
- Doc: https://www.elastic.co/guide/en/elasticsearch/reference/1.7/index.html
- Python binding: http://elasticsearch-py.readthedocs.io/en/1.6.0/

### Accessing your local Elasticsearch

Docker forwards port 9200 from your host to your guest VM.

Simply open http://localhost:9200 in your web browser, or, better, install the chrome extension "Sense".

You can also use `curl` to explore your cluster.

### Examples:

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

## DB content in the development environment

Note that we only have data in Metz region.

Any search on another region than Metz will give zero results.

## Profiling

You will need to install a kgrind file visualizer for profiling. Kgrind files store the detailed results of a profiling.
- For Mac OS install and use QCacheGrind: `brew update && brew install qcachegrind`
- For other OSes: install and use [KCacheGrind](https://kcachegrind.github.io/html/Home.html)

## Running scripts

For example `create_index`:

    $ python labonneboite/scripts/create_index.py

## Running pylint

You can run [pylint](https://www.pylint.org) on the whole project:

    $ make pylint_all

Or on a specific python file:

    $ make pylint FILE=labonneboite/web/app.py

We recommend you use a pylint git pre-commit hook:

    $ pip install git-pylint-commit-hook
    $ vim .git/hooks/pre-commit
    #!/bin/bash
    # (...) previous content which was already present (e.g. nosetests)
    # add the following line at the end of your pre-commit hook file
    git-pylint-commit-hook

## Debugging

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

## Importer

The importer jobs are designed to recreate from scratch a complete dataset of offices.

Here is their normal workflow:

`check_etab` => `extract_etab` => `check_dpae` => `extract_dpae` => `compute_scores` => `validate_scores` => `geocode` => `populate_flags`

Use `make run_importer_jobs` to run all these jobs in local environment.

## Single-ROME vs Multi-ROME search

The company search on the frontend only allows searching for a single ROME (a.k.a. rome_code). However, historically the API allowed for multi-ROME search. This is no longer the case as of mid-2017, and the three reasons why we dropped support for multi-ROME search are:
- so that frontend and API behaviors are as similar as possible.
- tailoring search results to the requested rome_code adds some complexity and would be quite difficult to generalize to a multi-ROME search.
- nobody was actually using API multi-ROME search anyway.

## Load testing (API+Frontend)

We use the Locust framework (http://locust.io/). Here is how to run load testing against your local environment only. For instructions about how to run load testing against production, please see `README.md` in our private repository.

The load testing is designed to run directly from your vagrant VM using 4 cores (feel free to adjust this to your own number of CPUs). It runs in distributed mode (4 locust slaves and 1 master running the web interface).

- First double check your vagrant VM settings directly in VirtualBox interface. You should ensure that your VM uses 4 CPUs and not the default 1 CPU only. You have to make this change once, and you'll most likely need to reboot the VM to do it. Without this change, your VM CPU usage might quickly become the bottleneck of the load testing.
- Read `labonneboite/scripts/loadtesting.py` script and adjust values to your load testing scenario.
- Start your local server `make serve_web_app`
- Start your locust instance `make start_locust_against_localhost`. By default, this will load-test http://localhost:5000. To test a different server, run e.g: `make start_locust_against_localhost LOCUST_HOST=https://labonneboite.pole-emploi.fr` (please don't do this, though).
- Load the locust web interface in your browser: http://localhost:8089
- Start your swarm with for example 1 user then increase slowly and observe what happens.
- As long as your observed RPS stays coherent with your number of users, it means the app behaves correctly. As soon as the RPS is less than it shoud be and/or you get many 500 errors (check your logs) it means the load is too high or that your available bandwidth is too low.

## `create_index.py`

Here is how to profile the `create_index.py` script and its (long) reindexing of all elasticsearch data. This script is the first we had to do some profiling on, but the idea is that all techniques below should be easily reusable for future profilings of other parts of the code.

### Notes

- Part of this script heavily relies on parallel computing (using `multiprocessing` library). However profiling and parallel computing do not go very well together. Profiling the main process will give zero information about what happens inside each parallel job. This is why we also profile from within each job.

### Profiling the full script in local

Reminder: the local database has only a small part of the data .i.e data of only 1 of 96 departements, namely the departement 57. Thus profiling on this dataset is not exactly relevant. Let's still explain the details though.
- `make create_index_from_scratch_with_profiling`

Visualize the results (for Mac OS):
- `qcachegrind labonneboite/scripts/profiling_results/create_index_run.kgrind`
  - you will visualize the big picture of the profiling, however you cannot see there the profiling from within any of the parrallel jobs. 
  
![](https://www.evernote.com/l/ABKrdnXchbJNA6D_tl_PtEYUUezIhiz5DUcB/image.png)  

- `qcachegrind labonneboite/scripts/profiling_results/create_index_dpt57.kgrind`
  - you will visualize the profiling from within the single job reindexing data of departement 57.
  
![](https://www.evernote.com/l/ABLptykQ5cNP7LzMtHOsC9wMVPdnK-wYErYB/image.png)

### Profiling the full script in staging

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

### Profiling a single job in local

Former profiling methods are good to get a big picture however they take quite some time to compute, and sometimes you want a quick profiling in local in order to quickly see the result of some changes. Here is how to do that:
- `make create_index_from_scratch_with_profiling_single_job`

This variant disables parallel computation, skips all tasks but office reindexing, and runs only a single job (departement 57). This makes the result very fast and easy to profile:
- `qcachegrind labonneboite/scripts/profiling_results/create_index_run.kgrind`

![](https://www.evernote.com/l/ABJT1VAV0_xI26HSnAHBP5a7JRSar7CnMjcB/image.png)

### Surgical profiling line by line

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
