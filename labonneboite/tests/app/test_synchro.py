# coding: utf8

import random
import unittest

from sqlalchemy import create_engine

from labonneboite.common.es import Elasticsearch
from labonneboite.common.database import db_session, get_db_string
from labonneboite.common.database import ENGINE_PARAMS, REAL_DATABASE
from labonneboite.common.models import Office
from labonneboite.common import departements as dpt
from labonneboite.conf import settings


class SynchronizationIndexAndDatabaseTest(unittest.TestCase):
    """
    WARNING: this test class talks to the "real" database, not the "test" one.

    Tests that require a database will usually not use the "real" database.
    Separate, blank databases are usually created for the tests.

    However, this test is written so that it requires to talk to the "real" database.
    Plus this test seems to @vermeer to be vital:
    http://git.beta.pole-emploi.fr/labonneboite/labonneboite/merge_requests/54#note_1186

    That's why we override the `db_session`'s binding in this test.

    Note: the "real" database could be either the dev database or the staging database,
    depending on the value of `REAL_DATABASE`, see `labonneboite.common.database.py`
    for how its value is defined.
    """

    def setUp(self):
        # Cache the previous engine used by `db_session`.
        self.cached_engine = db_session.bind
        # Make `db_session` use the "real" database, not the "test" one.
        real_engine = create_engine(get_db_string(db_params=REAL_DATABASE), **ENGINE_PARAMS)
        db_session.bind = real_engine
        return super(SynchronizationIndexAndDatabaseTest, self).setUp()

    def tearDown(self):
        # Restore the cached engine.
        db_session.bind = self.cached_engine
        return super(SynchronizationIndexAndDatabaseTest, self).tearDown()

    def test_synchro(self):
        """
        Test that the data is synchronized between the SQL database and Elasticsearch.
        """
        random.seed(99)  # use a seed to get deterministic random numbers
        departement = random.choice(dpt.DEPARTEMENTS)
        offices = Office.query.filter(Office.departement == departement).limit(100)

        # If we got no results here, assume that tests are running locally,
        # i.e. on a dev machine which currently only have data for "Metz".
        # TODO: clearly identify which Elasticsearch we are talking to.
        if offices.count() == 0:
            offices = Office.query.filter(Office.departement == 57).limit(100)

        self.assertTrue(offices.count() > 0)

        es = Elasticsearch()
        scores = {office.siret: office.score for office in offices}
        body = {"query": {"filtered": {"filter": {"terms": {"siret": scores.keys()}}}}}
        res = es.search(index=settings.ES_INDEX, doc_type="office", body=body)
        for office in res['hits']['hits']:
            index_score = office["_source"]["score"]
            siret = office["_source"]["siret"]
            self.assertEquals(index_score, scores[siret])
