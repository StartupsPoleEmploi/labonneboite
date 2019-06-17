from unittest import mock

from labonneboite.common import models
from labonneboite.tests.test_base import DatabaseTest
from labonneboite.web.contact_form import forms, mail


class ContactFormBaseTest(DatabaseTest):
    """
    Base class for `contact_form` views.
    """

    def setUp(self):
        super().setUp()

        self.office_info = {
            'siret': "00000000000001",
            'naf': "4711B",
            'office_name': "Test company",
            'company_name': "Test company",
            'city_code': 44109,
            'zipcode': 44000,
            'departement': 44,
        }
        self.office = models.Office(**self.office_info).save()

        self.recruiter_hidden_identification = {
            'siret': self.office.siret,
            'first_name': "John",
            'last_name': "Doe",
            'phone': '0601020304',
            'email': "test@test.com",
        }


class UpdateCoordinatesTest(ContactFormBaseTest):
    """
    Test that a recruiter can update his company's coordinates.
    """

    def test_generate_update_coordinates_mail(self):
        """
        Test `mail.generate_update_coordinates_mail()` method.
        """
        with self.test_request_context():

            form_data = {
                'new_contact_mode': 'office',
                'new_email': 'exemple@domaine.com',
                'new_email_alternance': 'exemple-alternance@domaine.com',
                'new_phone': '01 77 86 39 49',
                'new_phone_alternance': '02 77 86 39 49',
                'new_website': 'http://exemple.com',
                'social_network': 'https://www.facebook.com/poleemploi/',
                'rgpd_consent': True,
            }
            form_data.update(self.recruiter_hidden_identification)
            form = forms.OfficeUpdateCoordinatesForm(data=form_data)

            recruiter_message = models.UpdateCoordinatesRecruiterMessage.create_from_form(form)
            mail_content = mail.generate_update_coordinates_mail(form, recruiter_message)

            contact_mode_label = forms.OfficeUpdateCoordinatesForm.CONTACT_MODES_LABELS.get(form.new_contact_mode, '')
            contact_mode_expected = 'Mode de contact à privilégier : {}'.format(contact_mode_label)

            self.assertIn('Nouveau site Internet : http://exemple.com', mail_content)
            self.assertIn('Nouvel e-mail recruteur : exemple@domaine.com', mail_content)
            self.assertIn('Nouveau téléphone : 01 77 86 39 49', mail_content)
            self.assertIn(contact_mode_expected, mail_content)
            self.assertIn('Nouvel email recruteur spécifique alternance : exemple-alternance@domaine.com', mail_content)
            self.assertIn('Nouveau téléphone spécifique alternance : 02 77 86 39 49', mail_content)
            self.assertIn('Réseau social : https://www.facebook.com/poleemploi/', mail_content)

    def test_update_coordinates_form(self):
        """
        Test `update_coordinates_form` view.
        """
        with mock.patch('labonneboite.web.contact_form.mail.send_mail'):

            form_data = {
                'new_contact_mode': 'office',
                'new_email': 'exemple@domaine.com',
                'new_email_alternance': 'exemple-alternance@domaine.com',
                'new_phone': '01 77 86 39 49',
                'new_phone_alternance': '02 77 86 39 49',
                'new_website': 'http://exemple.com',
                'social_network': 'https://www.facebook.com/poleemploi/',
                'rgpd_consent': True,
            }
            form_data.update(self.recruiter_hidden_identification)

            url = self.url_for('contact_form.update_coordinates_form')
            rv = self.app.post(url, data=form_data)

            self.assertEqual(rv.status_code, 302)
            self.assertIn(self.url_for('contact_form.success'), rv.location)

            # An entry should have been created in `UpdateCoordinatesRecruiterMessage`.
            msg = models.UpdateCoordinatesRecruiterMessage.query.filter(
                    models.UpdateCoordinatesRecruiterMessage.siret == form_data['siret'],
                ).one()
            self.assertEqual(msg.new_website, form_data['new_website'])
            self.assertEqual(msg.new_email, form_data['new_email'])
            self.assertEqual(msg.new_phone, form_data['new_phone'])
            self.assertEqual(msg.contact_mode, form_data['new_contact_mode'])
            self.assertEqual(msg.new_email_alternance, form_data['new_email_alternance'])
            self.assertEqual(msg.new_phone_alternance, form_data['new_phone_alternance'])
            self.assertEqual(msg.social_network, form_data['social_network'])
            self.assertEqual(msg.siret, form_data['siret'])
            self.assertEqual(msg.requested_by_first_name, form_data['first_name'])
            self.assertEqual(msg.requested_by_last_name, form_data['last_name'])
            self.assertEqual(msg.requested_by_email, form_data['email'])
            self.assertEqual(msg.requested_by_phone, form_data['phone'])
            self.assertEqual(msg.certified_recruiter, False)


