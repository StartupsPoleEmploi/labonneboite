# coding: utf8
import datetime
import mock

from flask import url_for
from social_flask_sqlalchemy.models import UserSocialAuth

from labonneboite.common import mapping as mapping_util
from labonneboite.common.models import Office, OfficeAdminAdd, OfficeAdminRemove, OfficeAdminUpdate
from labonneboite.common.models import OfficeAdminExtraGeoLocation, User
from labonneboite.common.database import db_session
from labonneboite.conf import settings
from labonneboite.common import es
from labonneboite.scripts import create_index as script
from labonneboite.tests.test_base import DatabaseTest
from labonneboite.web.auth.backends.peam import PEAMOpenIdConnect



class CreateIndexBaseTest(DatabaseTest):
    """
    Create Elasticsearch and DB content for the unit tests.
    """

    def setUp(self, *args, **kwargs):
        super(CreateIndexBaseTest, self).setUp(*args, **kwargs)

        # Mute script logging
        script.logger.setLevel(script.logging.CRITICAL)

        self.office1 = Office(
            siret="78548035101646",
            company_name="SUPERMARCHES MATCH",
            office_name="SUPERMARCHES MATCH",
            naf="4711D",
            street_number="45",
            street_name="AVENUE ANDRE MALRAUX",
            city_code="57463",
            zipcode="57000",
            email="supermarche@match.com",
            tel="0387787878",
            website="http://www.supermarchesmatch.fr",
            flag_alternance=0,
            flag_junior=0,
            flag_senior=0,
            flag_handicap=0,
            departement="57",
            headcount="12",
            score=90,
            score_alternance=90,
            x=6.17952,
            y=49.1044,
        )
        self.office1.save()

        self.office2 = Office(
            siret="78548035101647",
            company_name="HYPER U",
            office_name="HYPER U",
            naf="4711D",
            street_number="8",
            street_name="AVENUE DE LA LIBERATION",
            city_code="44101",
            zipcode="44620",
            email="hyper-u-lamontagne@match.com",
            tel="0240659515",
            website="http://www.hyper-u-lamontagne.fr",
            flag_alternance=0,
            flag_junior=0,
            flag_senior=0,
            flag_handicap=0,
            departement="44",
            headcount="21",
            score=77,
            score_alternance=75,
            x=-1.68333,
            y=47.183331,
        )
        self.office2.save()

        # We should have 2 offices in the DB.
        self.assertEqual(Office.query.count(), 2)

        # Put offices into ES.
        # Disable parallel computing because it does not play well with test environment (it hangs).
        script.create_offices(disable_parallel_computing=True)
        self.es.indices.flush(index=settings.ES_INDEX) # required by ES to register new documents.

        # We should have 3 offices in ES (2 + the fake office).
        count = self.es.count(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, body={'query': {'match_all': {}}})
        self.assertEqual(count['count'], 2+1)
        # Ensure that the office is the one that has been indexed in ES.
        res = self.es.get(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=self.office1.siret)
        self.assertEqual(res['_source']['email'], self.office1.email)
        res = self.es.get(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=self.office2.siret)
        self.assertEqual(res['_source']['email'], self.office2.email)

