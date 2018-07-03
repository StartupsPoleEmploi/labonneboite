# coding: utf8
from flask import flash, request, url_for
from flask import Markup
from flask_admin.contrib.sqla import ModelView
from wtforms import validators

from labonneboite.common.models import OfficeAdminAdd, OfficeAdminRemove
from labonneboite.web.admin.forms import nospace_filter, phone_validator, strip_filter, siret_validator
from labonneboite.web.admin.utils import datetime_format, AdminModelViewMixin, SelectForChoiceTypeField


class OfficeAdminRemoveModelView(AdminModelViewMixin, ModelView):
    """
    Admin interface for the `OfficeAdminRemove` model.
    http://flask-admin.readthedocs.io/en/latest/api/mod_model/
    """

    can_view_details = True
    column_searchable_list = ['siret', 'name']
    column_default_sort = ('date_created', True)
    page_size = 100

    column_list = [
        'siret',
        'name',
        'reason',
        'date_created',
        'date_updated',
        'date_follow_up_phone_call',
        'initiative',
    ]

    column_details_list = [
        'siret',
        'name',
        'initiative',
        'date_follow_up_phone_call',
        'requested_by_email',
        'requested_by_first_name',
        'requested_by_last_name',
        'requested_by_phone',
        'reason',
        'created_by',
        'date_created',
        'updated_by',
        'date_updated',
    ]

    column_formatters = {
        'date_created': datetime_format,
        'date_follow_up_phone_call': datetime_format,
        'date_updated': datetime_format,
    }

    column_labels = {
        'siret': "Siret",
        'name': "Nom de l'entreprise",
        'reason': "Raison",
        'initiative': "À l'initiative de",
        'date_follow_up_phone_call': "Date de rappel",
        'requested_by_email': "Email",
        'requested_by_first_name': "Prénom",
        'requested_by_last_name': "Nom",
        'requested_by_phone': "Téléphone",
        'date_created': "Date de création",
        'date_updated': "Date de modification",
        'created_by': "Créé par",
        'updated_by': "Modifié par",
    }

    column_descriptions = {
        'initiative': "Permet de préciser qui est à l'initiative de la suppression.",
        'requested_by_email': "Email de la personne qui demande la suppression.",
        'requested_by_first_name': "Prénom de la personne qui demande la suppression.",
        'requested_by_last_name': "Nom de la personne qui demande la suppression.",
        'requested_by_phone': "Téléphone de la personne qui demande la suppression.",
        'reason': "Raison de la suppression.",
        'date_follow_up_phone_call': "Date de rappel de l'employeur",
    }

    form_columns = [
        'siret',
        'name',
        'reason',
        'initiative',
        'date_follow_up_phone_call',
        'requested_by_email',
        'requested_by_first_name',
        'requested_by_last_name',
        'requested_by_phone',
    ]

    form_overrides = {
        'initiative': SelectForChoiceTypeField,
    }

    form_args = {
        'siret': {
            'filters': [strip_filter, nospace_filter],
            'validators': [siret_validator],
        },
        'name': {
            'filters': [strip_filter],
        },
        'reason': {
            'filters': [strip_filter],
        },
        'initiative': {
            'choices': OfficeAdminRemove.INITIATIVE_CHOICES,
        },
        'requested_by_email': {
            'validators': [validators.optional(), validators.Email()],
        },
        'requested_by_first_name': {
            'filters': [strip_filter],
        },
        'requested_by_last_name': {
            'filters': [strip_filter],
        },
        'requested_by_phone': {
            'filters': [strip_filter, nospace_filter],
            'validators': [validators.optional(), phone_validator],
        },
    }

    def create_form(self):
        form = super(OfficeAdminRemoveModelView, self).create_form()
        if 'siret' in request.args:
            form.siret.data = request.args['siret']
        if 'name' in request.args:
            form.name.data = request.args['name']
        if 'requested_by_email' in request.args:
            form.requested_by_email.data = request.args['requested_by_email']
        if 'requested_by_first_name' in request.args:
            form.requested_by_first_name.data = request.args['requested_by_first_name']
        if 'requested_by_last_name' in request.args:
            form.requested_by_last_name.data = request.args['requested_by_last_name']
        if 'requested_by_phone' in request.args:
            form.requested_by_phone.data = request.args['requested_by_phone']
        if 'reason' in request.args:
            form.reason.data = request.args['reason']

        return form

    def validate_form(self, form):
        """
        Ensure that the office to remove does not already exist in `OfficeAdminAdd`.
        """
        is_valid = super(OfficeAdminRemoveModelView, self).validate_form(form)
        if is_valid and 'siret' in list(form.data.keys()):
            office_to_add = OfficeAdminAdd.query.filter_by(siret=form.data['siret']).first()
            if office_to_add:
                # Use the link of the list view with a filter on the `siret`, because
                # the delete button is missing on the edit and/or detail view.
                # https://github.com/flask-admin/flask-admin/issues/1327
                office_to_add_url = url_for('officeadminadd.index_view', search=office_to_add.siret)
                msg = (
                    "Vous ne pouvez pas supprimer cette entreprise car elle existe déjà dans la liste "
                    "<b>Ajouter une entreprise</b>.<br>Vous devez d'abord "
                    '<a target="_blank" href="{url}">la supprimer de cette liste</a>.'.format(url=office_to_add_url)
                )
                flash(Markup(msg), 'error')
                return False
        return is_valid
