# coding: utf8
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
        'siret': u"Siret",
        'company_name': u"Raison sociale",
        'office_name': u"Enseigne",
        'naf': u"Code NAF",
        'street_number': u"Numero rue",
        'street_name': u"Libellé rue",
        'zipcode': u"Code postal",
        'city_code': u"Code commune",
        'email': u"Email",
        'tel': u"Téléphone",
        'website': u"Site web",
        'flag_alternance': u"Drapeau alternance",
        'flag_junior': u"Drapeau junior",
        'flag_senior': u"Drapeau senior",
        'flag_handicap': u"Drapeau handicap",
        'departement': u"Département",
        'headcount': u"Tranche effectif",
        'score': u"Score",
        'x': u"Longitude",
        'y': u"Latitude",
        'reason': u"Raison",
        'date_created': u"Date de création",
        'date_updated': u"Date de modification",
        'created_by': u"Créé par",
        'updated_by': u"Modifié par",
    }

    column_descriptions = {
        'reason': u"Raison de l'ajout.",
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
        'reason': {
            'filters': [strip_filter],
        },
    }

    def validate_form(self, form):
        """
        Ensure that the office to add does not already exist in `OfficeAdminRemove`.
        """
        is_valid = super(OfficeAdminAddModelView, self).validate_form(form)
        if is_valid:
            office_to_remove = OfficeAdminRemove.query.filter_by(siret=form.data['siret']).first()
            if office_to_remove:
                # Use the link of the list view with a filter on the `siret`, because
                # the delete button is missing on the edit and/or detail view.
                # https://github.com/flask-admin/flask-admin/issues/1327
                office_to_remove_url = url_for('officeadminremove.index_view', search=office_to_remove.siret)
                msg = (
                    u"Vous ne pouvez pas ajouter cette entreprise car elle existe déjà dans la liste "
                    u"<b>Supprimer une entreprise</b>.<br>Vous devez d'abord "
                    u'<a target="_blank" href="{url}">la supprimer de cette liste</a>.'.format(url=office_to_remove_url)
                )
                flash(Markup(msg), 'error')
                return False
        return is_valid
