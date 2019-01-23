# coding: utf8
from unittest import mock
from flask import request

from labonneboite.tests.test_base import DatabaseTest
from labonneboite.web.contact_form import forms, mail
from labonneboite.common import models
from labonneboite.web.app import app

# We use request.form because some ROME codes can be added manually on the client side
REQUEST_FORM = [
    ('D1507', ['lbb', 'lba']),
    ('D1106', ['lbb']),
    ('D1505', ['lba']),
    # Added job on the client side, not related to office NAF
    ('E1102', ['lbb', 'lba']),
]


# Common helpers
def create_other_form(overrides=None):
    overrides = overrides or {}

    form = forms.OfficeOtherRequestForm(
        comment="Bonjour à tous",
        **get_form_common_fields(overrides)
    )
    return form


def create_update_coordinates_form(overrides=None):
    overrides = overrides or {}

    form = forms.OfficeUpdateCoordinatesForm(
        new_contact_mode=overrides.get('new_contact_mode', 'office'),
        new_website=overrides.get('new_website', 'http://exemple.com'),
        new_email=overrides.get('new_email', 'exemple@domaine.com'),
        new_phone=overrides.get('new_phone', '01 77 86 39 49'),
        new_email_alternance=overrides.get('new_email_alternance', 'exemple-alternance@domaine.com'),
        new_phone_alternance=overrides.get('new_phone_alternance', '02 77 86 39 49'),
        social_network=overrides.get('social_network', 'https://www.facebook.com/poleemploi/'),
        **get_form_common_fields(overrides)
    )
    return form


def create_update_jobs_form(overrides=None):
    overrides = overrides or {}

    form = forms.OfficeUpdateJobsForm(
        **get_form_common_fields(overrides)
    )
    return form


def create_remove_form(overrides=None):
    overrides = overrides or {}
    form = forms.OfficeRemoveForm(
        remove_lbb=overrides.get('remove_lbb', True),
        remove_lba=overrides.get('remove_lba', True),
        **get_form_common_fields(overrides)
    )
    return form

def get_form_common_fields(overrides):
    overrides = overrides or {}
    return {
        'siret': overrides.get('siret', '00000000000008'),
        'last_name': overrides.get('last_name', 'Bonaparte'),
        'first_name': overrides.get('first_name', 'Napoléon'),
        'phone': overrides.get('phone', '0123456789'),
        'email': overrides.get('email', 'bonaparte@napoleon.fr'),
    }


def create_office():
    office = models.Office(
        siret='00000000000008',
        naf='4711B',
        office_name="Test company",
        company_name="Test company",
        city_code=44109,
        zipcode=44000,
        departement=44,
    )
    office.save()