class DeleteOfficeAdminTest(CreateIndexBaseTest):
    def test_office_admin_add(self):
        form = {
            "siret": "78548035101646",
            "company_name": "SUPERMARCHES MATCH",
            "office_name": "SUPERMARCHES MATCH",
            "naf": "4711D",
            "street_number": "45",
            "street_name": "AVENUE ANDRE MALRAUX",
            "city_code": "57463",
            "zipcode": "57000",
            "email": "supermarche@match.com",
            "tel": "0387787878",
            "website": "http://www.supermarchesmatch.fr",
            "flag_alternance": 0,
            "flag_junior": 0,
            "flag_senior": 0,
            "flag_handicap": 0,
            "departement": "57",
            "headcount": "12",
            "score": 90,
            "x": 6.17952,
            "y": 49.1044,
            "reason": "Demande de mise en avant",
        }

        with self.test_request_context:
            # Create an user admin
            self.user = User(email='john@doe.com', gender='male',
                             first_name='John', last_name='Doe', active=True,
                             is_admin=True)
            db_session.add(self.user)
            db_session.flush()

            user_social_auth = UserSocialAuth(
                provider=PEAMOpenIdConnect.name,
                extra_data={'id_token': 'fake'},
                user_id=self.user.id,
            )
            db_session.add(user_social_auth)
            db_session.commit()

            # Login as user admin
            self.user = db_session.query(User).filter_by(id=self.user.id).first()
            self.assertEqual(db_session.query(User).count(), 1)
            self.login(self.user)

            # Create OfficeAdminRemove
            self.assertEqual(0, OfficeAdminAdd.query.filter_by(id=1).count())
            self.app.post(url_for('officeadminadd.create_view'), data=form)
            self.assertEqual(1, OfficeAdminAdd.query.filter_by(id=1).count())

            # Delete OfficeAdminAdd
            self.app.post(url_for('officeadminadd.delete_view'), data={'id': 1})
            self.assertEqual(0, OfficeAdminRemove.query.filter_by(id=1).count())

    def test_office_admin_remove(self):
        # Create officeAdminRemove
        form = {
            'siret': '01234567891234',
            'name': 'Test company',
            'reason': 'N/A',
            'initiative': 'office',
        }

        with self.test_request_context:
            # Create an user admin
            self.user = User(email='john@doe.com', gender='male',
                             first_name='John', last_name='Doe', active=True,
                             is_admin=True)
            db_session.add(self.user)
            db_session.flush()

            user_social_auth = UserSocialAuth(
                provider=PEAMOpenIdConnect.name,
                extra_data={'id_token': 'fake'},
                user_id=self.user.id,
            )
            db_session.add(user_social_auth)
            db_session.commit()

            # Login as user admin
            self.user = db_session.query(User).filter_by(id=self.user.id).first()
            self.assertEqual(db_session.query(User).count(), 1)
            self.login(self.user)

            # Create OfficeAdminRemove
            self.assertEqual(0, OfficeAdminRemove.query.filter_by(siret='01234567891234').count())
            self.app.post(url_for('officeadminremove.create_view'), data=form)
            self.assertEqual(1, OfficeAdminRemove.query.filter_by(siret='01234567891234').count())

            # Delete OfficeAdminRemove
            self.app.post(url_for('officeadminremove.delete_view'), data={'id': 1})
            self.assertEqual(0, OfficeAdminRemove.query.filter_by(id=1).count())


class VariousModesTest(CreateIndexBaseTest):
    """
    Test various modes of create_index script.
    Always disable parallel computing because it does not play well with testing,
    as it basically hangs.

    FIXME this is actually quite ugly, as it manipulates dev ES index and not test ES index
    """

    def test_create_index(self):
        script.update_data_profiling_wrapper(
            create_full=False,
            create_partial=False,
            disable_parallel_computing=True,
        )

    def test_create_index_from_scratch(self):
        # longer ES timeout needed for slow docker performance in local dev on Mac OS when running `make test-scripts`
        with mock.patch.object(settings, 'ES_TIMEOUT', 30):
            script.update_data_profiling_wrapper(
                create_full=True,
                create_partial=False,
                disable_parallel_computing=True,
            )

    def test_create_index_from_scratch_with_profiling(self):
        with mock.patch.object(script.Profiling, 'ACTIVATED', True):
            script.update_data_profiling_wrapper(
                create_full=True,
                create_partial=False,
                disable_parallel_computing=True,
            )

    def test_create_index_from_scratch_with_profiling_create_partial(self):
        with mock.patch.object(script.Profiling, 'ACTIVATED', True):
            script.update_data_profiling_wrapper(
                create_full=False,
                create_partial=True,
                disable_parallel_computing=True,
            )

        # create_partial version of the script left ES data in an inconsistent state:
        # office data for only one departement
        # no ogr data nor location data
        # thus we need to rebuild normal data now:
        script.update_data_profiling_wrapper(
            create_full=True,
            create_partial=False,
            disable_parallel_computing=True,
        )

