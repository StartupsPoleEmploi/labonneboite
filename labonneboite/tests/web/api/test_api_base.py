import copy
import json
import os
from operator import itemgetter

from flask.wrappers import Response

from labonneboite.common import es
from labonneboite.common import mapping as mapping_util
from labonneboite.common import scoring as scoring_util
from labonneboite.common.models import Office
from labonneboite.conf import settings
from labonneboite.tests.test_base import DatabaseTest
from labonneboite.web.api import util

POSITIONS = {
    'bayonville_sur_mad': {
        'coords': [{
            'lat': 49,
            'lon': 6,
        }],
        'zip_code': '54890',
        'commune_id': '54055',
    },
    'caen': {
        'coords': [{
            'lat': 49.1812497463,
            'lon': -0.372499354315,
        }],
        'zip_code': '14000',
        'commune_id': '14118',
    },
    'metz': {
        'coords': [{
            'lat': 49.133333,
            'lon': 6.166667,
        }],
        'zip_code': '57050',
        'commune_id': '57463',
    },
    'nantes': {
        'coords': [{
            'lat': 47.217222,
            'lon': -1.553889,
        }],
        'zip_code': '44000',
        'commune_id': '44109',
    },
    # City close to Nantes
    'reze': {
        'coords': [{
            'lat': 47.2,
            'lon': -1.566667,
        }],
        'zip_code': '44400',
        'commune_id': '44143',
    },
    'lille': {
        'coords': [{
            'lat': 50.633333,
            'lon': 3.066667,
        }],
        'zip_code': '59800',
        'commune_id': '59350',
    },
    'toulouse': {
        'coords': [{
            'lat': 43.600000,
            'lon': 1.433333,
        }],
        'zip_code': '31500',
        'commune_id': '31555',
    },
    'pau': {
        'coords': [{
            'lat': 43.300000,
            'lon': -0.366667,
        }],
        'zip_code': '64000',
        'commune_id': '64445',
    },
    'poitiers': {
        'coords': [{
            'lat': 46.5833,
            'lon': 0.3333,
        }],
        'zip_code': '86000',
        'commune_id': '86194',
    },
    'paris': {
        'coords': [{
            'lat': 48.87950,
            'lon': 2.283439,
        }],
        'zip_code': '75004',
        'commune_id': '75056',
    },
    'neuilly-sur-seine': {
        'coords': [{
            'lat': 48.884831,
            'lon': 2.26851,
        }],
        'zip_code': '92200',
        'commune_id': '92051',
    },
    # For filters in response tests
    'toulon': {
        'coords': [{
            'lat': 43.1167,
            'lon': 5.9333,
        }],
        'zip_code': '83000',
        'commune_id': '83137',
    },
    # Located at 15km of Toulon
    'hyeres': {
        'coords': [{
            'lat': 43.1167,
            'lon': 6.1167,
        }],
        'zip_code': '83400',
        'commune_id': '83069',
    },
    # Located at 35km of Toulon
    'aubagne': {
        'coords': [{
            'lat': 43.283329,
            'lon': 5.56667,
        }],
        'zip_code': '13400',
        'commune_id': '13005',
    },
    # Located at 60km of Toulon
    'draguignan': {
        'coords': [{
            'lat': 43.53772,
            'lon': 6.464993,
        }],
        'zip_code': '83300',
        'commune_id': '83050',
    },
    # Located at 500km of Toulon
    'limoges': {
        'coords': [{
            'lat': 45.849998,
            'lon': 1.25,
        }],
        'zip_code': '87000',
        'commune_id': '87085',
    },
}

