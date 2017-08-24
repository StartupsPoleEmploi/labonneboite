# coding: utf8
import unittest

from labonneboite.common.models import OfficeAdminExtraGeoLocation


class OfficeAdminExtraGeoLocationTest(unittest.TestCase):
    """
    Tests for the OfficeAdminExtraGeoLocation model.
    """

    def test_codes_as_list(self):
        codes = u"   57070\n\n\n\n\n\n     75010  \n  54      "
        codes_as_list = OfficeAdminExtraGeoLocation.codes_as_list(codes)
        self.assertItemsEqual(codes_as_list, [u'54', u'57070', u'75010'])
        codes = u"75\r57\n13"
        codes_as_list = OfficeAdminExtraGeoLocation.codes_as_list(codes)
        self.assertItemsEqual(codes_as_list, [u'13', u'57', u'75'])

    def test_codes_as_geolocations(self):
        codes = u"75\n57070"
        codes_as_geolocations = OfficeAdminExtraGeoLocation.codes_as_geolocations(codes)
        expected = [
            # Found for the departement 75.
            ('48.8264581543', '2.32690527897'),
            ('48.8280603003', '2.3544809727'),
            ('48.8365381105', '2.42075934432'),
            ('48.8421891171', '2.29652252417'),
            ('48.8449537128', '2.37608588424'),
            ('48.846262612', '2.34839040879'),
            ('48.8501003498', '2.33402139523'),
            ('48.8543439464', '2.31294138206'),
            ('48.8553815318', '2.35541102422'),
            ('48.8566390262', '2.25972331102'),
            ('48.8566390262', '2.25972331102'),
            ('48.8590284068', '2.37705679761'),
            ('48.8622892805', '2.36158587519'),
            ('48.8628435865', '2.33807010768'),
            ('48.8643142257', '2.39961435812'),
            ('48.8684296759', '2.34149433888'),
            ('48.8729556556', '2.31369616661'),
            ('48.8758285242', '2.33869789273'),
            ('48.8761941084', '2.36107097577'),
            ('48.8878020912', '2.30862255671'),
            ('48.8928608126', '2.3479701879'),
            ('49.157869706', '6.2212499254'),
            # Found for 57070.
            ('48.8840228115', '2.38234715656'),
        ]
        self.assertItemsEqual(expected, codes_as_geolocations)

    def test_codes_as_json_geolocations(self):
        codes = u"75010"
        codes_as_json_geolocations = OfficeAdminExtraGeoLocation.codes_as_json_geolocations(codes)
        expected = '[["48.8761941084", "2.36107097577"]]'
        self.assertEqual(expected, codes_as_json_geolocations)
