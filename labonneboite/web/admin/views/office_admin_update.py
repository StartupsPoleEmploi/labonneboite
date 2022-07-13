import logging

from flask import flash, redirect, request, url_for
from flask import Markup
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import BaseForm
from wtforms import validators
from labonneboite_common.siret import is_siret

from labonneboite.common import mapping as mapping_util
from labonneboite.common import models
from labonneboite.web.admin.forms import nospace_filter, phone_validator, strip_filter
from labonneboite.web.admin.utils import datetime_format, AdminModelViewMixin
from labonneboite.conf import settings
from labonneboite.scripts import create_index
from labonneboite.importer.settings import SCORE_ALTERNANCE_REDUCING_MINIMUM_THRESHOLD, \
    HIRING_REDUCING_MINIMUM_THRESHOLD

logger = logging.getLogger('main')

UPDATE_STYLE = 'border: solid 5px green'
DESCRIPTION_TEMPLATE = '<strong style="color: red;">Ancienne valeur : {}</strong><br>{}'

CONTACT_MODES_ITEMS = (
    ('email', 'Envoyez votre candidature par mail'),
    ('mail', 'Envoyez votre candidature par courrier'),
    ('office', 'Présentez vous directement à l\'entreprise'),
    ('website', 'Postulez via le site internet de l\'entreprise'),
    ('phone', 'Contactez l\'entreprise par téléphone'),
)
CONTACT_MODES = dict(CONTACT_MODES_ITEMS)

HIDE_CHECKBOXES = {
    'new_email': 'remove_email',
    'new_phone': 'remove_phone',
    'new_website': 'remove_website',
}

LITTLE_BOOST_VALUE = 75


class RomeToRemoveException(Exception):
    pass


class RomeToBoostException(Exception):
    pass


class InvalidRome(Exception):
    pass


