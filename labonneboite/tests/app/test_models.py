# coding: utf8
import datetime

from labonneboite.common.database import db_session
from labonneboite.common.models import OfficeAdminExtraGeoLocation
from labonneboite.tests.test_base import DatabaseTest


class OfficeAdminExtraGeoLocationTest(DatabaseTest):
    """
    Tests for the OfficeAdminExtraGeoLocation model.
    """

    def test_clean(self):
        """
        Test `OfficeAdminExtraGeoLocation.clean()`.
        """
        extra_geolocation = OfficeAdminExtraGeoLocation(
            siret=u"38524664000176",
            codes=u"75110\n\n\n\n\n\n\n57616",
            reason=u"Paris 10 + Metz Saint Julien",
        )
        db_session.add(extra_geolocation)
        db_session.commit()
        # The `clean()` method should have been called automatically.
        extra_geolocation = db_session.query(OfficeAdminExtraGeoLocation).first()
        # Multiple newlines should have been removed.
        self.assertEqual(extra_geolocation.codes, u'57616\n75110')
        # Corresponding Lat/Lon coords should have been found and stored.
        self.assertEqual(
            extra_geolocation.geolocations,
            '[[49.135208952059884, 6.207906756168173], [48.8815994262695, 2.36229991912841]]'
        )

    def test_is_outdated(self):
        """
        Test `OfficeAdminExtraGeoLocation.is_outdated()`.
        """
        extra_geolocation = OfficeAdminExtraGeoLocation(
            siret=u"38524664000176",
            codes=u"75108",
        )
        extra_geolocation.save()
        self.assertFalse(extra_geolocation.is_outdated())
        # Make `extra_geolocation` instance out-of-date.
        extra_geolocation.date_end = datetime.datetime.now() - datetime.timedelta(days=1)
        extra_geolocation.update()
        self.assertTrue(extra_geolocation.is_outdated())

    def test_codes_as_list(self):
        """
        Test `OfficeAdminExtraGeoLocation.codes_as_list()`.
        """
        codes = u"   57616\n\n\n\n\n\n     75110  \n  54      "
        codes_as_list = OfficeAdminExtraGeoLocation.codes_as_list(codes)
        self.assertItemsEqual(codes_as_list, [u'54', u'57616', u'75110'])
        codes = u"75\r57\n13"
        codes_as_list = OfficeAdminExtraGeoLocation.codes_as_list(codes)
        self.assertItemsEqual(codes_as_list, [u'13', u'57', u'75'])

    def test_codes_as_geolocations(self):
        """
        Test `OfficeAdminExtraGeoLocation.codes_as_geolocations()`.
        """
        codes = u"75\n57616"
        codes_as_geolocations = OfficeAdminExtraGeoLocation.codes_as_geolocations(codes)
        expected = [
            # Found for the departement 75.
            (48.8274002075195, 2.36660003662109),
            (48.8367004394531, 2.39689993858337),
            (48.8611984252929, 2.3833999633789),
            (48.8815994262695, 2.36229991912841),
            (48.8866996765136, 2.30349993705749),
            (48.8712005615234, 2.28929996490478),
            (48.8445014953613, 2.29769992828369),
            (48.8316993713378, 2.32319998741149),
            (48.8825988769531, 2.39109992980957),
            (48.8917007446289, 2.35100007057189),
            (48.8646011352539, 2.40639996528625),
            (48.84495371275856, 2.3760858842364394),
            (48.872200012207, 2.31680011749267),
            (48.8801002502441, 2.34039998054504),
            (48.8544006347656, 2.36240005493164),
            (48.8446998596191, 2.35419988632202),
            (48.8470001220703, 2.33459997177124),
            (48.8564987182617, 2.31369996070861),
            (48.8536415100097, 2.34842991828918),
            (48.8694992065429, 2.34479999542236),
            (48.8627014160156, 2.3652000427246),
            # Found for 57616.
            (49.135208952059884, 6.207906756168173),
        ]
        self.assertItemsEqual(expected, codes_as_geolocations)

    def test_codes_as_json_geolocations(self):
        """
        Test `OfficeAdminExtraGeoLocation.codes_as_json_geolocations()`.
        """
        codes = u"75110"
        codes_as_json_geolocations = OfficeAdminExtraGeoLocation.codes_as_json_geolocations(codes)
        expected = '[[48.8815994262695, 2.36229991912841]]'
        self.assertEqual(expected, codes_as_json_geolocations)
