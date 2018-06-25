# coding: utf8
import unittest

from labonneboite.common import util
from labonneboite.common.load_data import load_contact_modes
from labonneboite.common.models import Office

class ContactModeTest(unittest.TestCase):

    def test_contact_mode(self):
        """
        Ensure contact_mode works in all edge cases.
        """
        contact_mode_dict = load_contact_modes()

        # Case 1 : naf and rome are in contact_mode mapping
        office1 = Office()
        rome = 'H2504'
        office1.naf = '1712Z'
        naf_prefix = office1.naf[:2]

        self.assertIn(naf_prefix, contact_mode_dict)
        self.assertIn(rome, contact_mode_dict[naf_prefix])
        contact_mode = util.get_contact_mode_for_rome_and_office(rome, office1)
        self.assertEqual(contact_mode, 'Se présenter spontanément')

        # Case 2 : naf is in contact_mode mapping but rome is not
        office2 = Office()
        rome = 'D1408'
        office2.naf = '1712Z'
        naf_prefix = office2.naf[:2]

        self.assertIn(naf_prefix, contact_mode_dict)
        self.assertNotIn(rome, contact_mode_dict[naf_prefix])
        contact_mode = util.get_contact_mode_for_rome_and_office(rome, office2)
        self.assertEqual(contact_mode, 'Se présenter spontanément')

        # Case 3 : naf is not in contact_mode mapping
        office3 = Office()
        rome = 'D1408'
        office3.naf = '9900Z'
        naf_prefix = office3.naf[:2]

        self.assertNotIn(naf_prefix, contact_mode_dict)
        contact_mode = util.get_contact_mode_for_rome_and_office(rome, office3)
        self.assertEqual(contact_mode, 'Envoyer un CV et une lettre de motivation')

        # Case 4 : custom contact_mode
        custom_contact_mode = 'Send a Fax'

        office4 = Office()
        rome = 'D1408'
        office4.naf = '1712Z'
        office4.contact_mode = custom_contact_mode

        contact_mode = util.get_contact_mode_for_rome_and_office(rome, office4)
        self.assertEqual(contact_mode, custom_contact_mode)
