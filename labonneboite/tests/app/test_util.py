from labonneboite.tests.test_base import DatabaseTest
from labonneboite.conf import settings
from labonneboite.common.util import get_enum_from_value

from enum import auto, Enum
class EnumTest(Enum):
    COMPANY_EMAIL = auto()
    COMPANY_PHONE = auto()
    COMPANY_WEBSITE = auto()
    COMPANY_BOE = auto()
    COMPANY_PMSMP = auto()

class UtilTest(DatabaseTest):

    def test_get_enum_from_value(self):
        self.assertEqual(get_enum_from_value(EnumTest, 'unknown_value'), None)
        self.assertEqual(get_enum_from_value(EnumTest, 'unknown_value', EnumTest.COMPANY_WEBSITE), EnumTest.COMPANY_WEBSITE)
        self.assertEqual(get_enum_from_value(EnumTest, EnumTest.COMPANY_WEBSITE.value), EnumTest.COMPANY_WEBSITE)
