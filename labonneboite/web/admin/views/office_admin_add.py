from flask import flash, url_for
from flask import Markup
from flask_admin.contrib.sqla import ModelView
from wtforms import validators

from labonneboite.common.models import OfficeAdminRemove
from labonneboite.conf import settings
from labonneboite.web.admin.forms import code_commune_validator, zip_code_validator
from labonneboite.web.admin.forms import nospace_filter, phone_validator, strip_filter, siret_validator
from labonneboite.web.admin.utils import datetime_format, AdminModelViewMixin, SelectForChoiceTypeField


class OfficeAdminAddModelView(AdminModelViewMixin, ModelView):
    """
    Admin interface for the `OfficeAdminAdd` model.
    http://flask-admin.readthedocs.io/en/latest/api/mod_model/
    """

    can_view_details = True
    column_searchable_list = ['siret', 'company_name', 'office_name']
    column_default_sort = ('date_created', True)
    page_size = 100

    column_list = [
        'siret',
        'company_name',
        'reason',
        'date_created',
        'date_updated',
    ]

    column_details_list = [
        'siret',
        'company_name',
        'office_name',
        'naf',
        'street_number',
        'street_name',
        'zipcode',
        'city_code',
        'email',
        'tel',
        'website',
        'flag_alternance',
        'flag_junior',
        'flag_senior',
        'flag_handicap',
        'departement',
        'headcount',
        'score',
        'score_alternance',
        'x',
        'y',
        'reason',
        'created_by',
        'date_created',
        'updated_by',
        'date_updated',
    ]

    column_formatters = {
        'date_created': datetime_format,
        'date_updated': datetime_format,
    }

    column_labels = {
        'siret': "Siret",
        'company_name': "Raison sociale",
        'office_name': "Enseigne",
        'naf': "Code NAF",
        'street_number': "Numero rue",
        'street_name': "Libellé rue",
        'zipcode': "Code postal",
        'city_code': "Code commune",
        'email': "Email",
        'tel': "Téléphone",
        'website': "Site web",
        'flag_alternance': "Drapeau alternance",
        'flag_junior': "Drapeau junior",
        'flag_senior': "Drapeau senior",
        'flag_handicap': "Drapeau handicap",
        'departement': "Département",
        'headcount': "Tranche effectif",
        'score': "Score",
        'score_alternance': "Score alternance",
        'x': "Longitude",
        'y': "Latitude",
        'reason': "Raison",
        'date_created': "Date de création",
        'date_updated': "Date de modification",
        'created_by': "Créé par",
        'updated_by': "Modifié par",
    }

    column_descriptions = {
        'reason': "Raison de l'ajout.",
        'score': "Valeur recommandée : entre 80 et 90",
        'score_alternance': "Valeur recommandée : entre 80 et 90",
    }

    form_columns = [
        'siret',
        'company_name',
        'office_name',
        'naf',
        'street_number',
        'street_name',
        'zipcode',
        'city_code',
        'departement',
        'email',
        'tel',
        'website',
        'flag_alternance',
        'flag_junior',
        'flag_senior',
        'flag_handicap',
        'headcount',
        'score',
        'score_alternance',
        'y',
        'x',
        'reason',
    ]

    form_overrides = {
        'headcount': SelectForChoiceTypeField,
    }

    form_args = {
        'siret': {
            'filters': [strip_filter, nospace_filter],
            'validators': [siret_validator],
        },

        'company_name': {
            'filters': [strip_filter],
        },
        'office_name': {
            'filters': [strip_filter],
        },
        'naf': {
            'filters': [strip_filter, nospace_filter],
        },
        'street_number': {
            'filters': [strip_filter, nospace_filter],
        },
        'street_name': {
            'filters': [strip_filter],
        },
        'zipcode': {
            'filters': [strip_filter, nospace_filter],
            'validators': [zip_code_validator],
        },
        'city_code': {
            'filters': [strip_filter, nospace_filter],
            'validators': [code_commune_validator],
        },
        'departement': {
            'filters': [strip_filter, nospace_filter],
        },
        'email': {
            'validators': [validators.optional(), validators.Email()],
        },
        'tel': {
            'filters': [strip_filter, nospace_filter],
            'validators': [validators.optional(), phone_validator],
        },
        'website': {
            'filters': [strip_filter],
            'validators': [validators.optional(), validators.URL()],
        },
        'headcount': {
            'choices': settings.HEADCOUNT_INSEE_CHOICES,
        },
        'score': {
            'validators': [validators.NumberRange(min=0, max=100)],
        },
        'score_alternance': {
            'validators': [validators.NumberRange(min=0, max=100)],
        },
        'reason': {
            'filters': [strip_filter],
        },
        'x': {
            'filters': [strip_filter, nospace_filter],
            'validators': [validators.required()],
        },
        'y': {
            'filters': [strip_filter, nospace_filter],
            'validators': [validators.required()],
        },
    }

    def validate_form(self, form):
        """
        Ensure that the office to add does not already exist in `OfficeAdminRemove`.
        """
        is_valid = super(OfficeAdminAddModelView, self).validate_form(form)
        if is_valid and 'siret' in list(form.data.keys()):
            office_to_remove = OfficeAdminRemove.query.filter_by(siret=form.data['siret']).first()
            if office_to_remove:
                # Use the link of the list view with a filter on the `siret`, because
                # the delete button is missing on the edit and/or detail view.
                # https://github.com/flask-admin/flask-admin/issues/1327
                office_to_remove_url = url_for('officeadminremove.index_view', search=office_to_remove.siret)
                msg = (
                    "Vous ne pouvez pas ajouter cette entreprise car elle existe déjà dans la liste "
                    "<b>Supprimer une entreprise</b>.<br>Vous devez d'abord "
                    '<a target="_blank" href="{url}">la supprimer de cette liste</a>.'.format(url=office_to_remove_url)
                )
                flash(Markup(msg), 'error')
                return False
        return is_valid
