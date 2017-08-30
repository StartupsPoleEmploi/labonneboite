# coding: utf8

import time

from labonneboite.common.models import Office
from labonneboite.tests.test_base import DatabaseTest
from labonneboite.conf import settings
from labonneboite.web.api import util
from labonneboite.common import mapping as mapping_util
from labonneboite.common import scoring as scoring_util


class ApiBaseTest(DatabaseTest):

    positions = {
        'bayonville_sur_mad': {
            'coords': [{
                'lat': 49,
                'lon': 6,
            }],
            'zip_code': u'54890',
            'commune_id': u'54055',
        },
        'caen': {
            'coords': [{
                'lat': 49.1812497463,
                'lon': -0.372499354315,
            }],
            'zip_code': u'14000',
            'commune_id': u'14118',
        },
    }

    def setUp(self, *args, **kwargs):
        super(ApiBaseTest, self).setUp(*args, **kwargs)

        # Delete index.
        self.es.indices.delete(index=self.ES_TEST_INDEX, ignore=[404])

        # Create new index.
        request_body = {
            "mappings": {
                "office": {
                    "properties": {
                        "naf": {
                            "type": "string",
                            "index": "not_analyzed"
                        },
                        "siret": {
                            "type": "string",
                            "index": "not_analyzed"
                        },
                        "name": {
                            "type": "string",
                            "index": "not_analyzed"
                        },
                        "score": {
                            "type": "integer",
                            "index": "not_analyzed"
                        },
                        "headcount": {
                            "type": "integer",
                            "index": "not_analyzed"
                        },
                        "locations": {
                            "type": "geo_point",
                        }
                    }
                }
            }
        }

        for rome_code in settings.ROME_DESCRIPTIONS.keys():
            request_body["mappings"]["office"]["properties"]["score_for_rome_%s" % rome_code] = {
                "type": "integer",
                "index": "not_analyzed"
            }
        self.es.indices.create(index=self.ES_TEST_INDEX, body=request_body)

        # Insert test data into Elasticsearch.
        docs = [
            {
                'naf': u'7320Z',  # Map to ROME D1405.
                'siret': u'00000000000001',
                'score': 68,
                'headcount': 11,
                'locations': self.positions['bayonville_sur_mad']['coords'],
                'name': u'Office 1',
            },
            {
                'naf': u'7320Z',  # Map to ROME D1405.
                'siret': u'00000000000002',
                'score': 69,
                'headcount': 31,
                'locations': self.positions['bayonville_sur_mad']['coords'],
                'name': u'Office 2',
            },
            {
                'naf': u'7320Z',  # Map to ROME D1405.
                'siret': u'00000000000003',
                'score': 70,
                'headcount': 31,
                'locations': self.positions['bayonville_sur_mad']['coords'],
                'name': u'Office 3',
            },
            {
                'naf': u'7320Z',  # Map to ROME D1405.
                'siret': u'00000000000004',
                'score': 71,
                'headcount': 31,
                'locations': self.positions['caen']['coords'],
                'name': u'Office 4',
            },
            {
                'naf': u'9511Z',  # Map to ROME M1801.
                'siret': u'00000000000005',
                'score': 71,
                'headcount': 31,
                'locations': self.positions['caen']['coords'],
                'name': u'Office 5',
            },
        ]
        for i, doc in enumerate(docs, start=1):
            # build scores for relevant ROME codes
            naf = doc['naf']
            score = doc['score']
            rome_codes = mapping_util.MANUAL_NAF_ROME_MAPPING[naf].keys()

            for rome_code in rome_codes:
                office_score_for_current_rome = scoring_util.get_score_adjusted_to_rome_code_and_naf_code(
                    score=score,
                    rome_code=rome_code,
                    naf_code=naf
                )
                doc['score_for_rome_%s' % rome_code] = office_score_for_current_rome

            self.es.index(index=self.ES_TEST_INDEX, doc_type=self.ES_OFFICE_TYPE, id=i, body=doc)

        # need for ES to register our new documents, flaky test here otherwise
        time.sleep(1)

        # Create related Office instances into MariaDB/MySQL.
        for doc in docs:

            # Set the right `commune_id` and `zipcode` depending on the location.
            commune_id = None
            zip_code = None
            for position in self.positions:
                if doc['locations'] == self.positions[position]['coords']:
                    commune_id = self.positions[position]['commune_id']
                    zip_code = self.positions[position]['zip_code']
                    break

            if not commune_id:
                raise ValueError("Cannot create an entry in Office with a city absent from self.positions.")

            office = Office(
                company_name=doc['name'],
                siret=doc['siret'],
                score=doc['score'],
                naf=doc['naf'],
                city_code=commune_id,
                zipcode=zip_code,
                email=u'foo@bar.com',
                departement=zip_code[:2],
                x=doc['locations'][0]['lon'],
                y=doc['locations'][0]['lat'],
            )
            office.save()

        # We should have as much entries in MariaDB/MySQL than in Elasticsearch.
        self.assertEquals(Office.query.count(), len(docs))

    def add_security_params(self, params):
        """
        Utility method that add `timestamp` and `signature` keys to params.
        """
        timestamp = util.make_timestamp()
        signature = util.make_signature(params, timestamp, user=params.get('user'))
        params['timestamp'] = timestamp
        params['signature'] = signature
        return params
