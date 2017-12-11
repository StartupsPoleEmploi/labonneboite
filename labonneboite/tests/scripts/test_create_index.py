# coding: utf8
import datetime
import time

from flask import url_for
from social_flask_sqlalchemy.models import UserSocialAuth

from labonneboite.common import mapping as mapping_util
from labonneboite.common import scoring as scoring_util
from labonneboite.common.models import Office, OfficeAdminAdd, OfficeAdminRemove, OfficeAdminUpdate
from labonneboite.common.models import OfficeAdminExtraGeoLocation, User
from labonneboite.common.database import db_session
from labonneboite.scripts import create_index as script
from labonneboite.tests.test_base import DatabaseTest
from labonneboite.web.auth.backends.peam import PEAMOpenIdConnect



class CreateIndexBaseTest(DatabaseTest):
    """
    Create Elasticsearch and DB content for the unit tests.
    """

    def setUp(self, *args, **kwargs):
        super(CreateIndexBaseTest, self).setUp(*args, **kwargs)

        # use custom ES index for tests
        script.INDEX_NAME = self.ES_TEST_INDEX
        # FIXME ideally we should point to ES test index
        # settings.ES_INDEX = self.ES_TEST_INDEX

        # Create 1 office.
        self.office = Office(
            siret=u"78548035101646",
            company_name=u"SUPERMARCHES MATCH",
            office_name=u"SUPERMARCHES MATCH",
            naf=u"4711D",
            street_number=u"45",
            street_name=u"AVENUE ANDRE MALRAUX",
            city_code=u"57463",
            zipcode=u"57000",
            email=u"supermarche@match.com",
            tel=u"0387787878",
            website=u"http://www.supermarchesmatch.fr",
            flag_alternance=0,
            flag_junior=0,
            flag_senior=0,
            flag_handicap=0,
            departement=u"57",
            headcount=u"12",
            score=90,
            x=6.17952,
            y=49.1044,
        )
        self.office.save()

        # We should have 1 office in the DB.
        self.assertEquals(Office.query.count(), 1)

        # Put the office into ES.
        # Disable parallel computing because it does not play well with test environment (it hangs).
        script.create_offices(disable_parallel_computing=True)
        time.sleep(1)  # Sleep required by ES to register new documents.

        # We should have 1 office in the ES.
        count = self.es.count(index=self.ES_TEST_INDEX, doc_type=self.ES_OFFICE_TYPE, body={'query': {'match_all': {}}})
        self.assertEquals(count['count'], 1)
        # Ensure that the office is the one that has been indexed in ES.
        res = self.es.get(index=self.ES_TEST_INDEX, doc_type=self.ES_OFFICE_TYPE, id=self.office.siret)
        self.assertEquals(res['_source']['email'], self.office.email)