class UpdateJobsTest(ContactFormBaseTest):
    """
    Test that a recruiter can add or delete ROME codes related to his company.

    Default ROME/NAF mapping for NAF `4711B`:
    -----------------------------------------------------------------
    D1507 "Mise en rayon libre-service"
    D1106 "Vente en alimentation"
    D1505 "Personnel de caisse"
    D1214 "Vente en habillement et accessoires de la personne"

    Some ROMEs not in the default ROME/NAF mapping for NAF `4711B`:
    -----------------------------------------------------------------
    M1802 "Expertise et support en systèmes d'information"
    M1803 "Direction des systèmes d'information"
    M1805 "Études et développement informatique"
    """

    def test_office_update_jobs_form(self):
        """
        Test `OfficeUpdateJobsForm` class.
        """
        form_data = {
            'romes_to_keep': ['D1507'],
            'romes_alternance_to_keep': ['D1106'],
            'extra_romes_to_add': ['M1805'],
            'extra_romes_alternance_to_add': ['M1805'],
        }
        form_data.update(self.recruiter_hidden_identification)

        # Populate global `request.form` because it's used in `form.validate().
        with self.test_request_context(method='POST', data=form_data):
            form = forms.OfficeUpdateJobsForm(data=form_data, office=self.office)
            form.validate()
            self.assertCountEqual(form.romes_to_add, {'D1507', 'M1805'})
            self.assertCountEqual(form.romes_alternance_to_add, {'D1106', 'M1805'})
            self.assertCountEqual(form.romes_to_remove, self.office.romes_codes - {'D1507', 'M1805'})
            self.assertCountEqual(form.romes_alternance_to_remove, self.office.romes_codes - {'D1106', 'M1805'})

    def test_generate_update_jobs_mail(self):
        """
        Test `mail.generate_update_jobs_mail()` method.
        """
        form_data = {
            'romes_to_keep': ['D1507', 'D1106'],
            'romes_alternance_to_keep': ['D1214', 'D1106'],
            'extra_romes_to_add': ['M1802', 'M1803', 'M1805'],
            'extra_romes_alternance_to_add': ['M1805'],
        }
        form_data.update(self.recruiter_hidden_identification)
        # Populate global `request.form` because it's used in `form.validate().
        with self.test_request_context(method='POST', data=form_data):
            form = forms.OfficeUpdateJobsForm(data=form_data, office=self.office)
            form.validate()
            recruiter_message = models.UpdateJobsRecruiterMessage.create_from_form(form)
            mail_content = mail.generate_update_jobs_mail(form, recruiter_message)
            self.assertIn(mail.format_romes(form.romes_to_add), mail_content)
            self.assertIn(mail.format_romes(form.romes_alternance_to_add), mail_content)
            self.assertIn(mail.format_romes(form.romes_to_remove), mail_content)
            self.assertIn(mail.format_romes(form.romes_alternance_to_remove), mail_content)

    def test_view_update_jobs_form(self):
        """
        Test `update_jobs_form` view.
        """
        with mock.patch('labonneboite.web.contact_form.mail.send_mail'):

            romes_to_keep = ['D1507', 'D1106']
            romes_alternance_to_keep = ['D1214', 'D1106']
            extra_romes_to_add = ['M1802', 'M1803', 'M1805']
            extra_romes_alternance_to_add = ['M1805']

            form_data = {
                'romes_to_keep': romes_to_keep,
                'romes_alternance_to_keep': romes_alternance_to_keep,
                'extra_romes_to_add': extra_romes_to_add,
                'extra_romes_alternance_to_add': extra_romes_alternance_to_add,
            }
            form_data.update(self.recruiter_hidden_identification)

            url = self.url_for('contact_form.update_jobs_form')
            rv = self.app.post(url, data=form_data)
            self.assertEqual(rv.status_code, 302)
            self.assertIn(self.url_for('contact_form.success'), rv.location)

            # An entry should have been created in `UpdateJobsRecruiterMessage`.
            msg = models.UpdateJobsRecruiterMessage.query.filter(
                    models.UpdateJobsRecruiterMessage.siret == self.office.siret,
                ).one()

            romes_to_add = set(romes_to_keep + extra_romes_to_add)
            self.assertCountEqual(romes_to_add, msg.romes_to_add.split(','))

            romes_alternance_to_add = set(romes_alternance_to_keep + extra_romes_alternance_to_add)
            self.assertCountEqual(romes_alternance_to_add, msg.romes_alternance_to_add.split(','))

            romes_to_remove = self.office.romes_codes - romes_to_add
            self.assertCountEqual(romes_to_remove, msg.romes_to_remove.split(','))

            romes_alternance_to_remove = self.office.romes_codes - romes_alternance_to_add
            self.assertCountEqual(romes_alternance_to_remove, msg.romes_alternance_to_remove.split(','))

            self.assertEqual(msg.siret, form_data['siret'])
            self.assertEqual(msg.requested_by_first_name, form_data['first_name'])
            self.assertEqual(msg.requested_by_last_name, form_data['last_name'])
            self.assertEqual(msg.requested_by_email, form_data['email'])
            self.assertEqual(msg.requested_by_phone, form_data['phone'])
            self.assertEqual(msg.certified_recruiter, False)