DOCS = [
    {
        'naf': '4646Z',  # Map to ROME D1405.
        'siret': '00000000000001',
        'company_name': 'Raison sociale 1',
        'score': 68,
        'score_alternance': 18,
        'headcount': 11,
        'locations': POSITIONS['bayonville_sur_mad']['coords'],
        'name': 'Office 1',
        'flag_alternance': 0,
        'flag_pmsmp': 0,
        'department': POSITIONS['bayonville_sur_mad']['zip_code'][0:2],
    },
    {
        'naf': '4646Z',  # Map to ROME D1405.
        'siret': '00000000000002',
        'company_name': 'Raison sociale 2',
        'score': 69,
        'score_alternance': 18,
        'headcount': 31,
        'locations': POSITIONS['bayonville_sur_mad']['coords'],
        'name': 'Office 2',
        'flag_alternance': 0,
        'flag_pmsmp': 0,
        'department': POSITIONS['bayonville_sur_mad']['zip_code'][0:2],
    },
    {
        'naf': '4646Z',  # Map to ROME D1405.
        'siret': '00000000000003',
        'score': 70,
        'score_alternance': 18,
        'headcount': 31,
        'locations': POSITIONS['bayonville_sur_mad']['coords'],
        'name': 'Office 3',
        'flag_alternance': 0,
        'flag_pmsmp': 0,
        'department': POSITIONS['bayonville_sur_mad']['zip_code'][0:2],
    },
    {
        'naf': '4646Z',  # Map to ROME D1405.
        'siret': '00000000000004',
        'score': 71,
        'score_alternance': 18,
        'headcount': 31,
        'locations': POSITIONS['caen']['coords'],
        'name': 'Office 4',
        'flag_alternance': 0,
        'flag_pmsmp': 0,
        'department': POSITIONS['caen']['zip_code'][0:2],
    },
    {
        'naf': '9511Z',  # Map to ROME M1801.
        'siret': '00000000000005',
        'score': 71,
        'score_alternance': 18,
        'headcount': 31,
        'locations': POSITIONS['caen']['coords'],
        'name': 'Office 5',
        'flag_alternance': 0,
        'flag_pmsmp': 0,
        'department': POSITIONS['caen']['zip_code'][0:2],
    },
    # For NAF filter
    {
        'naf': '4771Z',  # Map to ROME D1508.
        'siret': '00000000000006',
        'score': 75,
        'score_alternance': 18,
        'headcount': 31,
        'locations': POSITIONS['metz']['coords'],
        'name': 'Office 6',
        'flag_alternance': 0,
        'flag_pmsmp': 0,
        'department': POSITIONS['metz']['zip_code'][0:2],
    },
    {
        'naf': '4711F',  # Map to ROME D1508.
        'siret': '00000000000007',
        'score': 70,
        'score_alternance': 18,
        'headcount': 50,
        'locations': POSITIONS['metz']['coords'],
        'name': 'Office 7',
        'flag_alternance': 0,
        'flag_pmsmp': 0,
        'department': POSITIONS['metz']['zip_code'][0:2],
    },
    # For result sort
    {
        'naf': '9529Z',  # Map to ROME D1211
        'siret': '00000000000008',
        'score': 75,
        'score_alternance': 51,
        'headcount': 50,
        'locations': POSITIONS['nantes']['coords'],
        'name': 'Office 8',
        'flag_alternance': 0,
        'flag_pmsmp': 0,
        'department': POSITIONS['nantes']['zip_code'][0:2],
    },
    {
        'naf': '4741Z',  # Map to ROME D1211
        'siret': '00000000000009',
        'score': 99,
        'score_alternance': 51,
        'headcount': 50,
        'locations': POSITIONS['reze']['coords'],  # City close to Nantes
        'name': 'Office 9',
        'flag_alternance': 0,
        'flag_pmsmp': 0,
        'department': POSITIONS['reze']['zip_code'][0:2],
    },
    # For contract filter
    {
        'naf': '4752B',  # Map to Rome D1213
        'siret': '00000000000010',
        'score': 78,
        'score_alternance': 0,
        'headcount': 34,
        'locations': POSITIONS['lille']['coords'],
        'name': 'Office 10',
        'flag_alternance': 0,
        'flag_pmsmp': 0,
        'department': POSITIONS['lille']['zip_code'][0:2],
    },
    {
        'naf': '4752B',  # Map to Rome D1213
        'siret': '00000000000011',
        'score': 82,
        'score_alternance': 80,
        'headcount': 65,
        'locations': POSITIONS['lille']['coords'],
        'name': 'Office 11',
        'flag_alternance': 1,
        'flag_pmsmp': 0,
        'department': POSITIONS['lille']['zip_code'][0:2],
    },
    # For headcount filter
    {
        'naf': '7022Z',  # Map to Rome M1202
        'siret': '00000000000012',
        'score': 82,
        'score_alternance': 18,
        'headcount': 11,
        'locations': POSITIONS['toulouse']['coords'],
        'name': 'Office 12',
        'flag_alternance': 0,
        'flag_pmsmp': 0,
        'department': POSITIONS['toulouse']['zip_code'][0:2],
    },
    {
        'naf': '7022Z',  # Map to Rome M1202
        'siret': '00000000000013',
        'score': 82,
        'score_alternance': 18,
        'headcount': 22,
        'locations': POSITIONS['toulouse']['coords'],
        'name': 'Office 13',
        'flag_alternance': 0,
        'flag_pmsmp': 0,
        'department': POSITIONS['toulouse']['zip_code'][0:2],
    },
    # For headcount_text
    {
        'naf': '3212Z',  # Map to Rome B1603
        'siret': '00000000000014',
        'score': 80,
        'score_alternance': 18,
        'headcount': 53,  # headcount_text : '10 000 salariés et plus'
        'locations': POSITIONS['pau']['coords'],
        'name': 'Office 14',
        'flag_alternance': 0,
        'flag_pmsmp': 0,
        'department': POSITIONS['pau']['zip_code'][0:2],
    },
    # For flag_alternance in response
    {
        'naf': '3212Z',  # Map to Rome B1603
        'siret': '00000000000015',
        'score': 80,
        'score_alternance': 18,
        'headcount': 53,
        'locations': POSITIONS['poitiers']['coords'],
        'name': 'Office 15',
        'flag_alternance': 0,
        'flag_pmsmp': 0,
        'department': POSITIONS['poitiers']['zip_code'][0:2],
    },
    {
        'naf': '3212Z',  # Map to Rome B1603
        'siret': '00000000000016',
        'score': 70,
        'score_alternance': 80,
        'headcount': 53,
        'locations': POSITIONS['poitiers']['coords'],
        'name': 'Office 16',
        'flag_alternance': 1,
        'flag_pmsmp': 0,
        'department': POSITIONS['poitiers']['zip_code'][0:2],
    },
    # For filter_by_department and filter_by_flag_pmsmp
    {
        'naf': '5229A',  # Map to Rome N1202
        'siret': '00000000000017',
        'score': 90,
        'score_alternance': 18,
        'headcount': 53,
        'locations': POSITIONS['paris']['coords'],
        'name': 'Office 17',
        'flag_alternance': 0,
        'flag_pmsmp': 1,
        'department': POSITIONS['paris']['zip_code'][0:2],
    },
    {
        'naf': '5229A',  # Map to Rome N1202
        'siret': '00000000000018',
        'score': 78,
        'score_alternance': 18,
        'headcount': 53,
        'locations': POSITIONS['neuilly-sur-seine']['coords'],
        'name': 'Office 18',
        'flag_alternance': 0,
        'flag_pmsmp': 0,
        'department': POSITIONS['neuilly-sur-seine']['zip_code'][0:2],
    },
    # For filters in response tests
    {
        'naf': '4910Z',  # Map to Rome N4403
        'siret': '00000000000019',
        'score': 76,
        'score_alternance': 18,
        'headcount': 1,
        'locations': POSITIONS['toulon']['coords'],
        'name': 'Office 19',
        'flag_alternance': 0,
        'flag_pmsmp': 0,
        'department': POSITIONS['toulon']['zip_code'][0:2],
    },
    {
        'naf': '4910Z',  # Map to Rome N4403
        'siret': '00000000000020',
        'score': 90,
        'score_alternance': 18,
        'headcount': 3,
        'locations': POSITIONS['toulon']['coords'],
        'name': 'Office 20',
        'flag_alternance': 0,
        'flag_pmsmp': 0,
        'department': POSITIONS['toulon']['zip_code'][0:2],
    },
    {
        'naf': '4920Z',  # Map to Rome N4403
        'siret': '00000000000021',
        'score': 43,
        'score_alternance': 18,
        'headcount': 53,
        'locations': POSITIONS['toulon']['coords'],
        'name': 'Office 21',
        'flag_alternance': 1,
        'flag_pmsmp': 0,
        'department': POSITIONS['toulon']['zip_code'][0:2],
    },
    # For distance filter => between 10-30km
    {
        'naf': '4910Z',  # Map to Rome N4403
        'siret': '00000000000023',
        'score': 89,
        'score_alternance': 18,
        'headcount': 31,
        'locations': POSITIONS['hyeres']['coords'],  # 15km of Toulon
        'name': 'Office 23',
        'flag_alternance': 0,
        'flag_pmsmp': 0,
        'department': POSITIONS['hyeres']['zip_code'][0:2],
    },
    # For distance filter => between 30-50km
    {
        'naf': '4910Z',  # Map to Rome N4403
        'siret': '00000000000024',
        'score': 30,
        'score_alternance': 18,
        'headcount': 12,
        'locations': POSITIONS['aubagne']['coords'],  # 35km of Toulon
        'name': 'Office 24',
        'flag_alternance': 0,
        'flag_pmsmp': 0,
        'department': POSITIONS['aubagne']['zip_code'][0:2],
    },
    # For distance between 50-100km
    {
        'naf': '4910Z',  # Map to Rome N4403
        'siret': '00000000000025',
        'score': 82,
        'score_alternance': 18,
        'headcount': 11,
        'locations': POSITIONS['draguignan']['coords'],  # 60km of Toulon
        'name': 'Office 25',
        'flag_alternance': 0,
        'flag_pmsmp': 0,
        'department': POSITIONS['draguignan']['zip_code'][0:2],
    },
    # For distance filter => between 100-3000km
    {
        'naf': '4910Z',  # Map to Rome N4403
        'siret': '00000000000026',
        'score': 67,
        'score_alternance': 18,
        'headcount': 51,
        'locations': POSITIONS['limoges']['coords'],  # 500km of Toulon
        'name': 'Office 26',
        'flag_alternance': 0,
        'flag_pmsmp': 0,
        'department': POSITIONS['limoges']['zip_code'][0:2],
    },
    # For boost scores tests
    {
        'naf': '4646Z',  # Map to Rome D1405
        'siret': '00000000000027',
        'score': 43,
        'score_alternance': 18,
        'headcount': 53,
        'locations': POSITIONS['toulon']['coords'],
        'name': 'Office 27',
        'flag_alternance': 1,
        'flag_pmsmp': 0,
        'boosted_alternance_romes': None,
        'boosted_romes': {
            'A1503': True,
            'J1301': True,
            'K1304': True,
            'K1303': True,
            'A1408': True,
            'K1302': True,
            'M1607': True
        },
        'scores_by_rome': {
            'M1607': 45,
            'G1203': 52,
            'M1203': 20,
            'K1207': 60,
            'K1302': 50,
            'K1303': 51
        },
        'scores_alternance_by_rome': None,
        'department': POSITIONS['toulon']['zip_code'][0:2],
    },
    # To valid hidden scores
    {
        'naf': '4910Z',  # Map to Rome N4403
        'siret': '00000000000028',
        'score': 0,
        'score_alternance': 0,
        'headcount': 1,
        'locations': POSITIONS['toulon']['coords'],
        'name': 'Office 28',
        'flag_alternance': 0,
        'flag_pmsmp': 0,
        'department': POSITIONS['toulon']['zip_code'][0:2],
    },
]


