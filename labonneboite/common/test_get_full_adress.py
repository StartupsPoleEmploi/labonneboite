import unittest

from .get_full_adress import get_full_adress, IncorrectAdressDataException


class TestFullAddres(unittest.TestCase):
    def assertConvertMatch(self, street_number: str, street_name: str, zipcode: str, city: str, expected: str):
        result = get_full_adress(street_number, street_name, zipcode, city)
        self.assertEqual(result, expected)

    def testDistrict(self):
        self.assertConvertMatch("15", "RUE DU TEST", "75015", "PARIS 15EME ARRONDISSEMENT", "15 RUE DU TEST 75015 PARIS")
        self.assertRaises(IncorrectAdressDataException, lambda: get_full_adress("", "", "", "INVALID ARRONDISSEMENT"))
    
    def testLieuDit(self):
        self.assertConvertMatch("-", "LIEU DIT RONJOU", "73190", "SAINT-BALDOPH", "RONJOU 73190 SAINT-BALDOPH")

    def testEmpty(self):
        self.assertConvertMatch("", "", "", "", "")
        self.assertConvertMatch(None, None, None, None, "")
        self.assertConvertMatch("1", "", "", "", "1")
        self.assertConvertMatch("", "RUE", "", "", "RUE")
        self.assertConvertMatch("", "", "15000", "", "15000")
        self.assertConvertMatch("", "", "", "Metz", "Metz")
        self.assertConvertMatch("", "RUE", "15000", "", "RUE 15000")
        self.assertConvertMatch("1", "", "15000", "", "1 15000")
