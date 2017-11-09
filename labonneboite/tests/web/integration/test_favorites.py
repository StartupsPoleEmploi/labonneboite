# coding: utf8

import time

from labonneboite.common.models import User
from labonneboite.common.models import Office
from labonneboite.common.models import UserFavoriteOffice
from labonneboite.tests.test_base import DatabaseTest


class FavoriteBaseTest(DatabaseTest):
    """
    Create Elasticsearch and DB content for the unit tests.
    """

    positions = {
        'paris': {
            'coords': [{
                'lat': 48.866667,
                'lon': 2.333333,
            }],
            'zip_code': u'75010',
            'commune_id': u'75110',
        },
        'metz': {
            'coords': [{
                'lat': 49.133333,
                'lon': 6.166667,
            }],
            'zip_code': u'57000',
            'commune_id': u'57463',
        },
    }

    def setUp(self, *args, **kwargs):
        super(FavoriteBaseTest, self).setUp(*args, **kwargs)

        # Create a user.
        self.user = User.create(email=u'j@test.com', gender=u'male', first_name=u'John', last_name=u'Doe')

        # Delete index.
        self.es.indices.delete(index=self.ES_TEST_INDEX)

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
        self.es.indices.create(index=self.ES_TEST_INDEX, body=request_body)

        # Insert test data into Elasticsearch.
        docs = [
            {
                'naf': u'4711F',
                'siret': u'00000000000001',
                'score': 98,
                'headcount': 32,
                'locations': self.positions['metz']['coords'],
                'name': u'Centre Distributeur E.Leclerc',
            },
            {
                'naf': u'4722Z',
                'siret': u'00000000000002',
                'score': 98,
                'headcount': 12,
                'locations': self.positions['metz']['coords'],
                'name': u'Maison Nicolas',
            },
            {
                'naf': u'4711F',
                'siret': u'00000000000003',
                'score': 98,
                'headcount': 32,
                'locations': self.positions['paris']['coords'],
                'name': u'Carrefour Paris',
            },
            {
                'naf': u'4722Z',
                'siret': u'00000000000004',
                'score': 98,
                'headcount': 84,
                'locations': self.positions['paris']['coords'],
                'name': u'Maistre Mathieu',
            },
        ]
        for i, doc in enumerate(docs, start=1):
            self.es.index(index=self.ES_TEST_INDEX, doc_type=self.ES_OFFICE_TYPE, id=i, body=doc)

        # Sleep required by ES to register new documents, flaky test here otherwise.
        time.sleep(1)

        # Create related Office instances into MariaDB/MySQL.
        for doc in docs:

            # Set the right `commune_id` and `zipcode` depending on the location.
            commune_id = None
            zip_code = None
            commune_id = None
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


class FavoriteTest(FavoriteBaseTest):
    """
    Test favorites.
    """

    def test_favorites_list(self):
        """
        Test favorites list.
        """
        office = Office.query.filter(Office.siret == u'00000000000004').one()
        url_list = self.url_for('user.favorites_list')

        # An anonymous user cannot access the favorites list.
        rv = self.app.get(url_list)
        self.assertEqual(rv.status_code, 401)

        with self.test_request_context:

            self.login(self.user)

            rv = self.app.get(url_list)
            self.assertEqual(rv.status_code, 200)
            self.assertTrue(u'Aucun favori pour le moment.' in rv.data.decode('utf-8'))

            # Create a favorite for the user.
            UserFavoriteOffice.create(user_id=self.user.id, office_siret=office.siret)

            rv = self.app.get(url_list)
            self.assertEqual(rv.status_code, 200)
            self.assertTrue(office.name in rv.data.decode('utf-8'))
            self.assertTrue(office.city in rv.data.decode('utf-8'))

    def test_favorites_add(self):
        """
        Test the creation of a favorite.
        """
        office = Office.query.filter(Office.siret == u'00000000000002').one()
        url_list = self.url_for('user.favorites_list')
        url_add = self.url_for('user.favorites_add', siret=office.siret)

        # An anonymous user cannot add a favorite.
        rv = self.app.post(url_add)
        self.assertEqual(rv.status_code, 401)

        with self.test_request_context:

            self.login(self.user)

            rv = self.app.post(url_add)
            self.assertEqual(rv.status_code, 302)
            self.assertEqual(rv.location, url_list)  # User should be redirected to the list by default.

            favorites = UserFavoriteOffice.query.filter(UserFavoriteOffice.user_id == self.user.id).all()
            self.assertEqual(1, len(favorites))
            self.assertEqual(office.siret, favorites[0].office_siret)

            rv = self.app.get(url_list)
            self.assertEqual(rv.status_code, 200)
            self.assertTrue(office.name in rv.data.decode('utf-8'))
            self.assertTrue(office.city in rv.data.decode('utf-8'))

            # TODO: understand why using `self.user.favorite_offices` generates this error:
            # DetachedInstanceError: Parent instance <User at 0x7f4cb78e4510> is not bound to a Session;
            # lazy load operation of attribute 'favorite_offices' cannot proceed
            # => fully understand SQLAlchemy sessions and reverse relations.
            # Understand why this is working inside the `with` clause:
            # user = User.query.filter(User.id == self.user.id).one()
            # self.assertEqual(1, len(user.favorite_offices))

    def test_favorites_delete(self):
        """
        Test the deletion of a favorite.
        """
        office = Office.query.filter(Office.siret == u'00000000000003').one()
        url_list = self.url_for('user.favorites_list')
        url_delete = self.url_for('user.favorites_delete', siret=office.siret)

        # An anonymous user cannot delete a favorite.
        rv = self.app.post(url_delete)
        self.assertEqual(rv.status_code, 401)

        with self.test_request_context:

            self.login(self.user)

            # Create a favorite for the user.
            UserFavoriteOffice.create(user_id=self.user.id, office_siret=office.siret)

            rv = self.app.get(url_list)
            self.assertEqual(rv.status_code, 200)
            self.assertTrue(office.name in rv.data.decode('utf-8'))
            self.assertTrue(office.city in rv.data.decode('utf-8'))

            rv = self.app.post(url_delete)
            self.assertEqual(rv.status_code, 302)
            self.assertEqual(rv.location, url_list)  # User should be redirected to the list by default.

            rv = self.app.get(url_list)
            self.assertEqual(rv.status_code, 200)
            self.assertTrue(u'Aucun favori pour le moment.' in rv.data.decode('utf-8'))

    def test_favorites_download(self):
        url_favorites_download = self.url_for('user.favorites_download')
        office = Office.query.filter(Office.siret == u'00000000000001').one()
        UserFavoriteOffice.create(user_id=self.user.id, office_siret=office.siret)

        with self.test_request_context:
            self.login(self.user)
            rv = self.app.get(url_favorites_download)

        self.assertEqual(rv.status_code, 200)
        self.assertEqual('application/pdf', rv.mimetype)
        # Unfortunately, it's difficult to do any more testing on the content of the pdf
        self.assertLess(1000, len(rv.data))
