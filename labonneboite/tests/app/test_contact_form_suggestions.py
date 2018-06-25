# coding: utf8
import re
import urllib.request, urllib.parse, urllib.error
import urllib.parse

from flask import url_for

from wtforms import StringField, SelectField, TextAreaField
from wtforms.fields.html5 import EmailField, TelField

from labonneboite.common.models import Office, OfficeAdminAdd, OfficeAdminRemove, OfficeAdminUpdate
from labonneboite.tests.scripts.test_create_index import CreateIndexBaseTest
from labonneboite.web.office.views import make_save_suggestion
from labonneboite.web.office.forms import OfficeRemovalForm

class SaveSuggestionsTest(CreateIndexBaseTest):
    # No company and no OfficeAdminRemove
    def test_no_company_found(self):
        with self.test_request_context:
            # Create form
            form = OfficeRemovalForm()
            form.siret = StringField('Siret')
            form.siret.data = "Invalid"

            self.assertEqual('Aucune entreprise trouvée avec le siret Invalid', make_save_suggestion(form))

    # No company due to an OfficeAdminRemove
    def test_no_company_and_remove_office(self):
        with self.test_request_context:
            # Create OfficeAdminRemove
            office_to_remove = OfficeAdminRemove(
                id=1,
                siret='12345678901234',
                name=self.office1.company_name,
                reason="N/A",
                initiative='office',
            )
            office_to_remove.save(commit=True)

            # Create form
            form = OfficeRemovalForm()
            form.siret = StringField('Siret')
            form.siret.data = "12345678901234"

            url = url_for("officeadminremove.edit_view", id=1, _external=True)
            expected_text = "Entreprise retirée via Save : <a href='%s'>Voir la fiche de suppression</a>" % url

            self.assertEqual(expected_text, make_save_suggestion(form))

    # Company exists due to OfficeAdminAdd
    def test_company_and_office_admin_add(self):
        with self.test_request_context:
            # Create OfficeAdminAdd
            office_admin_add = OfficeAdminAdd(
                id=1,
                siret="78548035101646",
                company_name="SUPERMARCHES MATCH",
                office_name="SUPERMARCHES MATCH",
                naf="4711D",
                street_number="45",
                street_name="AVENUE ANDRE MALRAUX",
                city_code="57463",
                zipcode="57000",
                email="supermarche@match.com",
                tel="0387787878",
                website="http://www.supermarchesmatch.fr",
                flag_alternance=0,
                flag_junior=0,
                flag_senior=0,
                flag_handicap=0,
                departement="57",
                headcount="12",
                score=90,
                x=6.17952,
                y=49.1044,
                reason="Demande de mise en avant",
            )
            office_admin_add.save(commit=True)

            # Create form
            form = OfficeRemovalForm()
            form.siret = StringField('Siret')
            form.siret.data = "78548035101646"

            url = url_for("officeadminadd.edit_view", id=office_admin_add.id, _external=True)
            expected_text = "Entreprise créée via Save : <a href='%s'>Voir la fiche d'ajout</a>" % url

            self.assertEqual(expected_text, make_save_suggestion(form))

    # Company exists and has been modified by OfficeAdminUpdate
    def test_company_and_office_admin_update(self):
        with self.test_request_context:
            # Create OfficeAdminUpdate
            office_to_update = OfficeAdminUpdate(
                id=1,
                sirets="78548035101646",
                name="SUPERMARCHES MATCH"
            )
            office_to_update.save(commit=True)

            # Create form
            form = OfficeRemovalForm()
            form.siret = StringField('Siret')
            form.siret.data = "78548035101646"

            url = url_for("officeadminupdate.edit_view", id=office_to_update.id, _external=True)
            expected_text = "Entreprise modifiée via Save : <a href='%s'>Voir la fiche de modification</a>" % url

            self.assertEqual(expected_text, make_save_suggestion(form))

    # Company exists and no OfficeAdmin found and the user ask for a delete
    def test_company_and_no_office_admin_and_ask_remove(self):
        with self.test_request_context:
            office = self.create_office()
            office.save()

            form = self.create_form('enlever')
            expected_parameters = self.create_params(form)
            expected_text = r" Une suppression a été demandée : <a href='(?P<url>.*)'>Créer une fiche de suppression</a>"
            suggestion = make_save_suggestion(form)

            self.assertRegex(suggestion, expected_text)
            match = re.match(expected_text, suggestion)
            url, querystring = urllib.parse.splitquery(match.groupdict()['url'])
            parameters = dict(urllib.parse.parse_qsl(querystring))

            self.assertEqual(url_for("officeadminremove.create_view", _external=True), url)
            self.assertEqual(expected_parameters, parameters)

    # Company exists and no OfficeAdmin found : suggest officeAdminAdd
    def test_company_and_no_office_admin(self):
        with self.test_request_context:
            office = self.create_office()
            office.save()

            form = self.create_form()
            expected_parameters = self.create_params(form)
            expected_text = r"Entreprise non modifiée via Save : <a href='(?P<url>.*)'>Créer une fiche de modification</a>"
            suggestion = make_save_suggestion(form)

            self.assertRegex(suggestion, expected_text)
            match = re.match(expected_text, suggestion)
            url, querystring = urllib.parse.splitquery(match.groupdict()['url'])
            parameters = dict(urllib.parse.parse_qsl(querystring))

            self.assertEqual(url_for("officeadminupdate.create_view", _external=True), url)
            self.assertEqual(expected_parameters, parameters)


    def test_unicode_reason_does_not_raise_error(self):
        with self.test_request_context:
            office = self.create_office()
            office.save()
            form = self.create_form()
            form.comment.data = 'I❤️ unicode'

            make_save_suggestion(form)

    # Create a valid
    def create_form(self, action=''):
        form = OfficeRemovalForm()
        form.siret = StringField('Siret')
        form.action = SelectField('Je souhaite *')
        form.name = StringField("Nom de l'entreprise")
        form.email = EmailField('Email')
        form.first_name = StringField('Prénom')
        form.last_name = StringField('Nom')
        form.phone = TelField('Téléphone')
        form.comment = TextAreaField('Raison')

        # Set form values
        form.siret.data = "78548035101648"
        form.name.data = "Test company"
        form.email.data = "test@mail.com"
        form.first_name.data = "firstName"
        form.last_name.data = "lastName"
        form.phone.data = "010000000"
        form.comment.data = "Raison"
        form.action.data = action

        return form

    def create_params(self, form):
        return {
            'siret': form.siret.data,
            'name': form.name.data,
            'requested_by_email': form.email.data,
            'requested_by_first_name': form.first_name.data,
            'requested_by_last_name': form.last_name.data,
            'requested_by_phone': form.phone.data,
            'reason': form.comment.data,
        }

    def create_office(self):
        return Office(
            siret="78548035101648",
            company_name="Test company",
            office_name="Test company",
            naf="4711D",
            street_number="45",
            street_name="AVENUE ANDRE MALRAUX",
            city_code="57463",
            zipcode="57000",
            email="test@match.com",
            tel="0387787878",
            website="http://www.dummy.fr",
            flag_alternance=0,
            flag_junior=0,
            flag_senior=0,
            flag_handicap=0,
            departement="57",
            headcount="12",
            score=90,
            x=6.17952,
            y=49.1044,
        )