class UtilsTest(CreateIndexBaseTest):
    """
    Test utility functions.
    """

    def test_get_office_as_es_doc(self):
        """
        Test `get_office_as_es_doc()`.
        """
        doc = script.get_office_as_es_doc(self.office1)
        expected_doc = {
            'website': 'http://www.supermarchesmatch.fr',
            'tel': '0387787878',
            'flag_alternance': 0,
            'flag_senior': 0,
            'flag_handicap': 0,
            'naf': '4711D',
            'name': 'SUPERMARCHES MATCH',
            'flag_junior': 0,
            'score': 90,
            'scores_by_rome': {
                'N1103': 25,
                'D1214': 51,
                'D1101': 45,
                'D1507': 54,
                'D1506': 90,
                'D1505': 52,
                'D1502': 20,
                'M1607': 20,
                'K1303': 20,
                'D1106': 45
            },
            'locations': [
                {'lat': 49.1044, 'lon': 6.17952},
            ],
            'siret': '78548035101646',
            'headcount': 12,
            'email': 'supermarche@match.com',
        }
        # self.assertDictEqual(doc, expected_doc)


class AddOfficesTest(CreateIndexBaseTest):
    """
    Test add_offices().
    """

    def test_add_offices(self):
        """
        Test `add_offices` to add an office.
        """
        office_to_add = OfficeAdminAdd(
            siret="01625043300220",
            company_name="CHAUSSURES CENDRY",
            office_name="GEP",
            naf="4772A",
            street_number="11",
            street_name="RUE FABERT",
            zipcode="57000",
            city_code="57463",
            flag_alternance=0,
            flag_junior=0,
            flag_senior=0,
            departement="57",
            headcount='31',
            score=80,
            x=6.17528,
            y=49.1187,
            reason="Demande de mise en avant",
        )
        office_to_add.save()

        script.add_offices()

        office = Office.get(office_to_add.siret)
        self.assertEqual(office.company_name, office_to_add.company_name)
        self.assertEqual(office.score, office_to_add.score)
        self.assertEqual(office.email, "")
        self.assertEqual(office.tel, "")
        self.assertEqual(office.website, "")

        res = self.es.get(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=office_to_add.siret)
        self.assertEqual(res['_source']['siret'], office.siret)
        self.assertEqual(res['_source']['score'], office.score)


class RemoveOfficesTest(CreateIndexBaseTest):
    """
    Test remove_offices().
    """

    def test_remove_office(self):
        """
        Test `remove_offices` to delete an office.
        """
        office_to_remove1 = OfficeAdminRemove(
            siret=self.office1.siret,
            name=self.office1.company_name,
            reason="N/A",
            initiative=False,
        )
        office_to_remove1.save()

        office_to_remove2 = OfficeAdminRemove(
            siret=self.office2.siret,
            name=self.office2.company_name,
            reason="N/A",
            initiative=False,
        )
        office_to_remove2.save()

        # We should have 3 offices in ES (2 + the fake office).
        count = self.es.count(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, body={'query': {'match_all': {}}})
        self.assertEqual(count['count'], 3)

        script.remove_offices()
        self.es.indices.flush(index=settings.ES_INDEX) # Required by ES to register new documents.

        # The offices should have been removed from the DB.
        self.assertEqual(Office.query.count(), 0)

        # The offices should have been removed from ES. Only the fake doc remains.
        count = self.es.count(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, body={'query': {'match_all': {}}})
        self.assertEqual(count['count'], 1)


