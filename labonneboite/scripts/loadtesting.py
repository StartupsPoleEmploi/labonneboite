# coding: utf8

"""
Load testing API+Frontend using Locust framework.

See README.md to learn how to start locust interface.

The key parameters below you should adjust to your needs are:
- SECONDS_BETWEEN_TASKS
- `@task(n)` n value for each task

Here are two example scenarios you could test:

1) API requests only

- set SECONDS_BETWEEN_TASKS to 1
- set api_search task(1) and all other to task(0)

2) Frontend requests only

- set SECONDS_BETWEEN_TASKS to 10
- api_search task(0)
- frontend_search task(50)
- suggest_job_labels task(60)
- suggest_cities task(20)
- download_company task(2)

These ratios (50/60/20/2) directly come from observed ratios in production.
On average in production, we observe that for 50 frontend searches,
we get 60 suggest_job_labels requests, 20 suggest_cities requests etc..
"""

import random
import os
import csv
import math
from operator import itemgetter
import urllib
import logging

from slugify import slugify
from locust import HttpLocust, TaskSet, task

from labonneboite.importer import util as import_util
from labonneboite.conf import settings
from labonneboite.web.api import util

logger = logging.getLogger(__name__)
logger.info("loading locustfile")

con, cur = import_util.create_cursor()

# For each locust, number of seconds between its tasks.
# Default value : 1
SECONDS_BETWEEN_TASKS = 1


def generate_siret_choices():
    cur.execute("select siret from %s limit 100000" % (settings.OFFICE_TABLE))
    con.commit()
    rows = cur.fetchall()
    return [row[0] for row in rows]

SIRET_CHOICES = generate_siret_choices()


def generate_city_choices():
    fullname = os.path.join(os.path.dirname(os.path.realpath(__file__)),
        "../../labonneboite/common/data/consolidated_cities.csv")
    with open(fullname, "r") as city_file:
        reader = csv.reader(city_file)
        cities = []
        for city_name, first_zipcode, population, _, _ in reader:
            cities.append([city_name, first_zipcode, int(population)])
        cities_by_population = sorted(cities, key=itemgetter(2), reverse=True)
        city_choices = []
        for city in cities_by_population[:2000]:
            name, zipcode, population = city
            city_choices.append([(name, zipcode), math.log10(population)])
        return city_choices

CITY_CHOICES = generate_city_choices()


def generate_commune_choices():
    fullname = os.path.join(os.path.dirname(os.path.realpath(__file__)),
        "../../labonneboite/common/data/villes_france.csv")
    with open(fullname, "r") as commune_file:
        reader = csv.reader(commune_file)
        commune_choices = []
        for line in reader:
            commune_id = line[10]
            commune_choices.append(commune_id)
        return commune_choices

COMMUNE_CHOICES = generate_commune_choices()


def weighted_choice(choices):
    total = sum(w for c, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices:
        if upto + w >= r:
            return c
        upto += w
    assert False, "Shouldn't get here"


def pick_commune():
    return random.choice(COMMUNE_CHOICES)


def pick_location():
    city, zipcode = weighted_choice(CITY_CHOICES)
    return city, zipcode


def pick_job_name():
    return random.choice(settings.ROME_DESCRIPTIONS.values())


def pick_job_rome():
    return random.choice(settings.ROME_DESCRIPTIONS.keys())


class UserBehavior(TaskSet):

    companies = []

    def on_start(self):
        pass

    @task(0)
    def home(self):
        logger.info("GET /")
        self.client.get("/")

    @task(1)
    def api_search(self):
        logger.info("URL:API-search")

        commune_id = pick_commune()

        job = pick_job_rome()

        params = {
            'commune_id': commune_id,
            'rome_codes': job,
            'user': u'labonneboite',
        }

        timestamp = util.make_timestamp()
        signature = util.make_signature(params, timestamp, user=params.get('user'))
        params['timestamp'] = timestamp
        params['signature'] = signature

        url = '/api/v1/company/?%s' % urllib.urlencode(params)
        logger.info("GET %s", url)
        self.client.get(url)

    @task(0)
    def frontend_search(self):
        logger.info("URL:entreprises")

        location = pick_location()
        city = location[0]
        zipcode = location[1]

        job = pick_job_name()
        slugified_city = slugify(city.lower())
        slugified_job = slugify(job.lower())
        url = "/entreprises/%s-%s/%s?from=1&to=10" % (slugified_city, zipcode, slugified_job)
        logger.info("GET %s", url)
        self.client.get(url)

    @task(0)
    def suggest_job_labels(self):
        logger.info("URL:suggest_job_labels")

        term = pick_job_name()
        index = random.choice([3, 4, 5, 6])
        if not len(term) > index:
            index = len(term) - 1

        url = "/suggest_job_labels?term=%s" % term[:index]
        logger.info("GET %s", url)
        self.client.get(url)

    @task(0)
    def suggest_cities(self):
        logger.info("URL:suggest_cities")

        city_name, _ = pick_location()
        index = random.choice([3, 4, 5, 6])
        if not len(city_name) > index:
            index = len(city_name) - 1

        url = "/suggest_locations?term=%s" % urllib.quote_plus(city_name)[:index]
        logger.info("GET %s", url)
        self.client.get(url)

    @task(0)
    def download_company(self):
        logger.info("URL:download")
        siret = random.choice(SIRET_CHOICES)
        url = "/%s/download" % siret
        logger.info("GET %s", url)
        self.client.get(url)


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    # Broaden range a little to add some noise in duration between requests
    # while still respecting SECONDS_BETWEEN_TASKS value on average.
    min_wait = int(SECONDS_BETWEEN_TASKS * 1000 * 0.80)
    max_wait = int(SECONDS_BETWEEN_TASKS * 1000 * 1.20)