class FormContactMailTest(DatabaseTest):
    def test_other_form(self):
        with app.app_context(), self.test_request_context:
            form = create_other_form()
            mail_content = mail.generate_other_mail(form, models.OtherRecruiterMessage.create_from_form(form))

            actionLineExpected = 'Action : {}'.format(mail.compute_action_name(form))

            self.assertIn(actionLineExpected, mail_content)
            self.assertIn('Siret : 00000000000008', mail_content)
            self.assertIn('Prénom : Napoléon', mail_content)
            self.assertIn('Nom : Bonaparte', mail_content)
            self.assertIn('E-mail : bonaparte@napoleon.fr', mail_content)
            self.assertIn('Téléphone : 0123456789', mail_content)


    def test_remove_form(self):
        answers = [
            ('oui', True),
            ('non', False),
        ]

        # All possibilities
        for expected1, answer1 in answers:
            for expected2, answer2 in answers:
                with app.app_context(), self.test_request_context:
                    form = create_remove_form({'remove_lbb': answer1, 'remove_lba': answer2})
                    mail_content = mail.generate_delete_mail(form, models.RemoveRecruiterMessage.create_from_form(form))

                    lbbExpected = 'Suppression de LBB : {}'.format(expected1)
                    lbaExpected = 'Suppression de LBA : {}'.format(expected2)

                    self.assertIn(lbbExpected, mail_content)
                    self.assertIn(lbaExpected, mail_content)


    def test_new_coordinates(self):
        with app.app_context(), self.test_request_context:
            form = create_update_coordinates_form()
            recruiter_message = models.UpdateCoordinatesRecruiterMessage.create_from_form(form)
            mail_content = mail.generate_update_coordinates_mail(form, recruiter_message)

            contact_mode_label = forms.CONTACT_MODES_LABELS.get(form.new_contact_mode, '')
            contact_mode_expected = 'Mode de contact à privilégier : {}'.format(contact_mode_label)

            self.assertIn('Nouveau site Internet : http://exemple.com', mail_content)
            self.assertIn('Nouvel e-mail recruteur : exemple@domaine.com', mail_content)
            self.assertIn('Nouveau téléphone : 01 77 86 39 49', mail_content)
            self.assertIn(contact_mode_expected, mail_content)
            self.assertIn('Nouvel email recruteur spécifique alternance : exemple-alternance@domaine.com', mail_content)
            self.assertIn('Nouveau téléphone spécifique alternance : 02 77 86 39 49', mail_content)
            self.assertIn('Réseau social : https://www.facebook.com/poleemploi/', mail_content)


    def test_new_jobs(self):
        with app.test_request_context():
            # Make request.form mutable to make it mockable
            request.form = request.form.to_dict()

            with mock.patch('flask.request.form', REQUEST_FORM):
                create_office()

                form = create_update_jobs_form()
                recruiter_message = models.UpdateJobsRecruiterMessage.create_from_form(form)
                mail_content = mail.generate_update_jobs_mail(form, recruiter_message)

                self.assertIn(
                    'Romes à ajouter LBB : <ul><li>Ecriture d\'ouvrages, de livres (E1102)</li></ul>',
                    mail_content
                )
                self.assertIn(
                    'Romes à ajouter LBA : <ul><li>Ecriture d\'ouvrages, de livres (E1102)</li></ul>',
                    mail_content
                )


class CreateFormContactDatabase(DatabaseTest):
    def test_save_other_form(self):
        with app.app_context(), self.test_request_context:
            recruiter_message = models.OtherRecruiterMessage.create_from_form(create_other_form())

            self.assertEqual('00000000000008', recruiter_message.siret)
            self.assertEqual('Napoléon', recruiter_message.requested_by_first_name)
            self.assertEqual('Bonaparte', recruiter_message.requested_by_last_name)
            self.assertEqual('bonaparte@napoleon.fr', recruiter_message.requested_by_email)
            self.assertEqual('0123456789', recruiter_message.requested_by_phone)
            self.assertEqual('Bonjour à tous', recruiter_message.comment)


    def test_save_remove_form(self):
        with app.app_context(), self.test_request_context:
            recruiter_message = models.RemoveRecruiterMessage.create_from_form(create_remove_form())

            self.assertTrue(recruiter_message.remove_lbb)
            self.assertTrue(recruiter_message.remove_lba)


    def test_save_update_coordinates_form(self):
        with app.app_context(), self.test_request_context:
            recruiter_message = models.UpdateCoordinatesRecruiterMessage.create_from_form(create_update_coordinates_form())

            self.assertEqual('http://exemple.com', recruiter_message.new_website)
            self.assertEqual('exemple@domaine.com', recruiter_message.new_email)
            self.assertEqual('01 77 86 39 49', recruiter_message.new_phone)
            self.assertEqual('office', recruiter_message.contact_mode)
            self.assertEqual('exemple-alternance@domaine.com', recruiter_message.new_email_alternance)
            self.assertEqual('02 77 86 39 49', recruiter_message.new_phone_alternance)
            self.assertEqual('https://www.facebook.com/poleemploi/', recruiter_message.social_network)


    def test_save_update_jobs_form(self):
        with app.test_request_context():
            # Make request.form mutable to make it mockable
            request.form = request.form.to_dict()

            with mock.patch('flask.request.form', REQUEST_FORM):
                create_office()
                recruiter_message = models.UpdateJobsRecruiterMessage.create_from_form(create_update_jobs_form())

                self.assertIn('D1505', recruiter_message.romes_to_remove)
                self.assertIn('D1101', recruiter_message.romes_to_remove)

                self.assertIn('D1106', recruiter_message.romes_alternance_to_remove)
                self.assertIn('D1101', recruiter_message.romes_alternance_to_remove)

                self.assertIn('E1102', recruiter_message.romes_to_add)
                self.assertIn('E1102', recruiter_message.romes_alternance_to_add)