class UpdateOfficesTest(CreateIndexBaseTest):

    def test_no_update_no_company_removal(self):
        """
        No updates done, scores_by_romes and scores_alternance_by_rome should not be impacted
        Related to a previous bug where some scores where removed.
        """
        # No romes removed when computing scores
        with mock.patch.object(script.scoring_util, 'SCORE_FOR_ROME_MINIMUM', 0), mock.patch.object(script.scoring_util, 'SCORE_ALTERNANCE_FOR_ROME_MINIMUM', 0):
            script.update_offices()

        for office in [self.office1, self.office2]:
            romes_for_office = [rome.code for rome in mapping_util.romes_for_naf(office.naf)]
            res = self.es.get(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=office.siret)

            self.assertIn('scores_by_rome', res['_source'])
            self.assertIn('scores_alternance_by_rome', res['_source'])

            self.assertTrue(len(romes_for_office), len(res['_source']['scores_by_rome']))
            self.assertTrue(len(romes_for_office), len(res['_source']['scores_alternance_by_rome']))


    """
    Test update_offices().
    """

    def test_update_office_by_updating_contact(self):
        """
        Test `update_offices` to update an office: update email and website, keep current phone.
        """
        office_to_update = OfficeAdminUpdate(
            sirets=self.office1.siret,
            name=self.office1.company_name,
            boost=True,
            new_email="foo@pole-emploi.fr",
            new_phone="",  # Leave empty on purpose: it should not be modified.
            new_website="https://foo.pole-emploi.fr",
            remove_email=False,
            remove_phone=False,
            remove_website=False,
        )
        office_to_update.save()

        script.update_offices()

        office = Office.get(self.office1.siret)
        self.assertEqual(office.email, office_to_update.new_email)
        self.assertEqual(office.score, office.score)  # This value should not be modified.
        self.assertEqual(office.tel, self.office1.tel)  # This value should not be modified.
        self.assertEqual(office.website, office_to_update.new_website)

        res = self.es.get(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=office.siret)
        self.assertEqual(res['_source']['email'], office.email)
        self.assertEqual(res['_source']['phone'], office.tel)
        self.assertEqual(res['_source']['website'], office.website)

        # Global score should always be the same.
        self.assertEqual(res['_source']['score'], office.score)
        # Check scores for ROME.
        # Since `romes_to_boost` is empty, all romes should be boosted.
        self.assertEqual(office_to_update.romes_to_boost, "")
        for rome in mapping_util.romes_for_naf(office.naf):
            self.assertTrue(res['_source']['boosted_romes'][rome.code])

    def test_update_office_by_removing_contact(self):
        """
        Test `update_offices` to update an office: remove email, phone and website.
        """
        office_to_update = OfficeAdminUpdate(
            sirets=self.office1.siret,
            name=self.office1.company_name,
            new_email="foo@pole-emploi.fr",  # Should be overriden by remove_email.
            new_website="https://foo.pole-emploi.fr",  # Should be overriden by remove_website.
            remove_email=True,
            remove_phone=True,
            remove_website=True,
        )
        office_to_update.save()

        script.update_offices()

        office = Office.get(self.office1.siret)
        self.assertEqual(office.email, '')
        self.assertEqual(office.tel, '')
        self.assertEqual(office.website, '')

        res = self.es.get(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=office.siret)
        self.assertEqual(res['_source']['email'], '')
        self.assertEqual(res['_source']['phone'], '')
        self.assertEqual(res['_source']['website'], '')

    def test_update_office_boost_specific_romes(self):
        """
        Test `update_offices` to update an office: boost score for specific ROME codes.
        """
        romes_for_office = [rome.code for rome in mapping_util.romes_for_naf(self.office1.naf)]

        # Ensure the following ROME codes are related to the office.
        self.assertIn("D1507", romes_for_office)
        self.assertIn("D1103", romes_for_office)

        office_to_update = OfficeAdminUpdate(
            sirets=self.office1.siret,
            name=self.office1.company_name,
            boost=True,
            romes_to_boost="D1507\nD1103",  # Boost score only for those ROME.
        )
        office_to_update.save()

        script.update_offices()

        office = Office.get(self.office1.siret)
        res = self.es.get(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=office.siret)

        # Check boosted scores.
        self.assertEqual({
            'D1507': True,
            'D1103': True,
        }, res['_source']['boosted_romes'])


    def test_update_office_boost_unrelated_romes(self):
        """
        Test `update_offices` to update an office: boost score for specific ROME codes
        but with romes not associated to the office.
        """
        romes_for_office = [rome.code for rome in mapping_util.romes_for_naf(self.office1.naf)]

        self.assertNotIn("D1506", romes_for_office) # Rome not related to the office
        self.assertIn("D1507", romes_for_office) # Rome related to the office

        office_to_update = OfficeAdminUpdate(
            sirets=self.office1.siret,
            name=self.office1.company_name,
            boost=True,
            romes_to_boost="D1506\nD1507",  # Boost score only for those ROME.
        )
        office_to_update.save()

        script.update_offices()

        office = Office.get(self.office1.siret)
        res = self.es.get(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=office.siret)

        # Check boosted scores.
        self.assertTrue(res['_source']['boosted_romes']['D1506'])
        self.assertTrue(res['_source']['boosted_romes']['D1507'])

        # Other scores should not be boosted.
        for rome in romes_for_office:
            if rome != "D1507":
                self.assertNotIn(rome, res['_source']['boosted_romes'])

    def test_update_office_removed_romes(self):
        """
        Test `update_offices` to update an office: remove specific ROME to an office
        """
        romes_for_office = [rome.code for rome in mapping_util.romes_for_naf(self.office1.naf)]

        self.assertIn("D1101", romes_for_office) # Rome related to the office
        self.assertIn("D1507", romes_for_office) # Rome related to the office

        office_to_update = OfficeAdminUpdate(
            sirets=self.office1.siret,
            name=self.office1.company_name,
            boost=False,
            romes_to_boost='',
            romes_to_remove="D1507",  # Remove score only for those ROME.
        )
        office_to_update.save()

        script.update_offices()

        office = Office.get(self.office1.siret)
        res = self.es.get(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=office.siret)

        # Check rome scores.
        self.assertIn('D1101', res['_source']['scores_by_rome'])
        self.assertNotIn('D1507', res['_source']['scores_by_rome'])

        # Other scores should not be boosted.
        for rome in romes_for_office:
            if rome != "D1507":
                self.assertNotIn(rome, res['_source']['boosted_romes'])

    def test_update_office_add_alternance_infos(self):
        """
        Test `update_offices` to add an email for alternance
        """
        office = Office.get(self.office1.siret)
        self.assertNotEqual(office.email_alternance, "email_alternance@mail.com")

        office_to_update = OfficeAdminUpdate(
            sirets=self.office1.siret,
            name=self.office1.company_name,
            email_alternance="email_alternance@mail.com",
            phone_alternance="0699999999",
            website_alternance="http://example-alternance.com",
        )
        office_to_update.save(commit=True)
        script.update_offices()

        office = Office.get(self.office1.siret)
        self.assertEqual(office.email_alternance, "email_alternance@mail.com")
        self.assertEqual(office.phone_alternance, "0699999999")
        self.assertEqual(office.website_alternance, "http://example-alternance.com")

    def test_update_office_remove_alternance(self):
        """
        Test `update_offices` to hide it on lba
        """

        # Remove alternance for this company
        office_to_update = OfficeAdminUpdate(
            sirets=self.office1.siret,
            name=self.office1.company_name,
            score_alternance=0,
        )

        office = Office.get(self.office1.siret)
        self.assertNotEqual(office.score_alternance, 0)

        office_to_update.save(commit=True)
        script.update_offices()

        # Expected score alternance = 0
        office = Office.get(self.office1.siret)
        self.assertEqual(office.score_alternance, 0)


    def test_update_office_remove_on_lbb(self):
        """
        Test `update_offices` to hide on lbb
        """

        # Remove for this company
        office_to_update = OfficeAdminUpdate(
            sirets=self.office1.siret,
            name=self.office1.company_name,
            score=0,
        )

        office = Office.get(self.office1.siret)
        self.assertNotEqual(office.score, 0)

        office_to_update.save(commit=True)
        script.update_offices()

        # Expected score_rome = 0
        office = Office.get(self.office1.siret)
        self.assertEqual(office.score, 0)


    def test_update_office_add_naf(self):
        romes_for_office = [rome.code for rome in mapping_util.romes_for_naf(self.office1.naf)]
        romes_for_office += [rome.code for rome in mapping_util.romes_for_naf("4772A")]

        office_to_update = OfficeAdminUpdate(
            sirets=self.office1.siret,
            name=self.office1.company_name,
            nafs_to_add="4772A",
        )
        office_to_update.save()

        # Use a mock to temporarily adjust scoring_util.SCORE_FOR_ROME_MINIMUM
        # and avoid removing romes if their score is too low.
        with mock.patch.object(script.scoring_util, 'SCORE_FOR_ROME_MINIMUM', 0):
            script.update_offices()

        res = self.es.get(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=self.office1.siret)
        self.assertEqual(len(set(romes_for_office)), len(res['_source']['scores_by_rome']))


    def test_remove_contacts_multi_siret(self):
        sirets = [self.office1.siret, self.office2.siret]

        office_to_update = OfficeAdminUpdate(
            sirets='\n'.join(sirets),
            name="Supermarché",
            remove_email=True,
            remove_phone=True,
            remove_website=True,
        )
        office_to_update.save()

        script.update_offices()

        for siret in sirets:
            office = Office.get(siret)
            self.assertEqual(office.email, '')
            self.assertEqual(office.tel, '')
            self.assertEqual(office.website, '')

            res = self.es.get(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=siret)
            self.assertEqual(res['_source']['email'], '')
            self.assertEqual(res['_source']['phone'], '')
            self.assertEqual(res['_source']['website'], '')


    def test_email_alternance_multi_siret(self):
        sirets = [self.office1.siret, self.office2.siret]

        office_to_update = OfficeAdminUpdate(
            sirets='\n'.join(sirets),
            name="Supermarché",
            email_alternance="email_alternance@mail.com",
            phone_alternance="0699999999",
            website_alternance="http://example-alternance.com",
        )
        office_to_update.save(commit=True)
        script.update_offices()

        for siret in sirets:
            office = Office.get(siret)
            self.assertEqual(office.email_alternance, "email_alternance@mail.com")
            self.assertEqual(office.phone_alternance, "0699999999")
            self.assertEqual(office.website_alternance, "http://example-alternance.com")


    def test_boost_multi_siret(self):
        sirets = [self.office1.siret, self.office2.siret]

        office_to_update = OfficeAdminUpdate(
            sirets='\n'.join(sirets),
            name="Supermarché",
            boost=True,
        )
        office_to_update.save(commit=True)
        script.update_offices()

        for siret in sirets:
            office = Office.get(siret)
            res = self.es.get(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=siret)

            # Since `romes_to_boost` is empty, all `scores_by_rome` should be boosted.
            self.assertEqual(office_to_update.romes_to_boost, "")
            for rome in mapping_util.romes_for_naf(office.naf):
                self.assertTrue(res['_source']['boosted_romes'][rome.code])


    def test_new_contact_multi_siret(self):
        sirets = [self.office1.siret, self.office2.siret]

        office_to_update = OfficeAdminUpdate(
            sirets='\n'.join(sirets),
            name="Supermarchés",
            new_email="foo@pole-emploi.fr",
            new_phone="0240656459",
            new_website="https://foo.pole-emploi.fr",
            remove_email=False,
            remove_phone=False,
            remove_website=False,
        )
        office_to_update.save()
        script.update_offices()

        for siret in sirets:
            office = Office.get(siret)
            self.assertEqual(office.email, office_to_update.new_email)
            self.assertEqual(office.tel, office_to_update.new_phone)
            self.assertEqual(office.website, office_to_update.new_website)

            res = self.es.get(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=siret)
            self.assertEqual(res['_source']['email'], office_to_update.new_email)
            self.assertEqual(res['_source']['phone'], office_to_update.new_phone)
            self.assertEqual(res['_source']['website'], office_to_update.new_website)


    def test_nafs_to_add_multi_siret(self):
        romes_for_office = [rome.code for rome in mapping_util.romes_for_naf(self.office1.naf)]
        romes_for_office += [rome.code for rome in mapping_util.romes_for_naf("4772A")]

        sirets = [self.office1.siret, self.office2.siret]

        office_to_update = OfficeAdminUpdate(
            sirets='\n'.join(sirets),
            name="Supermarchés",
            nafs_to_add="4772A",
        )
        office_to_update.save()

        # Use a mock to temporarily adjust scoring_util.SCORE_FOR_ROME_MINIMUM
        # and avoid removing romes if their score is too low.
        with mock.patch.object(script.scoring_util, 'SCORE_FOR_ROME_MINIMUM', 0):
            script.update_offices()

        for siret in sirets:
            res = self.es.get(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=siret)
            self.assertEqual(len(set(romes_for_office)), len(res['_source']['scores_by_rome']))


    def test_romes_to_boost_multi_siret(self):
        sirets = [self.office1.siret, self.office2.siret]

        romes_for_office = [rome.code for rome in mapping_util.romes_for_naf(self.office1.naf)]

        # Ensure the following ROME codes are related to the office.
        self.assertIn("D1507", romes_for_office)
        self.assertIn("D1103", romes_for_office)

        office_to_update = OfficeAdminUpdate(
            sirets='\n'.join(sirets),
            name="Supermarchés",
            boost=True,
            romes_to_boost="D1507\nD1103",  # Boost score only for those ROME.
        )
        office_to_update.save()

        script.update_offices()

        for siret in sirets:
            res = self.es.get(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=siret)

            # Check boosted scores.
            self.assertTrue(res['_source']['boosted_romes']['D1507'])
            self.assertTrue(res['_source']['boosted_romes']['D1103'])


    def test_romes_to_remove_multi_siret(self):
        romes_for_office = [rome.code for rome in mapping_util.romes_for_naf(self.office1.naf)]

        sirets = [self.office1.siret, self.office2.siret]


        self.assertIn("D1101", romes_for_office) # Rome related to the office
        self.assertIn("D1507", romes_for_office) # Rome related to the office

        office_to_update = OfficeAdminUpdate(
            sirets='\n'.join(sirets),
            name="Supermarchés",
            boost=False,
            romes_to_boost='',
            romes_to_remove="D1507",  # Remove score only for those ROME.
        )
        office_to_update.save()

        script.update_offices()

        for siret in sirets:
            res = self.es.get(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=siret)

            # Check romes
            self.assertIn('D1101', res['_source']['scores_by_rome'])
            self.assertNotIn('D1507', res['_source']['scores_by_rome'])


    def test_romes_alternance_to_remove_single_siret(self):
        romes_for_office = [rome.code for rome in mapping_util.romes_for_naf(self.office1.naf)]

        siret = self.office1.siret

        self.assertIn("D1101", romes_for_office) # Rome related to the office
        self.assertIn("D1507", romes_for_office) # Rome related to the office

        office_to_update = OfficeAdminUpdate(
            sirets=siret,
            name="Supermarchés",
            boost_alternance=False,
            romes_alternance_to_boost='',
            romes_alternance_to_remove="D1507",  # Remove score only for those ROME.
        )
        office_to_update.save()

        script.update_offices()

        res = self.es.get(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=siret)

        # Check romes
        self.assertIn('D1101', res['_source']['scores_alternance_by_rome'])
        self.assertNotIn('D1507', res['_source']['scores_alternance_by_rome'])


    def test_romes_alternance_to_remove_multi_siret(self):
        romes_for_office = [rome.code for rome in mapping_util.romes_for_naf(self.office1.naf)]

        sirets = [self.office1.siret, self.office2.siret]

        self.assertIn("D1101", romes_for_office) # Rome related to the office
        self.assertIn("D1507", romes_for_office) # Rome related to the office

        office_to_update = OfficeAdminUpdate(
            sirets='\n'.join(sirets),
            name="Supermarchés",
            boost_alternance=False,
            romes_alternance_to_boost='',
            romes_alternance_to_remove="D1507",  # Remove score only for those ROME.
        )
        office_to_update.save()

        script.update_offices()

        for siret in sirets:
            res = self.es.get(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=siret)

            # Check romes
            self.assertIn('D1101', res['_source']['scores_alternance_by_rome'])
            self.assertNotIn('D1507', res['_source']['scores_alternance_by_rome'])


    def test_update_office_boost_specific_romes_alternance(self):
        """
        Test `update_offices` to update an office: boost alternance score for specific ROME codes.
        """
        romes_for_office = [rome.code for rome in mapping_util.romes_for_naf(self.office1.naf)]

        # Ensure the following ROME codes are related to the office.
        self.assertIn("D1507", romes_for_office)
        self.assertIn("D1103", romes_for_office)

        office_to_update = OfficeAdminUpdate(
            sirets=self.office1.siret,
            name=self.office1.company_name,
            boost_alternance=True,
            romes_alternance_to_boost="D1507\nD1103",  # Boost score only for those ROME.
        )
        office_to_update.save()

        script.update_offices()

        office = Office.get(self.office1.siret)
        res = self.es.get(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=office.siret)

        # Check boosted scores.
        self.assertEqual({
            'D1507': True,
            'D1103': True,
        }, res['_source']['boosted_alternance_romes'])


    def test_update_office_social_network(self):
        """
        Test `update_offices` to update an office: boost alternance score for specific ROME codes.
        """
        office_to_update = OfficeAdminUpdate(
            sirets=self.office1.siret,
            name=self.office1.company_name,
            social_network="https://www.facebook.com/poleemploi/",
        )
        office_to_update.save()
        script.update_offices()
        office = Office.get(self.office1.siret)
        # Check contact mode
        self.assertEqual("https://www.facebook.com/poleemploi/", office.social_network)


    def test_update_office_contact_mode(self):
        """
        Test `update_offices` to update an office: boost alternance score for specific ROME codes.
        """
        office_to_update = OfficeAdminUpdate(
            sirets=self.office1.siret,
            name=self.office1.company_name,
            contact_mode="Come with his driver license",
        )

        office_to_update.save()
        script.update_offices()

        office = Office.get(self.office1.siret)

        # Check contact mode
        self.assertEqual("Come with his driver license", office.contact_mode)