class DeleteOfficeAdminTest(CreateIndexBaseTest):
    def test_remove_office_admin(self):
        # Create officeAdminRemove and OfficeAdminAdd
        office_to_remove = OfficeAdminRemove(
            id=1,
            siret=self.office.siret,
            name=self.office.company_name,
            reason=u"N/A",
            initiative=False,
        )
        office_to_add = OfficeAdminAdd(
            id=1,
            siret=self.office.siret,
            company_name=self.office.company_name,
            office_name=self.office.office_name,
            naf=self.office.naf,
            street_number=self.office.street_number,
            street_name=self.office.street_name,
            zipcode=self.office.zipcode,
            city_code=self.office.city_code,
            flag_alternance=self.office.flag_alternance,
            flag_junior=self.office.flag_junior,
            flag_senior=self.office.flag_senior,
            departement=self.office.departement,
            headcount=self.office.headcount,
            score=self.office.score,
            x=self.office.x,
            y=self.office.y,
            reason=u"Demande de mise en avant",
        )
        office_to_remove.save()
        office_to_add.save()

        self.assertEquals(1, OfficeAdminRemove.query.filter_by(id=1).count())
        self.assertEquals(1, OfficeAdminAdd.query.filter_by(id=1).count())

        with self.test_request_context:
            # Create an user admin
            self.user = User(email=u'john@doe.com', gender=u'male',
                             first_name=u'John', last_name=u'Doe', active=True,
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
            self.assertEquals(db_session.query(User).count(), 1)
            self.login(self.user)

            # Calls to delete OfficeAdminRemove and OfficeAdminAdd
            self.app.post(url_for('officeadminadd.delete_view'), data={'id': 1})
            self.app.post(url_for('officeadminremove.delete_view'), data={'id': 1})

            self.assertEquals(0, OfficeAdminRemove.query.filter_by(id=1).count())
            self.assertEquals(0, OfficeAdminAdd.query.filter_by(id=1).count())


class VariousModesTest(CreateIndexBaseTest):
    """
    Test various modes of create_index script.
    Always disable parallel computing because it does not play well with testing,
    as it basically hangs.

    FIXME this is actually quite ugly, as it manipulates dev ES index and not test ES index
    """

    def test_create_index(self):
        script.update_data_profiling_wrapper(
            drop_indexes=False,
            enable_profiling=False,
            single_job=False,
            disable_parallel_computing=True,
        )

    def test_create_index_from_scratch(self):
        script.update_data_profiling_wrapper(
            drop_indexes=True,
            enable_profiling=False,
            single_job=False,
            disable_parallel_computing=True,
        )

    def test_create_index_from_scratch_with_profiling(self):
        script.update_data_profiling_wrapper(
            drop_indexes=True,
            enable_profiling=True,
            single_job=False,
            disable_parallel_computing=True,
        )

    def test_create_index_from_scratch_with_profiling_single_job(self):
        script.update_data_profiling_wrapper(
            drop_indexes=True,
            enable_profiling=True,
            single_job=True,
            disable_parallel_computing=True,
        )
        # single_job version of the script left ES data in an inconsistent state:
        # office data for only one departement
        # no ogr data nor location data
        # thus we need to rebuild normal data now:
        script.update_data_profiling_wrapper(
            drop_indexes=True,
            enable_profiling=False,
            single_job=False,
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
        doc = script.get_office_as_es_doc(self.office)
        expected_doc = {
            'website': u'http://www.supermarchesmatch.fr',
            'tel': u'0387787878',
            'flag_alternance': 0,
            'flag_senior': 0,
            'flag_handicap': 0,
            'naf': u'4711D',
            'name': u'SUPERMARCHES MATCH',
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
            'siret': u'78548035101646',
            'headcount': 12,
            'email': u'supermarche@match.com',
        }
        self.assertDictEqual(doc, expected_doc)


class AddOfficesTest(CreateIndexBaseTest):
    """
    Test add_offices().
    """

    def test_add_offices(self):
        """
        Test `add_offices` to add an office.
        """
        office_to_add = OfficeAdminAdd(
            siret=u"01625043300220",
            company_name=u"CHAUSSURES CENDRY",
            office_name=u"GEP",
            naf=u"4772A",
            street_number=u"11",
            street_name=u"RUE FABERT",
            zipcode=u"57000",
            city_code=u"57463",
            flag_alternance=0,
            flag_junior=0,
            flag_senior=0,
            departement=u"57",
            headcount=u'31',
            score=80,
            x=6.17528,
            y=49.1187,
            reason=u"Demande de mise en avant",
        )
        office_to_add.save()

        script.add_offices()

        office = Office.get(office_to_add.siret)
        self.assertEquals(office.company_name, office_to_add.company_name)
        self.assertEquals(office.score, office_to_add.score)
        self.assertEquals(office.email, u"")
        self.assertEquals(office.tel, u"")
        self.assertEquals(office.website, u"")

        res = self.es.get(index=self.ES_TEST_INDEX, doc_type=self.ES_OFFICE_TYPE, id=office_to_add.siret)
        self.assertEquals(res['_source']['siret'], office.siret)
        self.assertEquals(res['_source']['score'], office.score)


class RemoveOfficesTest(CreateIndexBaseTest):
    """
    Test remove_offices().
    """

    def test_remove_office(self):
        """
        Test `remove_offices` to delete an office.
        """
        office_to_remove = OfficeAdminRemove(
            siret=self.office.siret,
            name=self.office.company_name,
            reason=u"N/A",
            initiative=False,
        )
        office_to_remove.save()

        script.remove_offices()
        time.sleep(1)  # Sleep required by ES to register new documents.

        # The office should have been removed from the DB.
        self.assertEquals(Office.query.count(), 0)

        # The office should have been removed from ES.
        count = self.es.count(index=self.ES_TEST_INDEX, doc_type=self.ES_OFFICE_TYPE, body={'query': {'match_all': {}}})
        self.assertEquals(count['count'], 0)


class UpdateOfficesTest(CreateIndexBaseTest):
    """
    Test update_offices().
    """

    def test_update_office_by_updating_contact(self):
        """
        Test `update_offices` to update an office: update email and website, keep current phone.
        """
        office_to_update = OfficeAdminUpdate(
            siret=self.office.siret,
            name=self.office.company_name,
            boost=True,
            new_email=u"foo@pole-emploi.fr",
            new_phone=u"",  # Leave empty on purpose: it should not be modified.
            new_website=u"https://foo.pole-emploi.fr",
            remove_email=False,
            remove_phone=False,
            remove_website=False,
        )
        office_to_update.save()

        script.update_offices()

        office = Office.get(self.office.siret)
        self.assertEquals(office.email, office_to_update.new_email)
        self.assertEquals(office.score, office.score)  # This value should not be modified.
        self.assertEquals(office.tel, self.office.tel)  # This value should not be modified.
        self.assertEquals(office.website, office_to_update.new_website)

        res = self.es.get(index=self.ES_TEST_INDEX, doc_type=self.ES_OFFICE_TYPE, id=office.siret)
        self.assertEquals(res['_source']['email'], office.email)
        self.assertEquals(res['_source']['phone'], office.tel)
        self.assertEquals(res['_source']['website'], office.website)

        # Global score should always be the same.
        self.assertEquals(res['_source']['score'], office.score)
        # Check scores for ROME.
        # Since `romes_to_boost` is empty, all `scores_by_rome` should be set to 100.
        self.assertEquals(office_to_update.romes_to_boost, u"")
        for rome in mapping_util.romes_for_naf(office.naf):
            self.assertEquals(res['_source']['scores_by_rome'][rome.code], 100)

    def test_update_office_by_removing_contact(self):
        """
        Test `update_offices` to update an office: remove email, phone and website.
        """
        office_to_update = OfficeAdminUpdate(
            siret=self.office.siret,
            name=self.office.company_name,
            new_email=u"foo@pole-emploi.fr",  # Should be overriden by remove_email.
            new_website=u"https://foo.pole-emploi.fr",  # Should be overriden by remove_website.
            remove_email=True,
            remove_phone=True,
            remove_website=True,
        )
        office_to_update.save()

        script.update_offices()

        office = Office.get(self.office.siret)
        self.assertEquals(office.email, u'')
        self.assertEquals(office.tel, u'')
        self.assertEquals(office.website, u'')

        res = self.es.get(index=self.ES_TEST_INDEX, doc_type=self.ES_OFFICE_TYPE, id=office.siret)
        self.assertEquals(res['_source']['email'], u'')
        self.assertEquals(res['_source']['phone'], u'')
        self.assertEquals(res['_source']['website'], u'')

    def test_update_office_boost_specific_romes(self):
        """
        Test `update_offices` to update an office: boost score for specific ROME codes.
        """
        romes_for_office = [rome.code for rome in mapping_util.romes_for_naf(self.office.naf)]

        # Ensure the following ROME codes are related to the office.
        self.assertIn(u"D1507", romes_for_office)
        self.assertIn(u"D1103", romes_for_office)

        office_to_update = OfficeAdminUpdate(
            siret=self.office.siret,
            name=self.office.company_name,
            boost=True,
            romes_to_boost=u"D1507\nD1103",  # Boost score only for those ROME.
        )
        office_to_update.save()

        script.update_offices()

        office = Office.get(self.office.siret)
        res = self.es.get(index=self.ES_TEST_INDEX, doc_type=self.ES_OFFICE_TYPE, id=office.siret)

        # Check boosted scores.
        self.assertEquals(res['_source']['scores_by_rome']['D1507'], 100)
        self.assertEquals(res['_source']['scores_by_rome']['D1103'], 100)

        # Other scores should not be boosted.
        for rome in romes_for_office:
            if rome not in [u"D1507", u"D1103"]:
                try:
                    self.assertNotEqual(res['_source']['scores_by_rome'][rome], 100)
                except KeyError:
                    # Score for ROME has not been indexed because it was too low.
                    score = scoring_util.get_score_adjusted_to_rome_code_and_naf_code(
                        score=office.score, rome_code=rome, naf_code=office.naf)
                    self.assertTrue(score < script.SCORE_FOR_ROME_MINIMUM)

    def test_update_office_boost_unrelated_romes(self):
        """
        Test `update_offices` to update an office: boost score for specific ROME codes
        but with romes not associated to the office.
        """
        romes_for_office = [rome.code for rome in mapping_util.romes_for_naf(self.office.naf)]

        self.assertNotIn(u"D1506", romes_for_office) # Rome not related to the office
        self.assertIn(u"D1507", romes_for_office) # Rome related to the office

        office_to_update = OfficeAdminUpdate(
            siret=self.office.siret,
            name=self.office.company_name,
            boost=True,
            romes_to_boost=u"D1506\nD1507",  # Boost score only for those ROME.
        )
        office_to_update.save()

        script.update_offices()

        office = Office.get(self.office.siret)
        res = self.es.get(index=self.ES_TEST_INDEX, doc_type=self.ES_OFFICE_TYPE, id=office.siret)

        # Check boosted scores.
        self.assertEquals(res['_source']['scores_by_rome']['D1506'], 100)
        self.assertEquals(res['_source']['scores_by_rome']['D1507'], 100)

        # Other scores should not be boosted.
        for rome in romes_for_office:
            if rome not in [u"D1507"]:
                try:
                    self.assertNotEqual(res['_source']['scores_by_rome'][rome], 100)
                except KeyError:
                    # Score for ROME has not been indexed because it was too low.
                    score = scoring_util.get_score_adjusted_to_rome_code_and_naf_code(
                        score=office.score, rome_code=rome, naf_code=office.naf)
                    self.assertTrue(score < script.SCORE_FOR_ROME_MINIMUM)

    def test_update_office_removed_romes(self):
        """
        Test `update_offices` to update an office: remove specific ROME to an office
        """
        romes_for_office = [rome.code for rome in mapping_util.romes_for_naf(self.office.naf)]

        self.assertIn(u"D1101", romes_for_office) # Rome related to the office
        self.assertIn(u"D1507", romes_for_office) # Rome related to the office

        office_to_update = OfficeAdminUpdate(
            siret=self.office.siret,
            name=self.office.company_name,
            boost=False,
            romes_to_boost='',
            romes_to_remove=u"D1507",  # Remove score only for those ROME.
        )
        office_to_update.save()

        script.update_offices()

        office = Office.get(self.office.siret)
        res = self.es.get(index=self.ES_TEST_INDEX, doc_type=self.ES_OFFICE_TYPE, id=office.siret)

        # Check boosted scores.
        keys = res['_source']['scores_by_rome'].keys()
        self.assertTrue(u'D1101' in keys)
        self.assertFalse(u'D1507' in keys)

        # Other scores should not be boosted.
        for rome in romes_for_office:
            if rome not in [u"D1507"]:
                try:
                    self.assertNotEqual(res['_source']['scores_by_rome'][rome], 100)
                except KeyError:
                    # Score for ROME has not been indexed because it was too low.
                    score = scoring_util.get_score_adjusted_to_rome_code_and_naf_code(
                        score=office.score, rome_code=rome, naf_code=office.naf)
                    self.assertTrue(score < script.SCORE_FOR_ROME_MINIMUM)

    def test_update_office_add_email_alternance(self):
        """
        Test `update_offices` to add an email for alternance
        """
        office = Office.get(self.office.siret)
        self.assertNotEquals(office.email_alternance, "email_alternance@mail.com")
        
        office_to_update = OfficeAdminUpdate(
            siret=self.office.siret,
            name=self.office.company_name,
            email_alternance=u"email_alternance@mail.com",
        )
        office_to_update.save(commit=True)

        script.update_offices()

        office = Office.get(self.office.siret)
        self.assertEquals(office.email_alternance, "email_alternance@mail.com")

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
            siret=self.office.siret,
            codes=u"75110\n13055",  # Paris 10 + Marseille
        )
        extra_geolocation.save(commit=True)

        script.update_offices_geolocations()

        # The office should now have 3 geolocations in ES (the original one + Paris 10 + Marseille).
        res = self.es.get(index=self.ES_TEST_INDEX, doc_type=self.ES_OFFICE_TYPE, id=self.office.siret)
        expected_locations = [
            {u'lat': 49.1044, u'lon': 6.17952},
            {u'lat': 43.25996690043557, u'lon': 5.370740865779022},
            {u'lat': 48.8815994262695, u'lon': 2.36229991912841},
        ]
        self.assertItemsEqual(res['_source']['locations'], expected_locations)

        office = Office.get(self.office.siret)
        self.assertTrue(office.has_multi_geolocations)

        # Make `extra_geolocation` instance out-of-date.
        extra_geolocation.date_end = datetime.datetime.now() - datetime.timedelta(days=1)
        extra_geolocation.update()
        self.assertTrue(extra_geolocation.is_outdated())

        script.update_offices_geolocations()

        # The office extra geolocations should now be reset.
        res = self.es.get(index=self.ES_TEST_INDEX, doc_type=self.ES_OFFICE_TYPE, id=self.office.siret)
        expected_locations = [
            {u'lat': 49.1044, u'lon': 6.17952},
        ]
        self.assertItemsEqual(res['_source']['locations'], expected_locations)

        office = Office.get(self.office.siret)
        self.assertFalse(office.has_multi_geolocations)