class DeleteFormFormTest(ContactFormBaseTest):
    """
    Test that a recruiter can remove his company from LBB/LBA.
    """

    def test_generate_delete_mail(self):
        """
        Test `mail.generate_delete_mail()` method.
        """
        with self.test_request_context():

            form_data = {
                'remove_lba': True,
                'remove_lbb': False,
            }
            form_data.update(self.recruiter_hidden_identification)
            form = forms.OfficeRemoveForm(data=form_data)

            mail_content = mail.generate_delete_mail(form, models.RemoveRecruiterMessage.create_from_form(form))
            self.assertIn("Suppression de LBB : non", mail_content)
            self.assertIn("Suppression de LBA : oui", mail_content)

    def test_delete_form(self):
        """
        Test `delete_form` view.
        """
        with mock.patch('labonneboite.web.contact_form.mail.send_mail'):

            form_data = {
                'remove_lba': '1',
                'remove_lbb': '',  # Empty means not checked.
            }
            form_data.update(self.recruiter_hidden_identification)

            url = self.url_for('contact_form.delete_form')
            rv = self.app.post(url, data=form_data)

            self.assertEqual(rv.status_code, 302)
            self.assertIn(self.url_for('contact_form.success'), rv.location)

            # An entry should have been created in `RemoveRecruiterMessage`.
            msg = models.RemoveRecruiterMessage.query.filter(
                    models.RemoveRecruiterMessage.siret == form_data['siret'],
                ).one()
            self.assertEqual(msg.remove_lba, 1)
            self.assertEqual(msg.remove_lbb, 0)
            self.assertEqual(msg.siret, form_data['siret'])
            self.assertEqual(msg.requested_by_first_name, form_data['first_name'])
            self.assertEqual(msg.requested_by_last_name, form_data['last_name'])
            self.assertEqual(msg.requested_by_email, form_data['email'])
            self.assertEqual(msg.requested_by_phone, form_data['phone'])
            self.assertEqual(msg.certified_recruiter, False)


class OtherFormTest(ContactFormBaseTest):
    """
    Test that a recruiter can make another demand.
    """

    def test_generate_other_mail(self):
        """
        Test `mail.generate_other_mail()` method.
        """
        with self.test_request_context():

            form_data = {
                'comment': 'Bonjour à tous',
            }
            form_data.update(self.recruiter_hidden_identification)
            form = forms.OfficeOtherRequestForm(data=form_data)

            mail_content = mail.generate_other_mail(form, models.OtherRecruiterMessage.create_from_form(form))
            actionLineExpected = f"Action : {mail.compute_action_name(form)}"
            self.assertIn(actionLineExpected, mail_content)
            self.assertIn(f"Siret : {form_data['siret']}", mail_content)
            self.assertIn(f"Prénom : {form_data['first_name']}", mail_content)
            self.assertIn(f"Nom : {form_data['last_name']}", mail_content)
            self.assertIn(f"E-mail : {form_data['email']}", mail_content)
            self.assertIn(f"Téléphone : {form_data['phone']}", mail_content)


    def test_update_coordinates_form(self):
        """
        Test `other_form` view.
        """
        with mock.patch('labonneboite.web.contact_form.mail.send_mail'):

            form_data = {
                'comment': 'Bonjour à tous',
            }
            form_data.update(self.recruiter_hidden_identification)

            url = self.url_for('contact_form.other_form')
            rv = self.app.post(url, data=form_data)

            self.assertEqual(rv.status_code, 302)
            self.assertIn(self.url_for('contact_form.success'), rv.location)

            # An entry should have been created in `OtherRecruiterMessage`.
            msg = models.OtherRecruiterMessage.query.filter(
                    models.OtherRecruiterMessage.siret == form_data['siret'],
                ).one()

            self.assertEqual(msg.comment, form_data['comment'])
            self.assertEqual(msg.siret, form_data['siret'])
            self.assertEqual(msg.requested_by_first_name, form_data['first_name'])
            self.assertEqual(msg.requested_by_last_name, form_data['last_name'])
            self.assertEqual(msg.requested_by_email, form_data['email'])
            self.assertEqual(msg.requested_by_phone, form_data['phone'])
            self.assertEqual(msg.certified_recruiter, False)
