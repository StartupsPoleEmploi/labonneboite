# coding: utf8
import datetime
import time

from labonneboite.common import mapping as mapping_util
from labonneboite.common import scoring as scoring_util
from labonneboite.common.models import Office, OfficeAdminAdd, OfficeAdminRemove, OfficeAdminUpdate
from labonneboite.common.models import OfficeAdminExtraGeoLocation
from labonneboite.scripts import create_index as script
from labonneboite.tests.test_base import DatabaseTest


class CreateIndexBaseTest(DatabaseTest):
    """
    Create Elasticsearch and DB content for the unit tests.
    """

    def setUp(self, *args, **kwargs):
        super(CreateIndexBaseTest, self).setUp(*args, **kwargs)

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
        script.create_offices(index=self.ES_TEST_INDEX)
        time.sleep(1)  # Sleep required by ES to register new documents.

        # We should have 1 office in the ES.
        count = self.es.count(index=self.ES_TEST_INDEX, doc_type=self.ES_OFFICE_TYPE, body={'query': {'match_all': {}}})
        self.assertEquals(count['count'], 1)
        # Ensure that the office is the one that has been indexed in ES.
        res = self.es.get(index=self.ES_TEST_INDEX, doc_type=self.ES_OFFICE_TYPE, id=self.office.siret)
        self.assertEquals(res['_source']['email'], self.office.email)


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
                'D1101': 43,
                'D1106': 47,
                'D1214': 51,
                'D1505': 52,
                'D1507': 54,
                'N1103': 24,
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

        script.add_offices(index=self.ES_TEST_INDEX)
        time.sleep(1)  # Sleep required by ES to register new documents.

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

        script.remove_offices(index=self.ES_TEST_INDEX)
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

        script.update_offices(index=self.ES_TEST_INDEX)
        time.sleep(1)  # Sleep required by ES to register new documents.

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
        mapper = mapping_util.Rome2NafMapper()
        # Since `romes_to_boost` is empty, all `scores_by_rome` should be set to 100.
        self.assertEquals(office_to_update.romes_to_boost, u"")
        for rome in mapper.romes_for_naf(office.naf):
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

        script.update_offices(index=self.ES_TEST_INDEX)
        time.sleep(1)  # Sleep required by ES to register new documents.

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
        mapper = mapping_util.Rome2NafMapper()
        romes_for_office = [rome.code for rome in mapper.romes_for_naf(self.office.naf)]

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

        script.update_offices(index=self.ES_TEST_INDEX)
        time.sleep(1)  # Sleep required by ES to register new documents.

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
        mapper = mapping_util.Rome2NafMapper()
        romes_for_office = [rome.code for rome in mapper.romes_for_naf(self.office.naf)]

        self.assertNotIn(u"D1506", romes_for_office) # Rome not related to the office
        self.assertIn(u"D1507", romes_for_office) # Rome related to the office

        office_to_update = OfficeAdminUpdate(
            siret=self.office.siret,
            name=self.office.company_name,
            boost=True,
            romes_to_boost=u"D1506\nD1507",  # Boost score only for those ROME.
        )
        office_to_update.save()

        script.update_offices(index=self.ES_TEST_INDEX)
        time.sleep(1)  # Sleep required by ES to register new documents.

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
        mapper = mapping_util.Rome2NafMapper()
        romes_for_office = [rome.code for rome in mapper.romes_for_naf(self.office.naf)]

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

        script.update_offices(index=self.ES_TEST_INDEX)
        time.sleep(1)  # Sleep required by ES to register new documents.

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
        extra_geolocation.save()

        script.update_offices_geolocations(index=self.ES_TEST_INDEX)
        time.sleep(1)  # Sleep required by ES to register new documents.

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

        script.update_offices_geolocations(index=self.ES_TEST_INDEX)
        time.sleep(1)  # Sleep required by ES to register new documents.

        # The office extra geolocations should now be reset.
        res = self.es.get(index=self.ES_TEST_INDEX, doc_type=self.ES_OFFICE_TYPE, id=self.office.siret)
        expected_locations = [
            {u'lat': 49.1044, u'lon': 6.17952},
        ]
        self.assertItemsEqual(res['_source']['locations'], expected_locations)

        office = Office.get(self.office.siret)
        self.assertFalse(office.has_multi_geolocations)
