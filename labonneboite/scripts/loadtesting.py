# coding: utf8
import random
import os
import csv
import math
from operator import itemgetter
import urllib
import requests

from slugify import slugify
import MySQLdb as mdb
from locust import HttpLocust, TaskSet, task
from locust.exception import StopLocust

from labonneboite.conf import settings
from labonneboite.common import geocoding
import logging


logger = logging.getLogger(__name__)
logger.info("loading locustfile")


def create_cursor():
    con = mdb.connect('localhost', settings.USER, settings.PASSWORD, settings.DB)
    cur = con.cursor()
    return con, cur



con, cur = create_cursor()
cur.execute("select count(1) from %s" % (settings.OFFICE_TABLE))
con.commit()
OFFICE_COUNT = cur.fetchone()[0]


def generate_city_choices():
    fullname = os.path.join(settings.PROJECT_BASE, "labonneboite/common/data/consolidated_cities.csv")
    city_file = open(fullname, "r")
    reader = csv.reader(city_file)
    cities = []
    for city_name, first_zipcode, population, latitude, longitude in reader:
        cities.append([city_name, first_zipcode, int(population)])
    cities_by_population = sorted(cities, key=itemgetter(2), reverse=True)
    city_choices = []
    for city in cities_by_population[:2000]:
        name, zipcode, population = city
        city_choices.append([(name, zipcode), math.log10(population)])
    return city_choices

CITY_CHOICES = generate_city_choices()


# generate companies siret numbers for secretaries in a radius of 50km around Paris
rome = ['M1607',]
naf = []
latitude = 48.8536415100097
longitude = 2.34842991828918
distance = 50
headcount = None
from_number = 1
to_number = 100000


def weighted_choice(choices):
   total = sum(w for c, w in choices)
   r = random.uniform(0, total)
   upto = 0
   for c, w in choices:
      if upto + w >= r:
         return c
      upto += w
   assert False, "Shouldn't get here"


def pick_location():
    city, zipcode = weighted_choice(CITY_CHOICES)
    return city, zipcode


def pick_job():
    return random.choice(settings.ROME_DESCRIPTIONS.values())


class UserBehavior(TaskSet):

    companies = []

    def on_start(self):
        self.home()

    @task(5)
    def stop_session(self):
        logger.info("*** stop locust ***")
        raise StopLocust()

    @task(7)
    def home(self):
        logger.info("GET /")
        self.client.get("/")

    @task(16)
    def search(self):
        logger.info("URL:search")
        location = pick_location()
        city = location[0]
        zipcode = location[1]
        job = pick_job()
        # WTF... job is unicode but city is utf8...
        args = {
            'job': job.encode('utf-8'),
            'city': city,
            'zipcode': zipcode
        }
        param_string = urllib.urlencode(args)
        url = "/recherche?%s" % param_string
        logger.info("GET %s" % url)
        self.client.get(url)

    @task(25)
    def results(self):
        logger.info("URL:entreprises")

        location = pick_location()
        city = location[0]
        zipcode = location[1]

        job = pick_job()
        slugified_city = slugify(city.lower())
        slugified_job = slugify(job.lower())
        url = "/entreprises/%s-%s/%s?from=1&to=10" % (slugified_city, zipcode, slugified_job)
        logger.info("GET %s" % url)
        self.client.get(url)


    @task(32)
    def suggest_job_labels(self):
        logger.info("URL:suggest_job_labels")

        term  = pick_job()
        index = random.choice([3,4,5,6])
        if not len(term) > index:
            index = len(term) - 1

        url = "/suggest_job_labels?term=%s" % term[:index]
        logger.info("GET %s" % url)
        self.client.get(url)

    @task(16)
    def suggest_cities(self):
        logger.info("URL:suggest_cities")

        city_name, zipcode  = pick_location()
        index = random.choice([3,4,5,6])
        if not len(city_name) > index:
            index = len(city_name) - 1

        url = "/suggest_locations?term=%s" % urllib.quote_plus(city_name)[:index]
        logger.info("GET %s" % url)
        self.client.get(url)

    @task(4)
    def download_company(self):
        logger.info("URL:download")
        siret = random.choice(SIRET_NUMBERS)
        url = "/%s/download" % siret
        logger.info("GET %s" % url)
        self.client.get(url)


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait=1000
    max_wait=27000
