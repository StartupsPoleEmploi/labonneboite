# coding: utf8
from flask import flash, request
from flask import Markup
from flask_admin.contrib.sqla import ModelView
from wtforms import validators

from labonneboite.common import mapping as mapping_util
from labonneboite.common.models import Office, OfficeAdminUpdate
from labonneboite.common.siret import is_siret
from labonneboite.web.admin.forms import nospace_filter, phone_validator, strip_filter, siret_validator
from labonneboite.web.admin.utils import datetime_format, AdminModelViewMixin
from labonneboite.conf import settings

class RomeToRemoveException(Exception):
    pass

class RomeToBoostException(Exception):
    pass

class InvalidRome(Exception):
    pass


class OfficeAdminUpdateModelView(AdminModelViewMixin, ModelView):
    """
    Admin interface for the `OfficeAdminUpdate` model.
    http://flask-admin.readthedocs.io/en/latest/api/mod_model/
    """

    can_delete = False
    can_view_details = True
    column_searchable_list = ['sirets', 'name']
    column_default_sort = ('date_created', True)
    page_size = 100

    column_list = [
        'sirets',
        'name',
        'reason',
        'date_created',
    ]

    column_details_list = [
        'sirets',
        'name',
        'boost',
        'romes_to_boost',
        'boost_alternance',
        'romes_alternance_to_boost',
        'romes_to_remove',
        'nafs_to_add',
        'new_email',
        'email_alternance',
        'new_phone',
        'new_website',
        'remove_email',
        'remove_phone',
        'remove_website',
        'remove_flag_alternance',
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
        'sirets': u"Sirets",
        'name': u"Nom de l'entreprise",
        'reason': u"Raison",
        'boost': u"Booster le score - LBB",
        'romes_to_boost': u"Limiter le boosting du score à certain codes ROME uniquement - LBB",
        'romes_to_remove': u"Retirer des codes ROME associés à une entreprise - LBB",
        'boost_alternance': u"Booster le score - Alternance",
        'romes_alternance_to_boost': u"Limiter le boosting du score à certain codes ROME uniquement - Alternance",
        'romes_alternance_to_remove': u"Retirer des codes ROME associés à une entreprise - Alternance",
        'nafs_to_add': u"Ajouter un ou plusieurs NAF à une entreprise",
        'new_email': u"Nouvel email",
        'email_alternance': u"Email dédié à l'alternance",
        'new_phone': u"Nouveau téléphone",
        'new_website': u"Nouveau site web",
        'remove_email': u"Ne pas afficher l'email",
        'remove_phone': u"Ne pas afficher le téléphone",
        'remove_website': u"Ne pas afficher le site web",
        'remove_flag_alternance': u'Ne pas afficher le libellé "Alternance"',
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
        'sirets': Markup(
            u"Veuillez entrer un siret par ligne"
            u"<br>"
            u"Tous les sirets doivent être associés au même NAF (le premier NAF servant de référence)"
        ),
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
            u"Si ce champ est renseigné, le(s) ROME spécifié(s) ne seront plus associés à cette entreprise sur LBB."
            u"<br>"
            u"<a href=\"/data/romes-for-siret\" target=\"_blank\">Trouver les ROME pour un SIRET</a>."
        ),
        'romes_to_remove': Markup(
            u"Veuillez entrer un ROME par ligne."
            u"<br>"
            u"Si ce champ est renseigné, le(s) ROME spécifié(s) ne seront plus associés à cette entreprise - pour l'alternance."
            u"<br>"
            u"<a href=\"/data/romes-for-siret\" target=\"_blank\">Trouver les ROME pour un SIRET</a>."
        ),
        'new_email': u"Laisser vide s'il n'y a pas de modification à apporter",
        'new_phone': u"Laisser vide s'il n'y a pas de modification à apporter",
        'new_website': u"Laisser vide s'il n'y a pas de modification à apporter",
        'remove_email': u"Cocher cette case pour supprimer l'email",
        'remove_phone': u"Cocher cette case pour supprimer le téléphone",
        'remove_website': u"Cocher cette case pour supprimer le site web",
        'remove_flag_alternance': u"Cocher cette case pour supprimer le libellé 'alternance' et l'email dédié à l'alternance",
        'reason': u"Raison de la modification.",
    }

    form_columns = [
        'sirets',
        'name',
        'boost',
        'romes_to_boost',
        'romes_to_remove',
        'boost_alternance',
        'romes_alternance_to_boost',
        'romes_alternance_to_remove',
        'nafs_to_add',
        'new_email',
        'email_alternance',
        'new_phone',
        'new_website',
        'remove_email',
        'remove_phone',
        'remove_website',
        'remove_flag_alternance',
        'requested_by_email',
        'requested_by_first_name',
        'requested_by_last_name',
        'requested_by_phone',
        'reason',
    ]

    form_args = {
        'sirets': {
            'filters': [strip_filter, nospace_filter],
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
        'romes_alternance_to_boost': {
            'filters': [strip_filter],
        },
        'romes_alternance_to_remove': {
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

    def create_form(self):
        form = super(OfficeAdminUpdateModelView, self).create_form()
        if 'siret' in request.args:
            form.sirets.data = request.args['siret']
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
        is_valid = super(OfficeAdminUpdateModelView, self).validate_form(form)

        # All sirets must be well formed
        sirets = OfficeAdminUpdate.as_list(form.data['sirets'])
        only_one_siret = len(sirets) == 1

        if is_valid and not sirets:
            message = u"Le champs 'Sirets' est obligatoire. Veuillez le renseigner."
            flash(message, 'error')
            return False

        if is_valid:
            for siret in sirets:
                if not is_siret(siret):
                    message = u"Ce siret suivant n'est pas composé de 14 chiffres : {}".format(siret)
                    flash(message, 'error')
                    return False

        # If only one siret, we valdate it
        # If more than one siret : no siret validation
        if is_valid and only_one_siret:
            siret = sirets[0]
            office = Office.query.filter_by(siret=siret).first()
            if not office:
                message = u"Le siret suivant n'est pas présent sur LBB: {}".format(siret)
                flash(message, 'error')
                return False

        if is_valid:
            for siret in sirets:
                if 'id' in request.args:
                    # Avoid conflict with itself if update by adding id != request.args['id']
                    office_update_conflict = OfficeAdminUpdate.query.filter(
                        OfficeAdminUpdate.sirets.like("%{}%".format(siret)),
                        OfficeAdminUpdate.id != request.args['id']
                    )
                else:
                    office_update_conflict = OfficeAdminUpdate.query.filter(
                        OfficeAdminUpdate.sirets.like("%{}%".format(siret))
                    )

                if office_update_conflict.count() > 0:
                    message = u""""
                        Le siret {} est déjà présent dans la fiche n°{}
                    """.format(siret, office_update_conflict[0].id)
                    flash(message, 'error')
                    return False


        # Get company
        first_office = Office.query.filter_by(siret=sirets[0]).first() if sirets else None

        # Codes ROMES to boost or to add
        if is_valid and form.data.get('romes_to_boost'):
            try:
                self.validate_romes_to_boost(form, 'romes_to_boost', 'boost')
            except (RomeToBoostException, InvalidRome) as e:
                flash(e.message, 'error')
                return False

        # Codes ROMES to boost or to add (for alternance)
        if is_valid and form.data.get('romes_alternance_to_boost'):
            try:
                self.validate_romes_to_boost(form, 'romes_to_boost', 'boost_alternance')
            except (RomeToBoostException, InvalidRome) as e:
                flash(e.message, 'error')
                return False


        # Codes ROMES to remove for LBB
        if is_valid and form.data.get('romes_to_remove'):
            try:
                office_naf = first_office.naf if only_one_siret else None
                self.validate_romes_to_remove(form, 'romes_to_remove', office_naf)
            except (RomeToRemoveException, InvalidRome) as e:
                flash(e.message, 'error')
                return False

        # Codes ROMES to remove (for alternance)
        if is_valid and form.data.get('romes_alternance_to_remove'):
            try:
                office_naf = first_office.naf if only_one_siret else None
                self.validate_romes_to_remove(form, 'romes_alternance_to_remove', office_naf)
            except (RomeToRemoveException, InvalidRome) as e:
                flash(e.message, 'error')
                return False

        # Codes NAF to add
        if is_valid and form.data.get('nafs_to_add'):
            nafs_to_add = form.data.get('nafs_to_add')

            for naf in OfficeAdminUpdate.as_list(nafs_to_add):
                if naf not in settings.NAF_CODES:
                    msg = u"`%s` n'est pas un code NAF valide." % naf
                    flash(msg, 'error')
                    return False
                if naf == first_office.naf and only_one_siret:
                    msg = u"Le NAF `%s` est déjà associé à cette entreprise." % naf
                    flash(msg, 'error')
                    return False

        return is_valid


    def validate_romes_to_remove(self, form, romes_to_remove_field, office_naf=None):
        romes_to_remove = form.data.get(romes_to_remove_field)

        for rome in OfficeAdminUpdate.as_list(romes_to_remove):
            self.validate_rome(rome, romes_to_remove_field)

            if office_naf:
                office_romes = [item.code for item in mapping_util.romes_for_naf(office_naf)]
                if rome not in office_romes:
                    msg = u"`%s` n'est pas un code ROME lié au NAF de cette entreprise. Champ : '%s'" % (
                            rome,
                            self.column_labels[romes_to_remove_field]
                        )
                    raise RomeToRemoveException(msg)


    def validate_romes_to_boost(self, form, romes_boost_field, boost_field):
        romes_to_boost = form.data.get(romes_boost_field)

        if not form.data.get(boost_field):
            msg = u"Vous devez cocher la case `%s`. " % self.column_labels[boost_field]
            raise RomeToBoostException(msg)


        for rome in OfficeAdminUpdate.as_list(romes_to_boost):
            self.validate_rome(rome, romes_boost_field)


    def validate_rome(self, rome, field_name):
        if not mapping_util.rome_is_valid(rome):
            msg = u"`%s` n'est pas un code ROME valide. Assurez-vous de ne saisir qu'un élément par ligne. Champ : '%s'" % (
                rome,
                self.column_labels[field_name]
            )
            raise InvalidRome(msg)