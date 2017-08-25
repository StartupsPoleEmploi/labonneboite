# coding: utf8
from flask import flash
from flask import Markup
from flask_admin.contrib.sqla import ModelView

from labonneboite.common import geocoding
from labonneboite.common.models import OfficeAdminExtraGeoLocation
from labonneboite.web.admin.forms import strip_filter
from labonneboite.web.admin.utils import datetime_format, AdminModelViewMixin


class OfficeAdminExtraGeoLocationModelView(AdminModelViewMixin, ModelView):
    """
    Admin interface for the `OfficeAdminExtraGeoLocation` model.
    http://flask-admin.readthedocs.io/en/latest/api/mod_model/
    """

    can_view_details = True
    column_searchable_list = ['siret']
    column_default_sort = ('date_created', True)
    page_size = 100

    column_list = [
        'siret',
        'codes',
        'reason',
        'date_created',
    ]

    column_details_list = [
        'siret',
        'codes',
        'geolocations',
        'reason',
        'created_by',
        'date_created',
        'updated_by',
        'date_updated',
    ]

    column_formatters = {
        'date_created': datetime_format,
        'date_updated': datetime_format,
        'codes': lambda view, context, model, name: model.codes_as_list(model.codes),
        'geolocations': lambda view, context, model, name: Markup(model.geolocations_as_html_links()),
    }


    column_labels = {
        'siret': u"Siret",
        'codes': u"Départements / Code postaux",
        'geolocations': u"Latitude/longitude",
        'reason': u"Raison",
        'date_created': u"Date de création",
        'date_updated': u"Date de modification",
        'created_by': u"Créé par",
        'updated_by': u"Modifié par",
    }

    column_descriptions = {
        'codes': u"Veuillez entrer un département ou un code postal par ligne.",
    }

    # `geolocations` is not included, it will be populated based on the `codes` content.
    form_columns = [
        'siret',
        'codes',
        'reason',
    ]

    form_args = {
        'codes': {
            'filters': [strip_filter],
        },
        'reason': {
            'filters': [strip_filter],
        },
    }

    def validate_form(self, form):
        is_valid = super(OfficeAdminExtraGeoLocationModelView, self).validate_form(form)
        if is_valid and form.data.get('codes'):
            for code in OfficeAdminExtraGeoLocation.codes_as_list(form.data['codes']):
                if len(code) not in [2, 5]:
                    msg = (u"`%s` n'est pas un code postal ou un numéro de département valide" % code)
                    flash(msg, 'error')
                    return False
                if OfficeAdminExtraGeoLocation.is_departement(code):
                    if not geocoding.get_all_lat_long_from_departement(code):
                        msg = (u"Impossible de trouver des latitude/longitude pour le département %s" % code)
                        flash(msg, 'error')
                        return False
                elif OfficeAdminExtraGeoLocation.is_zipcode(code):
                    lat_long = geocoding.get_lat_long_from_zipcode(code)
                    if lat_long == (None, None):
                        msg = (u"Impossible de trouver les latitude/longitude du code postal %s" % code)
                        flash(msg, 'error')
                        return False
        return is_valid
