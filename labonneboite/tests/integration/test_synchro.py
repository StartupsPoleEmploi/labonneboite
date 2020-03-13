import random
import unittest

from labonneboite.common import departements as dpt
from labonneboite.common.es import Elasticsearch
from labonneboite.common.models import Office
from labonneboite.conf import settings


class SynchronizationIndexAndDatabaseTest(unittest.TestCase):
    """
    WARNING: this test class should probably talk to the "real" database, not
    the "test" one.
    """

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
        body = {"query": {"filtered": {"filter": {"terms": {"siret": list(scores.keys())}}}}}
        res = es.search(index=settings.ES_INDEX, doc_type="office", body=body)
        for office in res["hits"]["hits"]:
            index_score = office["_source"]["score"]
            siret = office["_source"]["siret"]
            self.assertEqual(index_score, scores[siret])
