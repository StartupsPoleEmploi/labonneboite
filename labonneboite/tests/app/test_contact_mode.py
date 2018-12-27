# coding: utf8
import unittest

from labonneboite.common.contact_mode import (CONTACT_MODE_MAIL, CONTACT_MODE_EMAIL,
        CONTACT_MODE_OFFICE, CONTACT_MODE_WEBSITE, CONTACT_MODE_PHONE)
from labonneboite.common.models import Office

class ContactModeTest(unittest.TestCase):

    def test_contact_mode(self):
        """
        Ensure contact_mode works in all edge cases.
        """
        # office has no data at all
        office = Office()
        self.assertEqual(office.recommended_contact_mode, None)
        self.assertEqual(office.recommended_contact_mode_label, '')

        # office has a contact_mode suggesting email but has no data
        office = Office()
        office.contact_mode = 'Contactez nous par mail'
        office.email = ''
        self.assertEqual(office.recommended_contact_mode, None)

        # office has a contact_mode suggesting email and has data
        office = Office()
        office.contact_mode = 'Contactez nous par mail'
        office.email = 'pouac@plonk.fr'
        self.assertEqual(office.recommended_contact_mode, CONTACT_MODE_EMAIL)

        # office has a contact_mode suggesting phone but has no data
        office = Office()
        office.contact_mode = 'Contactez nous par téléphone'
        office.tel = ''
        self.assertEqual(office.recommended_contact_mode, None)

        # office has a contact_mode suggesting phone and has data
        office = Office()
        office.contact_mode = 'Contactez nous par téléphone'
        office.tel = '0199009900'
        self.assertEqual(office.recommended_contact_mode, CONTACT_MODE_PHONE)

        # office has a contact_mode suggesting website but has no data
        office = Office()
        office.contact_mode = 'Déposez votre CV sur notre site internet'
        office.website = ''
        self.assertEqual(office.recommended_contact_mode, None)

        # office has a contact_mode suggesting website and has data
        office = Office()
        office.contact_mode = 'Déposez votre CV sur notre site internet'
        office.website = 'http://www.pouac.fr'
        self.assertEqual(office.recommended_contact_mode, CONTACT_MODE_WEBSITE)

        # office has a contact_mode suggesting postal mail
        office = Office()
        office.contact_mode = 'Envoyez votre CV par courrier'
        self.assertEqual(office.recommended_contact_mode, CONTACT_MODE_MAIL)

        # office has a contact_mode suggesting showing up
        office = Office()
        office.contact_mode = 'Présentez vous directement à notre entreprise'
        self.assertEqual(office.recommended_contact_mode, CONTACT_MODE_OFFICE)

        # in absence of contact_mode, email has precedence over phone
        office = Office()
        office.email = 'pouac@plonk.fr'
        office.tel = '0199009900'
        self.assertEqual(office.recommended_contact_mode, CONTACT_MODE_EMAIL)

        # in absence of contact_mode and email, phone has precedence over website
        office = Office()
        office.email = ''
        office.tel = '0199009900'
        office.website = 'http://www.pouac.fr'
        self.assertEqual(office.recommended_contact_mode, CONTACT_MODE_PHONE)

        # only a website
        office = Office()
        office.email = ''
        office.tel = ''
        office.website = 'http://www.pouac.fr'
        self.assertEqual(office.recommended_contact_mode, CONTACT_MODE_WEBSITE)


