# coding: utf8
from flask import flash
from flask import Markup
from flask_admin.contrib.sqla import ModelView
from wtforms import validators

from labonneboite.common import mapping as mapping_util
from labonneboite.common.models import Office, OfficeAdminUpdate
from labonneboite.web.admin.forms import nospace_filter, phone_validator, strip_filter, siret_validator
from labonneboite.web.admin.utils import datetime_format, AdminModelViewMixin
from labonneboite.conf import settings


class OfficeAdminUpdateModelView(AdminModelViewMixin, ModelView):
    """
    Admin interface for the `OfficeAdminUpdate` model.
    http://flask-admin.readthedocs.io/en/latest/api/mod_model/
    """

    can_delete = False
    can_view_details = True
    column_searchable_list = ['siret', 'name']
    column_default_sort = ('date_created', True)
    page_size = 100

    column_list = [
        'siret',
        'name',
        'reason',
        'date_created',
    ]

    column_details_list = [
        'siret',
        'name',
        'boost',
        'romes_to_boost',
        'romes_to_remove',
        'nafs_to_add',
        'new_email',
        'email_alternance',
        'new_phone',
        'new_website',
        'remove_email',
        'remove_phone',
        'remove_website',
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
        'date_updated': datetime_format,
        'romes_to_boost': lambda view, context, model, name: Markup(model.romes_as_html(model.romes_to_boost)),
        'romes_to_remove': lambda view, context, model, name: Markup(model.romes_as_html(model.romes_to_remove)),
    }

    column_labels = {
        'siret': u"Siret",
        'name': u"Nom de l'entreprise",
        'reason': u"Raison",
        'boost': u"Booster le score",
        'romes_to_boost': u"Limiter le boosting du score à certain codes ROME uniquement",
        'romes_to_remove': u"Retirer des codes ROME associés à une entreprise",
        'nafs_to_add': u"Ajouter un ou plusieurs NAF à une entreprise",
        'new_email': u"Nouvel email",
        'email_alternance': u"Email dédié à l'alternance",
        'new_phone': u"Nouveau téléphone",
        'new_website': u"Nouveau site web",
        'remove_email': u"Ne pas afficher l'email",
        'remove_phone': u"Ne pas afficher le téléphone",
        'remove_website': u"Ne pas afficher le site web",
        'requested_by_email': u"Email",
        'requested_by_first_name': u"Prénom",
        'requested_by_last_name': u"Nom",
        'requested_by_phone': u"Téléphone",
        'date_created': u"Date de création",
        'date_updated': u"Date de modification",
        'created_by': u"Créé par",
        'updated_by': u"Modifié par",
    }

    column_descriptions = {
        'requested_by_email': u"Email de la personne qui demande la suppression.",
        'requested_by_first_name': u"Prénom de la personne qui demande la suppression.",
        'requested_by_last_name': u"Nom de la personne qui demande la suppression.",
        'requested_by_phone': u"Téléphone de la personne qui demande la suppression.",
        'boost': u"Cocher cette case pour forcer le positionnement en tête des résultats",
        'romes_to_boost': Markup(
            u"Veuillez entrer un ROME par ligne."
            u"<br>"
            u"Si ce champ est renseigné, le score sera forcé uniquement pour le(s) ROME spécifié(s)."
            u"<br>"
            u"<a href=\"/data/romes-for-siret\" target=\"_blank\">Trouver les ROME pour un SIRET</a>."
        ),
        'nafs_to_add': Markup(
            u"Veuillez entrer un NAF par ligne."
        ),
        'romes_to_remove': Markup(
            u"Veuillez entrer un ROME par ligne."
            u"<br>"
            u"Si ce champ est renseigné, le(s) ROME spécifié(s) ne seront plus associés à cette entreprise."
            u"<br>"
            u"<a href=\"/data/romes-for-siret\" target=\"_blank\">Trouver les ROME pour un SIRET</a>."
        ),
        'new_email': u"Laisser vide s'il n'y a pas de modification à apporter",
        'new_phone': u"Laisser vide s'il n'y a pas de modification à apporter",
        'new_website': u"Laisser vide s'il n'y a pas de modification à apporter",
        'remove_email': u"Cocher cette case pour supprimer l'email",
        'remove_phone': u"Cocher cette case pour supprimer le téléphone",
        'remove_website': u"Cocher cette case pour supprimer le site web",
        'reason': u"Raison de la modification.",
    }

    form_columns = [
        'siret',
        'name',
        'boost',
        'romes_to_boost',
        'romes_to_remove',
        'nafs_to_add',
        'new_email',
        'email_alternance',
        'new_phone',
        'new_website',
        'remove_email',
        'remove_phone',
        'remove_website',
        'requested_by_email',
        'requested_by_first_name',
        'requested_by_last_name',
        'requested_by_phone',
        'reason',
    ]

    form_args = {
        'siret': {
            'filters': [strip_filter, nospace_filter],
            'validators': [siret_validator],
        },
        'name': {
            'filters': [strip_filter],
        },
        'romes_to_boost': {
            'filters': [strip_filter],
        },
        'romes_to_remove': {
            'filters': [strip_filter],
        },
        'nafs_to_add': {
            'filters': [strip_filter],
        },
        'new_email': {
            'validators': [validators.optional(), validators.Email()],
        },
        'email_alternance': {
            'validators': [validators.optional(), validators.Email()],
        },
        'new_phone': {
            'filters': [strip_filter, nospace_filter],
            'validators': [validators.optional(), phone_validator],
        },
        'new_website': {
            'filters': [strip_filter],
            'validators': [validators.optional(), validators.URL()],
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
        'reason': {
            'filters': [strip_filter],
        },
    }

    def validate_form(self, form):
        is_valid = super(OfficeAdminUpdateModelView, self).validate_form(form)

        # Codes ROMES to boost or to add
        if is_valid and form.data.get('romes_to_boost'):

            romes_to_boost = form.data.get('romes_to_boost')

            if not form.data.get('boost'):
                msg = u"Vous devez cocher la case `Booster le score`."
                flash(msg, 'error')
                return False

            office_to_update = Office.query.filter_by(siret=form.data['siret']).first()
            if not office_to_update:
                msg = u"Le siret `%s` n'est pas présent sur LBB." % form.data['siret']
                flash(msg, 'error')
                return False

            for rome in OfficeAdminUpdate.as_list(romes_to_boost):
                if not mapping_util.rome_is_valid(rome):
                    msg = (
                        u"`%s` n'est pas un code ROME valide."
                        u"<br>"
                        u"Assurez-vous de ne saisir qu'un élément par ligne."
                        % rome
                    )
                    flash(Markup(msg), 'error')
                    return False

        # Codes ROMES to remove
        if is_valid and form.data.get('romes_to_remove'):
            romes_to_remove = form.data.get('romes_to_remove')

            office_to_update = Office.query.filter_by(siret=form.data['siret']).first()
            if not office_to_update:
                msg = u"Le siret `%s` n'est pas présent sur LBB." % form.data['siret']
                flash(msg, 'error')
                return False

            office_romes = [item.code for item in mapping_util.romes_for_naf(office_to_update.naf)]
            for rome in OfficeAdminUpdate.as_list(romes_to_remove):

                if not mapping_util.rome_is_valid(rome):
                    msg = (
                        u"`%s` n'est pas un code ROME valide."
                        u"<br>"
                        u"Assurez-vous de ne saisir qu'un élément par ligne."
                        % rome
                    )
                    flash(Markup(msg), 'error')
                    return False

                if rome not in office_romes:
                    msg = u"`%s` n'est pas un code ROME lié au NAF de cette entreprise." % rome
                    flash(msg, 'error')
                    return False

        # Codes NAF to add
        if is_valid and form.data.get('nafs_to_add'):
            nafs_to_add = form.data.get('nafs_to_add')

            office_to_update = Office.query.filter_by(siret=form.data['siret']).first()
            if not office_to_update:
                msg = u"Le siret `%s` n'est pas présent sur LBB." % form.data['siret']
                flash(msg, 'error')
                return False

            for naf in OfficeAdminUpdate.as_list(nafs_to_add):
                if naf not in settings.NAF_CODES:
                    msg = u"`%s` n'est pas un code NAF valide." % naf
                    flash(msg, 'error')
                    return False
                if naf == office_to_update.naf:
                    msg = u"Le NAF `%s` est déjà associé à cette entreprise." % naf
                    flash(msg, 'error')
                    return False

        return is_valid
