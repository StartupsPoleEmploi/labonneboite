from flask import request
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import BaseForm
from wtforms import validators


from labonneboite.common.models import OfficeAdminAdd, OfficeAdminRemove, OfficeAdminUpdate
from labonneboite.web.admin.forms import nospace_filter, phone_validator, strip_filter, siret_validator
from labonneboite.web.admin.utils import datetime_format, AdminModelViewMixin, SelectForChoiceTypeField
from labonneboite.scripts import create_index


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

    def _remove_office_admin_update(self, offices_to_update: OfficeAdminUpdate) -> None:
        """
        Remove offices to update if all offices are present in OfficeAdminRemove
        """

        sirets = OfficeAdminUpdate.as_list(offices_to_update.sirets)
        are_all_in_remove_table = True
        for siret in sirets:
            if not OfficeAdminRemove.query.filter_by(siret=siret).first():
                are_all_in_remove_table = False
                break
        if are_all_in_remove_table:
            offices_to_update.delete()

    def after_model_change(self, form: BaseForm,
                           model: OfficeAdminRemove,
                           is_created: bool) -> None:
        """
        Remove office in ElacticSearch and MySQL DB and remove it from
        OfficeAdminAdd and OfficeAdminUpdate if it exists in such DB
        """

        # remove office in OfficeAdminAdd
        OfficeAdminAdd.query.filter_by(siret=model.siret).delete()

        # remove office if it exists in OfficeAdminUpdate
        offices_to_update = OfficeAdminUpdate.query.\
            filter(OfficeAdminUpdate.sirets.contains(model.siret)).first()
        if offices_to_update:
            self._remove_office_admin_update(offices_to_update)

        create_index.remove_individual_office(model.siret)
