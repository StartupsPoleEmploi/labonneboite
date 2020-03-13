```
 _       _                            _           _ _
| | __ _| |__   ___  _ __  _ __   ___| |__   ___ (_) |_ ___
| |/ _` | '_ \ / _ \| '_ \| '_ \ / _ \ '_ \ / _ \| | __/ _ \
| | (_| | |_) | (_) | | | | | | |  __/ |_) | (_) | | ||  __/
|_|\__,_|_.__/ \___/|_| |_|_| |_|\___|_.__/ \___/|_|\__\___|
```

[![Build Status](https://travis-ci.org/StartupsPoleEmploi/labonneboite.svg?branch=master)](https://travis-ci.org/StartupsPoleEmploi/labonneboite)

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

La Bonne Boite c’est un [site web](https://labonneboite.pole-emploi.fr) mais aussi une [API](https://www.emploi-store-dev.fr/portail-developpeur/detailapicatalogue/57909ba23b2b8d019ee6cc5f)

La Bonne Boite, [on en parle dans la presse](https://labonneboite.pole-emploi.fr/espace-presse)

# Project overview

[A 2016 study by INSEE](https://insee.fr/fr/statistiques/2901587) states that 7% of recruitments come from job offers, whereas **42%** come from unsollicited applications. Thus the « hidden market » (not materialized in job offers) is the first source of recruitements in France!

La Bonne Boite (LBB) is a service launched by Pole Emploi (french national employment agency) to offer a new way for job seekers to look for a new job. Instead of searching for job offers, the job seeker can look directly for companies that have a high "hiring potential" and send them unsollicited applications. The "hiring potential" is an algorithm exclusivity created by Pole Emploi that estimates how many contracts a given company is likely to hire in the next 6 months.

By only contacting companies with a high "hiring potential", job seekers can focus their efforts only on companies that are likely to hire them. Instead of targeting every and any company that might potentially be interested by their profile, La Bonne Boite drastically reduces the number of companies a job seeker needs to have in mind when looking for a job.

The "hiring potential" is an indicator based on a machine learning model, in this case a regression. La Bonne Boite processes millions of recrutements of all french companies over years to compute this "hiring potential".

It has already been deployed in France with early results that are very promising. Early development is being made for new countries (Luxembourg).

La Bonne Boite is a [web site](https://labonneboite.pole-emploi.fr) and an [API](https://www.emploi-store-dev.fr/portail-developpeur/detailapicatalogue/57909ba23b2b8d019ee6cc5f).

[Press Coverage on La Bonne Boite](https://labonneboite.pole-emploi.fr/espace-presse)

# Development

Table of contents:

- [Installation](#install)
- [Launch web app in development](#launch-web-app)
- [Run asynchronous tasks](#run-asynchronous-tasks)
- [Run tests](#run-tests)
- [Access your local MySQL](#access-your-local-mysql)
- [Elastic Search](#elasticsearch)
- [DB content in the development environment](#db-content-in-the-development-environment)
- [Running scripts](#running-scripts)
- [Code quality](#code-quality)
- [Debugging safely in development, staging or production](#debugging-safely-in-a-development-staging-or-production-environment)
- [Importer](#importer)
- [Single ROME versus multi-ROME search](#single-rome-vs-multi-rome-search)
- [Load testing (API and front end)](#load-testing-apifrontend)
- [Profiling](#profiling)
- [How to contribute](#how-to-contribute)
- [Je Postule](#je-postule)
- [Further documentation](#further-documentation)


## Install

### Install OS requirements:

On Debian-based OS:

    $ sudo apt-get install -y language-pack-fr git python3 python3-dev python-virtualenv python-pip mysql-server libmysqlclient-dev libncurses5-dev build-essential python-numpy python-scipy python-mysqldb chromium-chromedriver xvfb graphviz htop libblas-dev liblapack-dev libatlas-base-dev gfortran

    # On Mac OS:

    $ brew install openssl selenium-server-standalone
    $ brew switch openssl 1.0.2s  # fixes error about libssl 1.0.0 missing
    $ brew cask install chromedriver

You will also need to install docker and docker-compose. Follow the instructions related to your particular OS from the [official Docker documentation](https://docs.docker.com/install/).

### Create a virtualenv for Python 3.6

For now, La Bonne Boite runs in production under Python 3.6.8. You are going to have to create a virtualenv that runs this specific version of Python.

Create an [isolated Python environment](https://virtualenv.pypa.io/), for example using [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/):

    $ mkvirtualenv --python=`which python3.6` lbb
    $ workon lbb

You might need to add `labonneboite` base directory to the Python path. This has to be run only once. One way to do it using `virtualenvwrapper`:

    $ add2virtualenv $PWD

### Install python requirements:

Our requirements are managed with [`pip-tools`](https://github.com/jazzband/pip-tools).

Note that you will need a local version of MySQL with `mysql_config` to install `mysqlclient`.

    pip install --upgrade pip
    pip install pip-tools
    make compile-requirements

To update your virtualenv, you must then run:

    pip-sync
    python setup.py develop

#### How to upgrade a specific package

To upgrade a package DO NOT EDIT `requirements.txt` DIRECTLY! Instead, run:

    pip-compile -o requirements.txt --upgrade-package mypackagename requirements.in

This last command will upgrade `mypackagename` and its dependencies to the latest version.

### Start required services (MySQL and Elasticsearch)

    $ make services

### Create databases and import data

    $ make data

If needed, run `make clear-data` to clear any old/partial data you might already have.

### Populate Elastic Search

This is required for autocomplete and search to work

    $ make create-index

#### Known issues

You may have to run `sudo usermod -a -G docker $USER`, then reboot your computer to enable the current user to use docker, as the problem is described [here](https://techoverflow.net/2017/03/01/solving-docker-permission-denied-while-trying-to-connect-to-the-docker-daemon-socket/)

MacOS users, if you get a `ld: library not found for -lintl` error when running `pip-sync`, try this fix: `ln -s /usr/local/Cellar/gettext/0.19.8.1/lib/libintl.* /usr/local/lib/`. For more information see [this post](https://github.com/unbit/uwsgi-docs/issues/363).

## Launch web app

    make serve-web-app

The app is available on port `5000` on host machine. Open a web browser, load
http://localhost:5000 and start browsing.

## Run asynchronous tasks

Some parts of the code are run in a separate task queue which can be launched with:

    make consume-tasks

Or in development:

    make consume-tasks-dev

Asynchronous tasks are backed by Redis and [Huey](https://huey.readthedocs.io/en/latest/).

## Run tests

We are using [Nose](https://nose.readthedocs.io/):

    $ make test-all

## Access your local MySQL

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

### Access your local Elasticsearch

Docker forwards port 9200 from your host to your guest VM.

Simply open http://localhost:9200 in your web browser, or, better, install the chrome extension "Sense".

You can also use `curl` to explore your cluster.

### Examples

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

## Running scripts

For example `create_index`:

    $ python labonneboite/scripts/create_index.py

## Code quality

We use three code quality tools: black, isort and flake8.

Run `make quality` for run all three of them. Or `make black`, `make isort` and `make flake8` separately.

Black and isort will automatically apply changes for you, however flake8 requires you to manually fix every issue.

We recommend you run `make setup_git_pre_commit_hook` to setup a git pre-commit hook which will run both black and isort automatically before every commit.

You will still have to run flake 8 manually though.

## Debugging safely in a development, staging or production environment

### Development

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


### Staging or production

Debugging **safely** in staging and in production is hard but not impossible! Here is how you can do.


#### Set a breaking point and target it
Add a breaking point in your code.

:warning: This will of course block each incoming request, so make sure you know what you do.

Example:

```
# views.py
import requests

