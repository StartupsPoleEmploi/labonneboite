from unittest import mock

from labonneboite.common.models import Office
from labonneboite.common.models import UpdateJobsRecruiterMessage
from labonneboite.tests.test_base import DatabaseTest
from labonneboite.web.contact_form import forms, mail


class ContactFormBaseTest(DatabaseTest):
    """
    Base class for `contact_form` views.
    """

    def setUp(self):
        """
        Default ROME/NAF mapping for NAF `4711B`:
        -----------------------------------------------------------------
        D1507 "Mise en rayon libre-service"
        D1106 "Vente en alimentation"
        D1505 "Personnel de caisse"
        D1214 "Vente en habillement et accessoires de la personne"
        N1103 "Magasinage et préparation de commandes"
        D1101 "Boucherie"
        G1602 "Personnel de cuisine"
        G1803 "Service en restauration"
        D1301 "Management de magasin de détail"
        N4105 "Conduite et livraison par tournées sur courte distance"
        G1603 "Personnel polyvalent en restauration"
        D1502 "Management/gestion de rayon produits alimentaires"
        D1102 "Boulangerie - viennoiserie"
        D1504 "Direction de magasin de grande distribution"
        D1107 "Vente en gros de produits frais"
        D1105 "Poissonnerie"

        Some ROMEs not in the default ROME/NAF mapping for NAF `4711B`:
        -----------------------------------------------------------------
        M1802 "Expertise et support en systèmes d'information"
        M1803 "Direction des systèmes d'information"
        M1805 "Études et développement informatique"
        """
        super().setUp()

        self.office_info = {
            'siret': '00000000000001',
            'naf': '4711B',
            'office_name': "Test company",
            'company_name': "Test company",
            'city_code': 44109,
            'zipcode': 44000,
            'departement': 44,
        }
        self.office = Office(**self.office_info).save()

        self.recruiter_hidden_identification = {
            'siret': self.office.siret,
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '0606060606',
            'email': 'test@test.com',
        }


class MailTest(ContactFormBaseTest):
    """
    Test the mail module.
    """

    def test_generate_update_jobs_mail(self):

        with self.test_request_context:

            form_data = {
                'romes_to_keep': ['D1507', 'D1106', 'D1214', 'D1101', 'D1502'],
                'romes_alternance_to_keep': ['D1101', 'D1105'],
                'extra_romes_to_add': ['M1802', 'M1803', 'M1805'],
                'extra_romes_alternance_to_add': ['M1805'],
            }

            # Add recruiter hidden identification info.
            form_data.update(self.recruiter_hidden_identification)

            form = forms.OfficeUpdateJobsForm(data=form_data, office=self.office)
            form.validate()

            recruiter_message = UpdateJobsRecruiterMessage.create_from_form(form)

            mail_content = mail.generate_update_jobs_mail(form, recruiter_message)

            self.assertIn(mail.format_romes(form.romes_to_add), mail_content)
            self.assertIn(mail.format_romes(form.romes_alternance_to_add), mail_content)
            self.assertIn(mail.format_romes(form.romes_to_remove), mail_content)
            self.assertIn(mail.format_romes(form.romes_alternance_to_remove), mail_content)


class UpdateJobsFormTest(ContactFormBaseTest):
    """
    Test the abitlity for a recruiter to add or delete
    ROME codes related to his company.
    """

    def test_GET_without_recruiter_id(self):
        url = self.url_for('contact_form.update_jobs_form', siret=self.office.siret)
        rv = self.app.get(url)
        self.assertEqual(rv.status_code, 302)
        self.assertEqual(rv.location, self.url_for('contact_form.change_info'))

    def test_GET_with_recruiter_id(self):
        url = self.url_for('contact_form.update_jobs_form', **self.recruiter_hidden_identification)
        rv = self.app.get(url)
        self.assertEqual(rv.status_code, 200)

        self.assertIn('name="romes_to_keep"', rv.data.decode())
        self.assertIn('name="romes_alternance_to_keep"', rv.data.decode())
        for rome_code in self.office.romes_codes:
            self.assertIn(rome_code, rv.data.decode())

        self.assertNotIn('name="extra_romes_to_add"', rv.data.decode())
        self.assertNotIn('name="extra_romes_alternance_to_add"', rv.data.decode())

    def test_add_and_remove_romes_codes(self):

        # Do not try to send a real email.
        with mock.patch('labonneboite.web.contact_form.mail.send_mail'):

            romes_to_keep = ['D1507', 'D1106', 'D1214', 'D1101', 'D1502']
            romes_alternance_to_keep = ['D1101', 'D1105']
            extra_romes_to_add = ['M1802', 'M1803', 'M1805']
            extra_romes_alternance_to_add = ['M1805']

            form_data = {
                'romes_to_keep': romes_to_keep,
                'romes_alternance_to_keep': romes_alternance_to_keep,
                'extra_romes_to_add': extra_romes_to_add,
                'extra_romes_alternance_to_add': extra_romes_alternance_to_add,
            }

            # Add recruiter hidden identification info.
            form_data.update(self.recruiter_hidden_identification)

            url = self.url_for('contact_form.update_jobs_form')
            rv = self.app.post(url, data=form_data)

            # TOFIX: success must be an HTTP 302.
            # self.assertEqual(rv.status_code, 302)
            self.assertEqual(rv.status_code, 200)

            # An entry should have been created in `UpdateJobsRecruiterMessage`.
            msg = UpdateJobsRecruiterMessage.query.filter(
                    UpdateJobsRecruiterMessage.siret == self.office.siret,
                ).one()

            romes_to_add = set(romes_to_keep + extra_romes_to_add)
            self.assertCountEqual(romes_to_add, msg.romes_to_add.split(','))

            romes_alternance_to_add = set(romes_alternance_to_keep + extra_romes_alternance_to_add)
            self.assertCountEqual(romes_alternance_to_add, msg.romes_alternance_to_add.split(','))

            romes_to_remove = self.office.romes_codes - romes_to_add
            self.assertCountEqual(romes_to_remove, msg.romes_to_remove.split(','))

            romes_alternance_to_remove = self.office.romes_codes - romes_alternance_to_add
            self.assertCountEqual(romes_alternance_to_remove, msg.romes_alternance_to_remove.split(','))
