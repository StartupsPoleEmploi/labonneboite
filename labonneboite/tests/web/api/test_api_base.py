# coding: utf8

import time

from labonneboite.common.models import Office
from labonneboite.tests.test_base import DatabaseTest
from labonneboite.web.api import util
from labonneboite.conf import settings
from labonneboite.common import mapping as mapping_util
from labonneboite.common import scoring as scoring_util
from labonneboite.scripts.create_index import mapping_office


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
        'metz': {
            'coords': [{
                'lat': 49.133333,
                'lon': 6.166667,
            }],
            'zip_code': u'57050',
            'commune_id': u'57463',
        },
        'nantes': {
            'coords': [{
                'lat': 47.217222,
                'lon': -1.553889,
            }],
            'zip_code': u'44000',
            'commune_id': u'44109',
        },
        # City close to Nantes
        'reze': {
            'coords': [{
                'lat': 47.2,
                'lon': -1.566667,
            }],
            'zip_code': u'44400',
            'commune_id': u'44143',
        },
        'lille': {
            'coords': [{
                'lat': 50.633333,
                'lon': 3.066667,
            }],
            'zip_code': u'59800',
            'commune_id': u'59350',
        },
        'toulouse': {
            'coords': [{
                'lat': 43.600000,
                'lon': 1.433333,
            }],
            'zip_code': u'31500',
            'commune_id': u'31555',
        },
        'pau': {
            'coords': [{
                'lat': 43.300000,
                'lon': -0.366667,
            }],
            'zip_code': u'64000',
            'commune_id': u'64445',
        },
        'poitiers': {
            'coords': [{
                'lat': 46.5833,
                'lon': 0.3333,
            }],
            'zip_code': u'86000',
            'commune_id': u'86194',
        },
        'paris': {
            'coords': [{
                'lat': 48.87950,
                'lon': 2.283439,
            }],
            'zip_code': u'75004',
            'commune_id': u'75056',
        },
        'neuilly-sur-seine': {
            'coords': [{
                'lat': 48.884831,
                'lon': 2.26851,
            }],
            'zip_code': u'92200',
            'commune_id': u'92051',
        },
    }

    def setUp(self, *args, **kwargs):
        super(ApiBaseTest, self).setUp(*args, **kwargs)

        settings.ES_INDEX = self.ES_TEST_INDEX  # Override the setting value.

        # Delete index.
        self.es.indices.delete(index=self.ES_TEST_INDEX, params={'ignore': [404]})

        # Create new index.
        request_body = {
            "mappings": {
                "office": mapping_office
            }
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
                'flag_alternance': 0,
                'department': self.positions['bayonville_sur_mad']['zip_code'][0:2],
            },
            {
                'naf': u'7320Z',  # Map to ROME D1405.
                'siret': u'00000000000002',
                'score': 69,
                'headcount': 31,
                'locations': self.positions['bayonville_sur_mad']['coords'],
                'name': u'Office 2',
                'flag_alternance': 0,
                'department': self.positions['bayonville_sur_mad']['zip_code'][0:2],
            },
            {
                'naf': u'7320Z',  # Map to ROME D1405.
                'siret': u'00000000000003',
                'score': 70,
                'headcount': 31,
                'locations': self.positions['bayonville_sur_mad']['coords'],
                'name': u'Office 3',
                'flag_alternance': 0,
                'department': self.positions['bayonville_sur_mad']['zip_code'][0:2],
            },
            {
                'naf': u'7320Z',  # Map to ROME D1405.
                'siret': u'00000000000004',
                'score': 71,
                'headcount': 31,
                'locations': self.positions['caen']['coords'],
                'name': u'Office 4',
                'flag_alternance': 0,
                'department': self.positions['caen']['zip_code'][0:2],
            },
            {
                'naf': u'9511Z',  # Map to ROME M1801.
                'siret': u'00000000000005',
                'score': 71,
                'headcount': 31,
                'locations': self.positions['caen']['coords'],
                'name': u'Office 5',
                'flag_alternance': 0,
                'department': self.positions['caen']['zip_code'][0:2],
            },
            # For NAF filter
            {
                'naf': u'4711C',  # Map to ROME D1508.
                'siret': u'00000000000006',
                'score': 75,
                'headcount': 31,
                'locations': self.positions['metz']['coords'],
                'name': u'Office 6',
                'flag_alternance': 0,
                'department': self.positions['metz']['zip_code'][0:2],
            },
            {
                'naf': u'5610C',  # Map to ROME D1508.
                'siret': u'00000000000007',
                'score': 70,
                'headcount': 50,
                'locations': self.positions['metz']['coords'],
                'name': u'Office 7',
                'flag_alternance': 0,
                'department': self.positions['metz']['zip_code'][0:2],
            },
            # For result sort
            {
                'naf': u'9103Z', # Map to ROME D1211
                'siret': u'00000000000008',
                'score': 75,
                'headcount': 50,
                'locations': self.positions['nantes']['coords'],
                'name': u'Office 8',
                'flag_alternance': 0,
                'department': self.positions['nantes']['zip_code'][0:2],
            },
            {
                'naf': u'7010Z', # Map to ROME D1211
                'siret': u'00000000000009',
                'score': 99,
                'headcount': 50,
                'locations': self.positions['reze']['coords'], # City close to Nantes
                'name': u'Office 9',
                'flag_alternance': 0,
                'department': self.positions['reze']['zip_code'][0:2],
            },
            # For contract filter
            {
                'naf': u'4669A', # Map to Rome D1213
                'siret': u'00000000000010',
                'score': 78,
                'headcount': 34,
                'locations': self.positions['lille']['coords'],
                'name': u'Office 10',
                'flag_alternance': 0,
                'department': self.positions['lille']['zip_code'][0:2],
            },
            {
                'naf': u'4669A', # Map to Rome D1213
                'siret': u'00000000000011',
                'score': 82,
                'headcount': 65,
                'locations': self.positions['lille']['coords'],
                'name': u'Office 11',
                'flag_alternance': 1,
                'department': self.positions['lille']['zip_code'][0:2],
            },
            # For headcount filter
            {
                'naf': u'7022Z', # Map to Rome M1202
                'siret': u'00000000000012',
                'score': 82,
                'headcount': 11,
                'locations': self.positions['toulouse']['coords'],
                'name': u'Office 12',
                'flag_alternance': 0,
                'department': self.positions['toulouse']['zip_code'][0:2],
            },
            {
                'naf': u'7010Z',  # Map to Rome M1202
                'siret': u'00000000000013',
                'score': 82,
                'headcount': 22,
                'locations': self.positions['toulouse']['coords'],
                'name': u'Office 13',
                'flag_alternance': 0,
                'department': self.positions['toulouse']['zip_code'][0:2],
            },
            # For headcount_text
            {
                'naf': u'4648Z',  # Map to Rome B1603
                'siret': u'00000000000014',
                'score': 80,
                'headcount': 53, # headcount_text : '10 000 salariés et plus'
                'locations': self.positions['pau']['coords'],
                'name': u'Office 14',
                'flag_alternance': 0,
                'department': self.positions['pau']['zip_code'][0:2],
            },
            # For flag_alternance in response
            {
                'naf': u'4648Z',  # Map to Rome B1603
                'siret': u'00000000000015',
                'score': 80,
                'headcount': 53,
                'locations': self.positions['poitiers']['coords'],
                'name': u'Office 15',
                'flag_alternance': 0,
                'department': self.positions['poitiers']['zip_code'][0:2],
            },
            {
                'naf': u'4648Z',  # Map to Rome B1603
                'siret': u'00000000000016',
                'score': 70,
                'headcount': 53,
                'locations': self.positions['poitiers']['coords'],
                'name': u'Office 16',
                'flag_alternance': 1,
                'department': self.positions['poitiers']['zip_code'][0:2],
            },
            # For filter_by_department
            {
                'naf': u'5229A',  # Map to Rome N1202
                'siret': u'00000000000017',
                'score': 90,
                'headcount': 53,
                'locations': self.positions['paris']['coords'],
                'name': u'Office 17',
                'flag_alternance': 0,
                'department': self.positions['paris']['zip_code'][0:2],
            },
            {
                'naf': u'5229A',  # Map to Rome N1202
                'siret': u'00000000000018',
                'score': 78,
                'headcount': 53,
                'locations': self.positions['neuilly-sur-seine']['coords'],
                'name': u'Office 18',
                'flag_alternance': 0,
                'department': self.positions['neuilly-sur-seine']['zip_code'][0:2],
            }
        ]
        for i, doc in enumerate(docs, start=1):
            # Build scores for relevant ROME codes.
            naf = doc['naf']
            score = doc['score']
            rome_codes = mapping_util.MANUAL_NAF_ROME_MAPPING[naf].keys()

            scores_by_rome = {}
            for rome_code in rome_codes:
                scores_by_rome[rome_code] = scoring_util.get_score_adjusted_to_rome_code_and_naf_code(
                    score=score,
                    rome_code=rome_code,
                    naf_code=naf
                )
            if scores_by_rome:
                doc['scores_by_rome'] = scores_by_rome

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
                flag_alternance=doc['flag_alternance'],
                headcount=doc['headcount'],
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
