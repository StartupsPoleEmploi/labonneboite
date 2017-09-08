# coding: utf8
import unittest

from labonneboite.common import util
from labonneboite.common.load_data import load_contact_modes

class ContactModeTest(unittest.TestCase):

    def test_contact_mode(self):
        """
        Ensure contact_mode works in all edge cases.
        """
        contact_mode_dict = load_contact_modes()

        # Case 1 : naf and rome are in contact_mode mapping
        rome = u'H2504'
        naf = u'1712Z'
        naf_prefix = naf[:2]

        self.assertIn(naf_prefix, contact_mode_dict)
        self.assertIn(rome, contact_mode_dict[naf_prefix])
        contact_mode = util.get_contact_mode_for_rome_and_naf(rome, naf)
        self.assertEqual(contact_mode, u'Se présenter spontanément')

        # Case 2 : naf is in contact_mode mapping but rome is not
        rome = u'D1408'
        naf = u'1712Z'
        naf_prefix = naf[:2]

        self.assertIn(naf_prefix, contact_mode_dict)
        self.assertNotIn(rome, contact_mode_dict[naf_prefix])
        contact_mode = util.get_contact_mode_for_rome_and_naf(rome, naf)
        self.assertEqual(contact_mode, u'Se présenter spontanément')

        # Case 3 : naf is not in contact_mode mapping
        rome = u'D1408'
        naf = u'9900Z'
        naf_prefix = naf[:2]

        self.assertNotIn(naf_prefix, contact_mode_dict)
        contact_mode = util.get_contact_mode_for_rome_and_naf(rome, naf)
        self.assertEqual(contact_mode, u'Envoyer un CV et une lettre de motivation')