class ApiBaseTest(DatabaseTest):

    positions = copy.deepcopy(POSITIONS)

    def get_docs(self):
        docs = copy.deepcopy(DOCS)
        for _, doc in enumerate(docs, start=1):
            # Build scores for relevant ROME codes.
            naf = doc['naf']
            rome_codes = list(mapping_util.MANUAL_NAF_ROME_MAPPING[naf].keys())

            # FIXME this is some dangerous code duplication with create_index, we should someday
            # make it more DNRY.
            score = doc['score']
            scores_by_rome = {}
            for rome_code in rome_codes:
                scores_by_rome[rome_code] = scoring_util.get_score_adjusted_to_rome_code_and_naf_code(
                    score=score,
                    rome_code=rome_code,
                    naf_code=naf,
                )
            if scores_by_rome:
                doc['scores_by_rome'] = scores_by_rome

            # FIXME this is some dangerous code duplication with create_index, we should someday
            # make it more DNRY.
            score_alternance = doc['score_alternance']
            scores_alternance_by_rome = {}
            for rome_code in rome_codes:
                raw_score = scoring_util.get_score_adjusted_to_rome_code_and_naf_code(
                    score=score_alternance,
                    rome_code=rome_code,
                    naf_code=naf,
                )
                if raw_score > 0:  # dirty fix until proper DNRY with create_index
                    scores_alternance_by_rome[rome_code] = raw_score
            if scores_alternance_by_rome:
                doc['scores_alternance_by_rome'] = scores_alternance_by_rome
        return docs

    def setUp(self, *args, **kwargs):
        super(ApiBaseTest, self).setUp(*args, **kwargs)

        self.docs = self.get_docs()

        # Insert test data into Elasticsearch.
        for _, doc in enumerate(self.docs, start=1):

            # just like in other environments, id should be the siret
            self.es.index(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=doc['siret'], body=doc)

        # need for ES to register our new documents, flaky test here otherwise
        self.es.indices.flush(index=settings.ES_INDEX)

        # Create related Office instances into MariaDB/MySQL.
        for doc in self.docs:

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
                office_name=doc['name'],
                siret=doc['siret'],
                score=doc['score'],
                score_alternance=doc['score_alternance'],
                naf=doc['naf'],
                city_code=commune_id,
                zipcode=zip_code,
                email='foo@bar.com',
                departement=zip_code[:2],
                company_name=doc['company_name'] if 'company_name' in doc else '',
                flag_alternance=doc['flag_alternance'],
                flag_pmsmp=doc['flag_pmsmp'],
                headcount=doc['headcount'],
                x=doc['locations'][0]['lon'],
                y=doc['locations'][0]['lat'],
            )
            office.save()

        # We should have as much entries in MariaDB/MySQL than in Elasticsearch, except
        # one more in ES for the fake document actually.
        es_count = self.es.count(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, body={'query': {'match_all': {}}})
        self.assertEqual(Office.query.count() + 1, es_count['count'])

    def tearDown(self):
        # Insert test data into Elasticsearch.
        for _, doc in enumerate(self.docs, start=1):
            # just like in other environments, id should be the siret
            self.es.delete(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=doc['siret'])
        sirets = list(map(itemgetter('siret'), self.docs))
        offices = Office.query.filter(Office.siret in sirets).delete()
        super().tearDown()

    def add_security_params(self, params):
        """
        Utility method that add `timestamp` and `signature` keys to params.
        """
        timestamp = util.make_timestamp()
        signature = util.make_signature(params, timestamp, user=params.get('user'))
        params['timestamp'] = timestamp
        params['signature'] = signature
        return params

    def get_fixture(self, fixture):
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', fixture)
        return json.load(open(fixture_path))

    def get_json(self, response: Response) -> dict:
        self.assertEqual(response.content_type, 'application/json')
        data: bytes = response.data
        text: str = data.decode(response.content_encoding or 'utf-8')
        json_response = json.loads(text)
        return json_response
