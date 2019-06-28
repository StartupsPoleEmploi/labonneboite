
from labonneboite.common.models import User
from labonneboite.common.models import Office
from labonneboite.common.models import UserFavoriteOffice
from labonneboite.common import es
from labonneboite.conf import settings
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
            'zip_code': '75010',
            'commune_id': '75110',
        },
        'metz': {
            'coords': [{
                'lat': 49.133333,
                'lon': 6.166667,
            }],
            'zip_code': '57000',
            'commune_id': '57463',
        },
    }

    def setUp(self):
        super(FavoriteBaseTest, self).setUp()

        # Create a user.
        self.user = User.create(email='j@test.com', gender='male', first_name='John', last_name='Doe')

        # Insert test data into Elasticsearch.
        docs = [
            {
                'naf': '4711F',
                'siret': '00000000000001',
                'score': 98,
                'headcount': 32,
                'locations': self.positions['metz']['coords'],
                'name': 'Centre Distributeur E.Leclerc',
            },
            {
                'naf': '4722Z',
                'siret': '00000000000002',
                'score': 98,
                'headcount': 12,
                'locations': self.positions['metz']['coords'],
                'name': 'Maison Nicolas',
            },
            {
                'naf': '4711F',
                'siret': '00000000000003',
                'score': 98,
                'headcount': 32,
                'locations': self.positions['paris']['coords'],
                'name': 'Carrefour Paris',
            },
            {
                'naf': '4722Z',
                'siret': '00000000000004',
                'score': 98,
                'headcount': 84,
                'locations': self.positions['paris']['coords'],
                'name': 'Maistre Mathieu',
            },
        ]
        for i, doc in enumerate(docs, start=1):
            self.es.index(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=i, body=doc)

        # Required by ES to register new documents, flaky test here otherwise.
        self.es.indices.flush(index=settings.ES_INDEX)

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
                email='foo@bar.com',
                departement=zip_code[:2],
                x=doc['locations'][0]['lon'],
                y=doc['locations'][0]['lat'],
            )
            office.save()

        # We should have as much entries in MariaDB/MySQL than in Elasticsearch.
        self.assertEqual(Office.query.count(), len(docs))


class FavoriteTest(FavoriteBaseTest):
    """
    Test favorites.
    """

    def test_favorites_download(self):
        """
        Test download favorites list as csv.
        """
        office = Office.query.filter(Office.siret == '00000000000004').one()
        url = self.url_for('user.favorites_list_as_csv')

        # An anonymous user cannot download the favorites list.
        rv = self.app.get(url)
        self.assertEqual(rv.status_code, 401)

        with self.test_request_context():

            self.login(self.user)

            # Create a favorite for the user.
            UserFavoriteOffice.create(user_id=self.user.id, office_siret=office.siret)

            rv = self.app.get(url)
            self.assertEqual(rv.status_code, 200)
            self.assertEqual('application/csv', rv.mimetype)
            self.assertIn('siret', rv.data.decode('utf-8'))
            self.assertIn(office.siret, rv.data.decode('utf-8'))

    def test_favorites_list(self):
        """
        Test favorites list.
        """
        office = Office.query.filter(Office.siret == '00000000000004').one()
        url_list = self.url_for('user.favorites_list')

        # An anonymous user cannot access the favorites list.
        rv = self.app.get(url_list)
        self.assertEqual(rv.status_code, 401)

        with self.test_request_context():

            self.login(self.user)

            rv = self.app.get(url_list)
            self.assertEqual(rv.status_code, 200)
            self.assertTrue('Aucun favori pour le moment.' in rv.data.decode('utf-8'))

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
        office = Office.query.filter(Office.siret == '00000000000002').one()
        url_list = self.url_for('user.favorites_list')
        url_add = self.url_for('user.favorites_add', siret=office.siret)
        url_search_without_domain = '/entreprises/nancy-54100/strategie-commerciale'
        url_search_with_domain = 'http://labonneboite.pole-emploi.fr' + url_search_without_domain

        # An anonymous user cannot add a favorite.
        rv = self.app.post(url_add)
        self.assertEqual(rv.status_code, 401)

        with self.test_request_context():

            self.login(self.user)

            rv = self.app.get(url_list)
            self.assertEqual(rv.status_code, 200)
            self.assertTrue('Aucun favori pour le moment.' in rv.data.decode('utf-8'))

            # Adding favorite without next_url :
            # User should be redirected to the favorites list by default.
            rv = self.app.post(url_add)
            self.assertEqual(rv.status_code, 302)
            self.assertEqual(rv.location, url_list)

            # Adding favorite from search results - the realistic case.
            # User should be redirected back to the search results.
            rv = self.app.post(url_add, data={'next': url_search_without_domain})
            self.assertEqual(rv.status_code, 302)
            self.assertEqual(rv.location, url_search_with_domain)

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
        office = Office.query.filter(Office.siret == '00000000000003').one()
        url_list = self.url_for('user.favorites_list')
        url_delete = self.url_for('user.favorites_delete', siret=office.siret)
        url_search_without_domain = '/entreprises/nancy-54100/strategie-commerciale'
        url_search_with_domain = 'http://labonneboite.pole-emploi.fr' + url_search_without_domain

        # An anonymous user cannot delete a favorite.
        rv = self.app.post(url_delete)
        self.assertEqual(rv.status_code, 401)

        with self.test_request_context():

            self.login(self.user)

            # Create a favorite for the user.
            UserFavoriteOffice.create(user_id=self.user.id, office_siret=office.siret)

            rv = self.app.get(url_list)
            self.assertEqual(rv.status_code, 200)
            self.assertTrue(office.name in rv.data.decode('utf-8'))
            self.assertTrue(office.city in rv.data.decode('utf-8'))

            # Deleting favorite without next_url :
            # User should be redirected to the favorites list by default.
            rv = self.app.post(url_delete)
            self.assertEqual(rv.status_code, 302)
            self.assertEqual(rv.location, url_list)

            # Create again the favorite for the user.
            UserFavoriteOffice.create(user_id=self.user.id, office_siret=office.siret)

            # Deleting favorite from search results - the realistic case.
            # User should be redirected back to the search results.
            rv = self.app.post(url_delete, data={'next': url_search_without_domain})
            self.assertEqual(rv.status_code, 302)
            self.assertEqual(rv.location, url_search_with_domain)

            rv = self.app.get(url_list)
            self.assertEqual(rv.status_code, 200)
            self.assertTrue('Aucun favori pour le moment.' in rv.data.decode('utf-8'))

    def test_favorites_download_list_as_pdf(self):
        url_favorites_download = self.url_for('user.favorites_list_as_pdf')
        office = Office.query.filter(Office.siret == '00000000000001').one()
        UserFavoriteOffice.create(user_id=self.user.id, office_siret=office.siret)

        with self.test_request_context():
            self.login(self.user)
            rv = self.app.get(url_favorites_download)

        self.assertEqual(rv.status_code, 200)
        self.assertEqual('application/pdf', rv.mimetype)
        # Unfortunately, it's difficult to do any more testing on the content of the pdf
        self.assertLess(1000, len(rv.data))