app.route('/armstrong')
def armstrong():
    if request.args('pdb'):
        from remote_pdb import RemotePdb
        RemotePdb('0.0.0.0', 4444).set_trace()
    return redirect(url_for('root.home'))
```

Then target your breaking point making a request to your route. Example:

```
import requests
requests.get('http://wonderful.world/armstrong?pdb=true')
```

Nothing happens, it's normal! Time for step two.


#### Getting the IP address if you're using Docker

Connect to the server via ssh.

Then get the container IP:

```
$ docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' container_name_or_id
# to get the container name, do a `docker ps`

176.3.33.3
```

Connect to your breaking point with telnet :

```
$ telnet 176.3.33.3 4444
Trying 176.3.33.3...
Connected to 176.3.33.3.
Escape character is '^]'.
>
```

#### If you're not using Docker

Connect to the server via ssh.

Then enter your breaking point with telnet :

```
$ telnet 0.0.0.0 4444
Trying 0.0.0.0...
Connected to 0.0.0.0.
Escape character is '^]'.
>
```

#### Exiting pdb and telnet

To exit pdb, type 'c' in pdb and then `ctrl+]`.

Then type `quit` to exit telnet.

```
(Pdb) c
# Then type 'ctrl + ]'
^]
# And type 'quit'
telnet> quit
Connection closed.
```


## Importer

The importer jobs are designed to recreate from scratch a complete dataset of offices.

Here is their normal workflow:

`check_etab` => `extract_etab` => `check_dpae` => `extract_dpae` => `compute_scores` => `validate_scores` => `geocode` => `populate_flags`

Use `make run-importer-jobs` to run all these jobs in local development environment.

## Single-ROME vs Multi-ROME search

The company search on the frontend only allows searching for a single ROME (a.k.a. rome_code). However, the API allows for multi-ROME search, both when sorting by distance and by score.

## Load testing (API+Frontend)

We use the Locust framework (http://locust.io/). Here is how to run load testing against your local environment only. For instructions about how to run load testing against production, please see `README.md` in our private repository.

The load testing is designed to run directly from your vagrant VM using 4 cores (feel free to adjust this to your own number of CPUs). It runs in distributed mode (4 locust slaves and 1 master running the web interface).

- First double check your vagrant VM settings directly in VirtualBox interface. You should ensure that your VM uses 4 CPUs and not the default 1 CPU only. You have to make this change once, and you'll most likely need to reboot the VM to do it. Without this change, your VM CPU usage might quickly become the bottleneck of the load testing.
- Read `labonneboite/scripts/loadtesting.py` script and adjust values to your load testing scenario.
- Start your local server `make serve-web-app`
- Start your locust instance `make start-locust-against-localhost`. By default, this will load-test http://localhost:5000. To test a different server, run e.g: `make start-locust-against-localhost LOCUST_HOST=https://labonneboite.pole-emploi.fr` (please don't do this, though).
- Load the locust web interface in your browser: http://localhost:8089
- Start your swarm with for example 1 user then increase slowly and observe what happens.
- As long as your observed RPS stays coherent with your number of users, it means the app behaves correctly. As soon as the RPS is less than it shoud be and/or you get many 500 errors (check your logs) it means the load is too high or that your available bandwidth is too low.