def is_empty_field(value):
    """
    Specific function for detecing empty value
    We don't use 'if' because the field could be a boolean
    """
    return value is None or value == ''


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
        'date_updated',
    ]

    column_details_list = [
        'sirets',
        'name',
        'hiring',
        'score_alternance',
        'contact_mode',
        'boost',
        'romes_to_boost',
        'boost_alternance',
        'romes_alternance_to_boost',
        'romes_to_remove',
        'nafs_to_add',
        'new_company_name',
        'new_office_name',
        'new_email',
        'new_phone',
        'email_alternance',
        'phone_alternance',
        'website_alternance',
        'new_website',
        'social_network',
        'remove_email',
        'remove_phone',
        'remove_website',
        'requested_by_email',
        'requested_by_first_name',
        'requested_by_last_name',
        'requested_by_phone',
        'certified_recruiter',
        'recruiter_uid',
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
        'sirets': "Sirets",
        'name': "Nom de l'entreprise",
        'reason': "Raison",
        'contact_mode': "Modifier le mode de contact",
        'boost': "Booster le score - LBB",
        'romes_to_boost': "Limiter le boosting du score à certain codes ROME uniquement - LBB",
        'romes_to_remove': "Retirer des codes ROME associés à une entreprise - LBB",
        'boost_alternance': "Booster le score - Alternance",
        'romes_alternance_to_boost': "Limiter le boosting du score à certain codes ROME uniquement - Alternance",
        'romes_alternance_to_remove': "Retirer des codes ROME associés à une entreprise - Alternance",
        'nafs_to_add': "Ajouter un ou plusieurs NAF à une entreprise",
        'new_company_name': "Nouvelle raison sociale",
        'new_office_name': "Nouvelle enseigne",
        'new_email': "Nouvel email",
        'new_phone': "Nouveau téléphone",
        'new_website': "Nouveau site web",
        'social_network': 'Réseau social',
        'remove_email': "Ne pas afficher l'email",
        'remove_phone': "Ne pas afficher le téléphone",
        'remove_website': "Ne pas afficher le site web",
        'email_alternance': "Email dédié à l'alternance",
        'phone_alternance': "Téléphone dédié à l'alternance",
        'website_alternance': "Site web dédié à l'alternance",
        'hiring': 'Modifier le nombre de recrutement (impactant fortement le score LBB)',
        'score_alternance': 'Modifier le score LBA',
        'requested_by_email': "Email",
        'requested_by_first_name': "Prénom",
        'requested_by_last_name': "Nom",
        'requested_by_phone': "Téléphone",
        'date_created': "Date de création",
        'date_updated': "Date de modification",
        'certified_recruiter': 'Recruteur certifié',
        'recruiter_uid': 'Identifiant unique du recruteur',
        'created_by': "Créé par",
        'updated_by': "Modifié par",
    }

    column_descriptions = {
        'sirets': Markup("Veuillez entrer un siret par ligne"
                         "<br>"
                         "Tous les sirets doivent être associés au même NAF (le premier NAF servant de référence)"),
        'requested_by_email': "Email de la personne qui demande la modification.",
        'requested_by_first_name': "Prénom de la personne qui demande la modification.",
        'requested_by_last_name': "Nom de la personne qui demande la modification.",
        'requested_by_phone': "Téléphone de la personne qui demande la modification.",
        'boost': "Cocher cette case pour forcer le positionnement en tête des résultats",
        'romes_to_boost': Markup(
            "Veuillez entrer un ROME par ligne."
            "<br>"
            "Si ce champ est renseigné, le score sera forcé uniquement pour le(s) ROME spécifié(s)."
            "<br>"
            "<a href=\"/data/romes-for-siret\" target=\"_blank\">Trouver les ROME pour un SIRET</a>."),
        'nafs_to_add': Markup("Veuillez entrer un NAF par ligne."),
        'romes_to_remove': Markup(
            "Veuillez entrer un ROME par ligne."
            "<br>"
            "Si ce champ est renseigné, le(s) ROME spécifié(s) ne seront plus associés à cette entreprise sur LBB."
            "<br>"
            "<a href=\"/data/romes-for-siret\" target=\"_blank\">Trouver les ROME pour un SIRET</a>."),
        'romes_alternance_to_remove': Markup(
            "Veuillez entrer un ROME par ligne."
            "<br>"
            "Si ce champ est renseigné, le(s) ROME spécifié(s) "
            "ne seront plus associés à cette entreprise - pour l'alternance."
            "<br>"
            "<a href=\"/data/romes-for-siret\" target=\"_blank\">Trouver les ROME pour un SIRET</a>."),
        'new_company_name': "Laisser vide s'il n'y a pas de modification à apporter",
        'new_office_name': "Laisser vide s'il n'y a pas de modification à apporter",
        'new_email': "Laisser vide s'il n'y a pas de modification à apporter",
        'new_phone': "Laisser vide s'il n'y a pas de modification à apporter",
        'new_website': "Laisser vide s'il n'y a pas de modification à apporter",
        'remove_email': "Cocher cette case pour supprimer l'email",
        'remove_phone': "Cocher cette case pour supprimer le téléphone",
        'remove_website': "Cocher cette case pour supprimer le site web",
        'hiring': "Nouveau nombre de recrutement dans les 6 mois (si 0 : suppression de l'entreprise sur LBB mais pas "
                  "LBA)",
        'score_aternance': "Nouveau score alternance (si 0 : suppression de l'entreprise pour l'alternance)",
        'reason': "Raison de la modification.",
        'certified_recruiter': 'Identifiant unique du recruteur',
        'recruiter_uid': 'Recruteur avec un email vérifié et l\'habilitation "recruteurcertifie" sur l\'ESD',
        'contact_mode': "Texte libre (maximum 255 caractères)",
    }

    form_columns = [
        'sirets',
        'name',
        'contact_mode',
        'hiring',
        'score_alternance',
        'boost',
        'romes_to_boost',
        'romes_to_remove',
        'boost_alternance',
        'romes_alternance_to_boost',
        'romes_alternance_to_remove',
        'nafs_to_add',
        'new_company_name',
        'new_office_name',
        'new_email',
        'new_phone',
        'new_website',
        'social_network',
        'email_alternance',
        'phone_alternance',
        'website_alternance',
        'remove_email',
        'remove_phone',
        'remove_website',
        'requested_by_email',
        'requested_by_first_name',
        'requested_by_last_name',
        'requested_by_phone',
        'certified_recruiter',
        'recruiter_uid',
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
        'new_company_name': {
            'filters': [strip_filter],
            'validators': [validators.optional()],
        },
        'new_office_name': {
            'filters': [strip_filter],
            'validators': [validators.optional()],
        },
        'new_email': {
            'validators': [validators.optional(), validators.Email()],
        },
        'email_alternance': {
            'validators': [validators.optional(), validators.Email()],
        },
        'phone_alternance': {
            'validators': [validators.optional(), phone_validator],
        },
        'website_alternance': {
            'validators': [validators.optional(), validators.URL()],
        },
        'new_phone': {
            'filters': [strip_filter, nospace_filter],
            'validators': [validators.optional(), phone_validator],
        },
        'new_website': {
            'filters': [strip_filter],
            'validators': [validators.optional(), validators.URL()],
        },
        'social_network': {
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
        'recruiter_uid': {
            'filters': [strip_filter, nospace_filter],
        },
        'reason': {
            'filters': [strip_filter],
        },
    }

    def _handle_view(self, name, **kwargs):
        """
        This method is executed before calling any view method.

        Sometimes, recruiter send two emails at the same time. Both contain
        a create office_admin_update link. But, when the first
        office_admin_update is created, the suggestion in the second mail
        became wrong. And, on saving, we got a conflict with the recently
        created office_admin_update. To avoid that, we redirect to the edit
        page if, afterall, an office_admin_update already exists for the
        company siret.
        """
        if name == 'create_view':
            recruiter_message = self.get_recruiter_message(request.args.get('recruiter_message_type'),
                                                           request.args.get('recruiter_message_id'))
            if recruiter_message:
                office_update_conflict = models.OfficeAdminUpdate.query.filter(
                    models.OfficeAdminUpdate.sirets.contains(recruiter_message.siret))
                if office_update_conflict.count():
                    params = {
                        'recruiter_message_id': recruiter_message.id,
                        'recruiter_message_type': recruiter_message.name,
                    }
                    url = url_for('officeadminupdate.edit_view', id=office_update_conflict[0].id, **params)
                    return redirect(url, code=302)

        return super(OfficeAdminUpdateModelView, self)._handle_view(name, **kwargs)

    def create_form(self):
        # Call only when a form is created
        form = super(OfficeAdminUpdateModelView, self).create_form()

        # Inject sirets from URL
        sirets = request.args.get('sirets', '')
        if sirets:
            form['sirets'].data = sirets.replace(',', '\n')

        return self.prefill_form(form)

    def on_form_prefill(self, form, id):
        # Call only when a form is updated
        return self.prefill_form(form, id)

    def prefill_form(self, form, form_id=None):
        """
        When the form is creating, we retrieve the recruiter_message
        based on 'recruiter_message_id' and 'recruiter_message_type' (if given).

        Then, for each field of the recruiter message, we compare it with the OfficeAdminUpdate stored in database.
        If changes, we give to the field a specific design (added in `form_widget_args`) and fill the form field
        with the new value.

        Return:
            The form updated with the new values and new field styles (if recruiter_message)
        """
        # Clean all styles before all
        self.form_widget_args = {}

        recruiter_message = self.get_recruiter_message(request.args.get('recruiter_message_type'),
                                                       request.args.get('recruiter_message_id'))
        if not recruiter_message:
            return form

        # Set sirets and office name fields on creation
        office = models.Office.query.filter(models.Office.siret == recruiter_message.siret).first()

        if form_id is None:
            self.set_update_style('sirets')
            form.sirets.data = recruiter_message.siret

            if office and 'name' not in request.form:
                form.name.data = office.name

        # If recruiter ask for updating his coordinates and job,
        # we assume that he wants to appear on LBB
        # so we improve his score if too low
        ask_job_or_coordinate_changes = recruiter_message.name in [
            models.UpdateCoordinatesRecruiterMessage.name, models.UpdateJobsRecruiterMessage.name
        ]

        if office and ask_job_or_coordinate_changes:
            if office.hiring <= HIRING_REDUCING_MINIMUM_THRESHOLD:
                self.set_update_style('hiring')
                self.set_little_boost(form['hiring'], office.hiring)

            if office.score_alternance <= SCORE_ALTERNANCE_REDUCING_MINIMUM_THRESHOLD:
                self.set_update_style('score_alternance')
                self.set_little_boost(form['score_alternance'], office.score_alternance)

        office_admin_update = models.OfficeAdminUpdate.query.filter(models.OfficeAdminUpdate.id == form_id).first()

        # Common behavior
        recruiter_phone = recruiter_message.requested_by_phone
        recruiter_phone = clean_phone(recruiter_phone) if recruiter_phone else None

        self.handle_diff('requested_by_last_name', recruiter_message.requested_by_last_name, office_admin_update, form)
        self.handle_diff('requested_by_first_name', recruiter_message.requested_by_first_name, office_admin_update,
                         form)
        self.handle_diff('requested_by_email', recruiter_message.requested_by_email, office_admin_update, form)
        self.handle_diff('requested_by_first_name', recruiter_message.requested_by_first_name, office_admin_update,
                         form)
        self.handle_diff('requested_by_last_name', recruiter_message.requested_by_last_name, office_admin_update, form)
        self.handle_diff('requested_by_phone', recruiter_phone, office_admin_update, form)
        self.handle_diff('certified_recruiter', recruiter_message.certified_recruiter, office_admin_update, form)
        self.handle_diff('recruiter_uid', recruiter_message.recruiter_uid, office_admin_update, form)

        if recruiter_message.name == models.UpdateCoordinatesRecruiterMessage.name:
            new_phone = clean_phone(recruiter_message.new_phone) if recruiter_message.new_phone else None

            new_phone_alternance = recruiter_message.new_phone_alternance
            new_phone_alternance = clean_phone(new_phone_alternance) if new_phone_alternance else None

            self.handle_diff('new_website', recruiter_message.new_website, office_admin_update, form)
            self.handle_diff('new_email', recruiter_message.new_email, office_admin_update, form)
            self.handle_diff('new_phone', new_phone, office_admin_update, form)
            self.handle_diff('social_network', recruiter_message.social_network, office_admin_update, form)
            self.handle_diff('phone_alternance', new_phone_alternance, office_admin_update, form)
            self.handle_diff('email_alternance', recruiter_message.new_email_alternance, office_admin_update, form)
            self.handle_diff('contact_mode', CONTACT_MODES.get(recruiter_message.contact_mode, ''), office_admin_update,
                             form)

        elif recruiter_message.name == models.RemoveRecruiterMessage.name:
            # The field is a boolean in contact form but an integer in the OfficeAdminpdate
            new_hiring = 0 if recruiter_message.remove_lbb else form.hiring.data
            new_score_alternance = 0 if recruiter_message.remove_lba else form.score_alternance.data
            self.handle_diff('hiring', new_hiring, office_admin_update, form)
            self.handle_diff('score_alternance', new_score_alternance, office_admin_update, form)

        elif recruiter_message.name == models.UpdateJobsRecruiterMessage.name:
            self.handle_diff('romes_to_boost', self.format(recruiter_message.romes_to_add), office_admin_update, form)
            self.handle_diff('romes_alternance_to_boost', self.format(recruiter_message.romes_alternance_to_add),
                             office_admin_update, form)
            self.handle_diff('romes_to_remove',
                             self.format(self.filter_romes(recruiter_message.romes_to_remove, office.naf)),
                             office_admin_update, form)
            self.handle_diff('romes_alternance_to_remove',
                             self.format(self.filter_romes(recruiter_message.romes_alternance_to_remove, office.naf)),
                             office_admin_update, form)

        elif recruiter_message.name == models.OtherRecruiterMessage.name:
            self.handle_diff('reason', recruiter_message.comment, office_admin_update, form)

        return form

    def handle_diff(self, form_field, new_value, office_admin_update, form):
        """
        This method compare the current OfficeAdminUpdate with the recruiterMessage given for a specific field.
        If a field has a new value, the field will be highlight a specific design and the old value
        will be added in the description.

        If there is no officeAdminUpdate, we only fill the form field
        """

        # OfficeAdminUpdate's creation (when there is no office_admin_update)
        if office_admin_update is None:
            # So we only set the value
            if not is_empty_field(new_value):
                self.set_update_style(form_field)
                form[form_field].data = new_value

            if form_field in HIDE_CHECKBOXES and not new_value:
                self.check_checkbox(form, HIDE_CHECKBOXES[form_field])
            return

        # OfficeAdminUpdate update
        current_value = getattr(office_admin_update, form_field)

        # Handle None and empty string value
        if is_empty_field(current_value) and is_empty_field(new_value):
            self.set_update_style(form_field)
            return

        if current_value != new_value:
            form[form_field].data = new_value
            self.set_update_style(form_field)

            # For phone, website and e-mail, we need to check the hide checkbox
            # if recruiter send an empty string (or refill it)
            if form_field in HIDE_CHECKBOXES:
                checkbox_field_name = HIDE_CHECKBOXES[form_field]

                checkbox_field = getattr(office_admin_update, checkbox_field_name)

                if not checkbox_field and current_value and not new_value:
                    self.check_checkbox(form, checkbox_field_name)
                # or at contrary, unchecked it if a new value have been send
                elif checkbox_field and new_value:
                    self.uncheck_checkbox(form, checkbox_field_name)

            # Update description with old value, added to the current description
            current_description = self.column_descriptions.get(form_field, '')
            new_description = Markup(DESCRIPTION_TEMPLATE.format(Markup.escape(current_value), current_description))
            form[form_field].description = new_description

        # Handle None and empty string value
        if is_empty_field(current_value) and is_empty_field(new_value):
            return

    def check_checkbox(self, form, checkbox_field_name):
        checkbox_current_description = self.column_descriptions.get(checkbox_field_name, '')
        form[checkbox_field_name].data = True
        form[checkbox_field_name].description = Markup(
            DESCRIPTION_TEMPLATE.format("Case non cochée", checkbox_current_description))

    def uncheck_checkbox(self, form, checkbox_field_name):
        checkbox_current_description = self.column_descriptions.get(checkbox_field_name, '')
        form[checkbox_field_name].data = False
        form[checkbox_field_name].description = Markup(
            DESCRIPTION_TEMPLATE.format("Case cochée", checkbox_current_description))

    def after_model_change(self, form: BaseForm, model: models.OfficeAdminUpdate, is_created: bool) -> None:
        create_index.update_offices_by_sirets(model.as_list(form.data['sirets']), model)

    def validate_form(self, form):
        # Add http:// is missing
        form['new_website'].data = format_url(form['new_website'].data)
        form['social_network'].data = format_url(form['social_network'].data)
        form['website_alternance'].data = format_url(form['website_alternance'].data)

        is_valid = super(OfficeAdminUpdateModelView, self).validate_form(form)
        if not is_valid:
            return is_valid

        # All sirets must be well formed
        sirets = models.OfficeAdminUpdate.as_list(form.data['sirets'])
        only_one_siret = len(sirets) == 1

        if not sirets:
            message = "Le champs 'Sirets' est obligatoire. Veuillez le renseigner."
            flash(message, 'error')
            return False

        for siret in sirets:
            if not is_siret(siret):
                message = "Ce siret suivant n'est pas composé de 14 chiffres : {}".format(siret)
                flash(message, 'error')
                return False

        # If only one siret, we valdate it
        # If more than one siret : no siret validation
        if only_one_siret:
            siret = sirets[0]
            office = models.Office.query.filter_by(siret=siret).first()
            if not office:
                message = "Le siret suivant n'est pas présent sur LBB: {}".format(siret)
                flash(message, 'error')
                return False

        # Show old value in description
        for siret in sirets:
            if 'id' in request.args:
                # Avoid conflict with itself if update by adding id != request.args['id']
                office_update_conflict = models.OfficeAdminUpdate.query.filter(
                    models.OfficeAdminUpdate.sirets.like("%{}%".format(siret)),
                    models.OfficeAdminUpdate.id != request.args['id'])
            else:
                office_update_conflict = models.OfficeAdminUpdate.query.filter(
                    models.OfficeAdminUpdate.sirets.like("%{}%".format(siret)))

            if office_update_conflict.count() > 0:
                message = """"
                    Le siret {} est déjà présent dans la fiche n°{}
                """.format(siret, office_update_conflict[0].id)
                flash(message, 'error')
                return False

        # Get company
        first_office = models.Office.query.filter_by(siret=sirets[0]).first() if sirets else None

        # Codes ROMES to boost or to add
        if form.data.get('romes_to_boost'):
            try:
                self.validate_romes_to_boost(form, 'romes_to_boost', 'boost')
            except (RomeToBoostException, InvalidRome) as e:
                flash(e.args[0], 'error')
                return False

        # Codes ROMES to boost or to add (for alternance)
        if form.data.get('romes_alternance_to_boost'):
            try:
                self.validate_romes_to_boost(form, 'romes_to_boost', 'boost_alternance')
            except (RomeToBoostException, InvalidRome) as e:
                flash(e.args[0], 'error')
                return False

        # Codes ROMES to remove for LBB
        if form.data.get('romes_to_remove'):
            try:
                office_naf = first_office.naf if only_one_siret else None
                self.validate_romes_to_remove(form, 'romes_to_remove', office_naf)
            except (RomeToRemoveException, InvalidRome) as e:
                flash(e.args[0], 'error')
                return False

        # Codes ROMES to remove (for alternance)
        if form.data.get('romes_alternance_to_remove'):
            try:
                office_naf = first_office.naf if only_one_siret else None
                self.validate_romes_to_remove(form, 'romes_alternance_to_remove', office_naf)
            except (RomeToRemoveException, InvalidRome) as e:
                flash(e.args[0], 'error')
                return False

        # Codes NAF to add
        if form.data.get('nafs_to_add'):
            nafs_to_add = form.data.get('nafs_to_add')

            for naf in models.OfficeAdminUpdate.as_list(nafs_to_add):
                if naf not in settings.NAF_CODES:
                    msg = "`%s` n'est pas un code NAF valide." % naf
                    flash(msg, 'error')
                    return False
                if naf == first_office.naf and only_one_siret:
                    msg = "Le NAF `%s` est déjà associé à cette entreprise." % naf
                    flash(msg, 'error')
                    return False

        # Identifiant recruteur
        if form.data.get('certified_recruiter') and not form.data.get('recruiter_uid'):
            msg = "La case 'Recruteur certifié' est cochée mais aucun identifiant n'est indiqué."
            flash(msg, 'error')
            return False

        return is_valid

    def validate_romes_to_remove(self, form, romes_to_remove_field, office_naf=None):
        romes_to_remove = form.data.get(romes_to_remove_field)

        for rome in models.OfficeAdminUpdate.as_list(romes_to_remove):
            self.validate_rome(rome, romes_to_remove_field)

            if office_naf:
                office_romes = [item.code for item in mapping_util.romes_for_naf(office_naf)]
                if rome not in office_romes:
                    msg = "`%s` n'est pas un code ROME lié au NAF de cette entreprise. Champ : '%s'" % (
                        rome, self.column_labels[romes_to_remove_field])
                    raise RomeToRemoveException(msg)

    def validate_romes_to_boost(self, form, romes_boost_field, boost_field):
        romes_to_boost = form.data.get(romes_boost_field)

        if not form.data.get(boost_field):
            msg = "Vous devez cocher la case `%s`. " % self.column_labels[boost_field]
            raise RomeToBoostException(msg)

        for rome in models.OfficeAdminUpdate.as_list(romes_to_boost):
            self.validate_rome(rome, romes_boost_field)

    def validate_rome(self, rome, field_name):
        if not mapping_util.rome_is_valid(rome):
            msg = "`{}` n'est pas un code ROME valide. Assurez-vous de ne saisir qu'un élément par ligne. Champ : '{}'"
            raise InvalidRome(msg.format(rome, self.column_labels[field_name]))

    def format(self, romes_str, char=','):
        return romes_str.replace(char, models.OfficeAdminUpdate.SEPARATORS[0]) if romes_str else romes_str

    # Temporary fix
    # Remove romes_to_removed not related to the office
    def filter_romes(self, romes_str, naf):
        office_romes = [item.code for item in mapping_util.romes_for_naf(naf)]
        romes = romes_str.split(',')
        romes_to_keep = [rome for rome in romes if rome in office_romes]

        return ','.join(romes_to_keep)

    def get_recruiter_message(self, model_name, id):
        MODELS_MAPPING = {
            models.UpdateCoordinatesRecruiterMessage.name: models.UpdateCoordinatesRecruiterMessage,
            models.RemoveRecruiterMessage.name: models.RemoveRecruiterMessage,
            models.UpdateJobsRecruiterMessage.name: models.UpdateJobsRecruiterMessage,
            models.OtherRecruiterMessage.name: models.OtherRecruiterMessage,
        }
        if model_name not in MODELS_MAPPING:
            return None
        return MODELS_MAPPING[model_name].get(id)

    def set_little_boost(self, form_field, hiring):
        form_field.data = LITTLE_BOOST_VALUE

        form_field.description = Markup("""
            <strong style="color: red;">
                Le recruteur nous ayant contacté et le nombre de recrutement prédit étant trop bas ({}).
                Nous supposons qu'il souhaite apparaître davantage et lui attribuons un léger boost.
            </strong>
        """).format(hiring)

    def set_update_style(self, field_name):
        self.form_widget_args.update({field_name: {'style': UPDATE_STYLE}})


def clean_phone(phone):
    return phone.replace(" ", "").replace(".", "")


def format_url(value):
    # Auto-adding http:// if missing
    if value and not value.startswith('http://') and not value.startswith('https://'):
        return '{}{}'.format('http://', value)
    return value