class UpdateOfficesGeolocationsTest(CreateIndexBaseTest):
    """
    Test update_offices_geolocations().
    """

    def test_update_offices_geolocations(self):
        """
        Test `update_offices_geolocations`.
        """
        # Add an entry in the OfficeAdminExtraGeoLocation table with extra geolocations.
        extra_geolocation = OfficeAdminExtraGeoLocation(
            siret=self.office1.siret,
            codes="75110\n13055",  # Paris 10 + Marseille
        )
        extra_geolocation.save(commit=True)

        script.update_offices_geolocations()

        # The office should now have 3 geolocations in ES (the original one + Paris 10 + Marseille).
        res = self.es.get(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=self.office1.siret)
        expected_locations = [
            {'lat': 43.25996690043557, 'lon': 5.370740865779022},
            {'lat': 48.8815994262695, 'lon': 2.36229991912841},
            {'lat': 49.1044, 'lon': 6.17952},
        ]
        self.assertEqual(sorted(res['_source']['locations'], key=lambda x: (x['lat'], x['lon'])), expected_locations)

        office = Office.get(self.office1.siret)
        self.assertTrue(office.has_multi_geolocations)

        # Make `extra_geolocation` instance out-of-date.
        extra_geolocation.date_end = datetime.datetime.now() - datetime.timedelta(days=1)
        extra_geolocation.update()
        self.assertTrue(extra_geolocation.is_outdated())

        script.update_offices_geolocations()

        # The office extra geolocations should now be reset.
        res = self.es.get(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=self.office1.siret)
        expected_locations = [
            {'lat': 49.1044, 'lon': 6.17952},
        ]
        self.assertEqual(res['_source']['locations'], expected_locations)

        office = Office.get(self.office1.siret)
        self.assertFalse(office.has_multi_geolocations)