## Profiling

You will need to install a kgrind file visualizer for profiling. Kgrind files store the detailed results of a profiling.
- For Mac OS install and use QCacheGrind: `brew update && brew install qcachegrind`
- For other OSes: install and use [KCacheGrind](https://kcachegrind.github.io/html/Home.html)

### Profiling `create_index.py`

Here is how to profile the `create_index.py` script and its (long) reindexing of all elasticsearch data. This script is the first we had to do some profiling on, but the idea is that all techniques below should be easily reusable for future profilings of other parts of the code.

### Notes

- Part of this script heavily relies on parallel computing (using `multiprocessing` library). However profiling and parallel computing do not go very well together. Profiling the main process will give zero information about what happens inside each parallel job. This is why we also profile from within each job.

### Profiling the full script in local

Reminder: the local database has only a small part of the data .i.e data of only 1 of 96 departements, namely the departement 57. Thus profiling on this dataset is not exactly relevant. Let's still explain the details though.
- `make create-index-from-scratch-with-profiling`

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
- `make create-index-from-scratch-with-profiling-on-staging`

Visualize the results (for Mac OS):
- `qcachegrind labonneboite/scripts/profiling_results/staging/create_index_run.kgrind`
  - you will visualize the big picture of the profiling, and as you have the full dataset, you will get the correct big picture about the time ratio between high-level methods:

![](https://www.evernote.com/l/ABIF2kbcoFtJCqDkThppsj98o8K1B7B__LUB/image.png)

- `qcachegrind labonneboite/scripts/profiling_results/staging/create_index_dpt57.kgrind`
  - you will visualize the profiling from within the single job reindexing data of departement 57.

![](https://www.evernote.com/l/ABKoq_-DZw1GlqbPyISsH_-MbQbxVyy9WoAB/image.png)

### Profiling a single job in local

Former profiling methods are good to get a big picture however they take quite some time to compute, and sometimes you want a quick profiling in local in order to quickly see the result of some changes. Here is how to do that:
- `make create-index-from-scratch-with-profiling-single-job`

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


## How to contribute

For devs in the core team, this repo follows the [Feature Branch Workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/feature-branch-workflow).

We are also open to comments, questions and contributions from devs outside the core dev team! Here is [a document about contributions to this project (in french)](/CONTRIBUTING.md)

## Je Postule

[_Je Postule_](https://github.com/StartupsPoleEmploi/jepostule) ("I apply") allows job seekers to apply directly and quickly to companies, which in turn can provide quick answers to applications. It can be integrated to many applications, like we did in La Bonne Boite.

In order to link your local instance of labonneboite with a local instance of jepostule, you will need to edit the file `labonneboite/conf/local_settings.py` to override the settings of the section "Je postule" from the file `labonneboite/conf/common/settings_common.py`. In particular you will need to set the client ID and client secret provided by jepostule when you create a client platform as explained in the README section "Create a client platform".

:point_up: If you want to disable Je Postule features in La Bonne Boite, you can do it pretty easily editing the `JEPOSTULE_QUOTA` setting:

```
JEPOSTULE_QUOTA = 0 # put 1 if you want to enable it.
```


## Further documentation

- [Data management](/ROME_NAF)
- [Search using isochrone data](/labonneboite/common/maps)
- [Database migration system](/labonneboite/alembic)
- [User Authentication system](/labonneboite/web/auth)
- [Functional tests](/labonneboite/tests/selenium)
