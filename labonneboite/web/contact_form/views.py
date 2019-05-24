# coding: utf8
from functools import wraps
from urllib.parse import urlencode
import logging

from flask import flash, redirect, render_template, session
from flask import Blueprint, Markup
from flask import url_for, request
from sqlalchemy.orm.exc import NoResultFound


from labonneboite.conf import settings
from labonneboite.web.admin.views.office_admin_update import CONTACT_MODES
from labonneboite.common import mapping as mapping_util
from labonneboite.common import models
from labonneboite.common.email_util import MailNoSendException
from labonneboite.web.contact_form import forms, mail
from labonneboite.web.utils import fix_csrf_session
from labonneboite.common.load_data import ROME_CODES
from labonneboite.web.auth.backends import peam_recruiter

logger = logging.getLogger('main')

contactFormBlueprint = Blueprint('contact_form', __name__)

ERROR_CONTACT_MODE_MESSAGE = 'Vous avez indiqué vouloir être contacté \'{}\' mais le champ \'{}\' n\'est pas renseigné. Nous vous invitons à le remplir.'

# Get form value from office.contact_mode text
CONTACT_MODES_LABEL_TO_FORM_VALUE = {v:k for k, v in CONTACT_MODES.items()}

ACTION_NAMES = [
    'update_coordinates',
    'update_jobs',
    'delete',
    'other',
]
 
@contactFormBlueprint.route('/verification-informations-entreprise', methods=['GET'])
@contactFormBlueprint.route('/verification-informations-entreprise/<siret>', methods=['GET'])
def change_info_or_apply_for_job(siret=None):
    """
    Ask user if he wants to change company information or apply for a job,
    in order to avoid the change_info page to be spammed so much by
    people thinking they are actually applying for a job.
    """
    return render_template(
        'contact_form/change_info_or_apply_for_job.html',
        use_lba_template=is_recruiter_from_lba(),
        siret=siret,
    )


@contactFormBlueprint.route('/connexion-recruteur', methods=['GET'])
def ask_recruiter_pe_connect():
    """
    Ask recruiters if they wants to be connected with their Pole Emploi recruiter account
    in order to validate their identity more quickly/easely
    """
    action_name = get_action_name()
    if not action_name:
        flash('Une erreur inattendue est survenue, veuillez sélectionner à nouveau une action', 'error')
        return redirect(url_for('contact_form.ask_action'))

    return render_template(
        'contact_form/ask_recruiter_pe_connect.html',
        use_lba_template=is_recruiter_from_lba(),
        siret=request.args.get('siret', ''),
        action_name=action_name,
        custom_ga_pageview='/recruteur/%s/connexion' % action_name,
    )


@contactFormBlueprint.route('/postuler/<siret>', methods=['GET'])
def apply_for_job(siret):
    """
    If user arrives here, it means we successfully avoided having him spam the
    company modification form. Now we just have to explain him what is wrong.
    """
    return render_template(
        'contact_form/apply_for_job.html',
        siret=siret,
        use_lba_template=is_recruiter_from_lba(),
    )

def create_form(form_class):
    """
    A decorator that inject hidden fields from OfficeHiddenIdentificationForm
    """
    def decorator(f):

        @wraps(f)
        def decorated_funtion(*args, **kwargs):
            kwargs['form'] = form_class()

            try:
                add_identication_data(kwargs['form'])
            except KeyError:
                flash('Veuillez tout d\'abord renseigner vos informations de contact', 'error')
                return redirect(url_for('contact_form.change_info'))

            return f(*args, **kwargs)
        return decorated_funtion

    return decorator


def add_identication_data(form):
    form.siret.data = request.args['siret']
    form.last_name.data = request.args['last_name']
    form.first_name.data = request.args['first_name']
    form.phone.data = request.args['phone']
    form.email.data = request.args['email']


def get_action_name():
    action_name = request.args.get('action_name', None)
    if action_name not in ACTION_NAMES:
        action_name = None
    return action_name


@contactFormBlueprint.route('/informations-entreprise', methods=['GET', 'POST'])
def change_info():
    """
    Let a user fill a form to identify himself/herself in order to request changes
    about an office.
    """
    fix_csrf_session()
    form = forms.OfficeIdentificationForm()

    # Clear session if user comes from 'I don't have recruiter account'
    if request.args.get('no_pe_connect', ''):
        peam_recruiter.clear_pe_connect_recruiter_session()

    # Siret information is present when coming from change_info route.
    # Apply it only if user has not typed anything else yet.
    params = request.args.copy()

    action_name = get_action_name()
    if not action_name:
        flash('Une erreur inattendue est survenue, veuillez sélectionner à nouveau une action', 'error')
        return redirect(url_for('contact_form.ask_action'))

    form.last_name.data = form.last_name.data or session.get(peam_recruiter.SessionKeys.LASTNAME.value)
    form.first_name.data = form.first_name.data or session.get(peam_recruiter.SessionKeys.FIRSTNAME.value)
    form.email.data = form.email.data or session.get(peam_recruiter.SessionKeys.EMAIL.value)

    siret = params.get('siret')
    if siret and not form.data['siret']:
        form.siret.data = siret

    if form.validate_on_submit():
        office = models.Office.query.filter(models.Office.siret == form.siret.data).first()
        if not office:
            form.siret.errors.append(unknown_siret_message())
        else:
            params = {key: form.data[key] for key in ['siret', 'last_name', 'first_name', 'phone', 'email']}
            if is_recruiter_from_lba():
                params.update({"origin":"labonnealternance"})
            action_form_url = "contact_form.%s_form" % action_name
            url = url_for(action_form_url, **params)
            return redirect(url)

    return render_template('contact_form/form.html',
        title='Erreur - Identifiez-vous' if form.errors else 'Identifiez-vous',
        submit_text='suivant',
        extra_submit_class='identification-form',
        form=form,
        is_certified_recruiter=peam_recruiter.is_certified_recruiter(),
        is_recruiter=peam_recruiter.is_recruiter(),
        use_lba_template=is_recruiter_from_lba(),
        show_credentials_disclaimer=True,
        show_required_disclaimer=True,
        hide_return=True,
        custom_ga_pageview='/recruteur/%s/identification' % action_name,
    )

@contactFormBlueprint.route('/informations-entreprise/action', methods=['GET'])
def ask_action():
    return render_template('contact_form/ask_action.html',
        title='Que voulez-vous faire ?',
        use_lba_template=is_recruiter_from_lba(),
        siret=request.args.get('siret', ''),
        custom_ga_pageview='/recruteur/choix-action',
    )


@contactFormBlueprint.route('/informations-entreprise/modifier-coordonnees', methods=['GET', 'POST'])
@create_form(forms.OfficeUpdateCoordinatesForm)
def update_coordinates_form(form):
    try:
        office = get_office_from_siret(request.args['siret'])
    except NoResultFound:
        flash(unknown_siret_message(), 'error')
        return redirect(url_for('contact_form.change_info'))

    # Fill form with form value (or office value by default)
    form.new_contact_mode.data = request.form.get(
        'new_contact_mode',
        CONTACT_MODES_LABEL_TO_FORM_VALUE.get(office.contact_mode, '')
    )
    form.new_website.data = request.form.get('new_website', office.website)
    form.new_email.data = request.form.get('new_email', office.email)
    form.new_phone.data = request.form.get('new_phone', office.phone)
    form.social_network.data = request.form.get('social_network', office.social_network)
    form.new_phone_alternance.data = request.form.get('new_phone_alternance', office.phone_alternance)
    form.new_email_alternance.data = request.form.get('new_email_alternance', office.email_alternance)

    if form.validate_on_submit():
        form_valid = True

        # If a recruiter choose a contact_mode, the associated field became required
        contact_mode = form.new_contact_mode.data
        if contact_mode == 'website' and not form.new_website.data:
            flash(ERROR_CONTACT_MODE_MESSAGE.format('Via votre site internet', 'Site Internet'), 'error')
            form_valid = False
        elif contact_mode == 'phone' and not form.new_phone.data:
            flash(ERROR_CONTACT_MODE_MESSAGE.format('Par téléphone', 'Téléphone'), 'error')
            form_valid = False
        elif contact_mode == 'email' and not form.new_email.data:
            flash(ERROR_CONTACT_MODE_MESSAGE.format('Par email', 'Email recruteur'), 'error')
            form_valid = False


        if form_valid:
            recruiter_message = models.UpdateCoordinatesRecruiterMessage.create_from_form(
                form,
                is_certified_recruiter=peam_recruiter.is_certified_recruiter(),
                uid=peam_recruiter.get_recruiter_uid()
            )
            mail_content = mail.generate_update_coordinates_mail(form, recruiter_message)

            try:
                mail.send_mail(mail_content, get_subject())
            except MailNoSendException as e:
                logger.exception(e)
                flash(generate_fail_flash_content(), 'error')
            else:
                redirect_params = get_success_value()
                return render_template('contact_form/success_message.html',
                    title="Confirmation - Merci pour votre message",
                    use_lba_template=is_recruiter_from_lba(),
                    site_name=redirect_params.get('site_name'),
                    email=redirect_params.get('email'),
                    home_url=redirect_params.get('home_url'),
                    suggest_update_jobs=True,
                    params=extract_recruiter_data(),
                    action_form_url=url_for('contact_form.ask_action', **request.args),
                    custom_ga_pageview='/recruteur/update_coordinates/success',
                )

    return render_template('contact_form/form.html',
        title='Erreur - Modifier ma fiche entreprise' if form.errors else 'Modifier ma fiche entreprise',
        form=form,
        submit_text='Modifier ma fiche entreprise',
        params=extract_recruiter_data(),
        use_lba_template=is_recruiter_from_lba(),
        show_entreprise_page=True,
        show_coordinates_disclaimer=True,
        custom_ga_pageview='/recruteur/update_coordinates/update_coordinates',
    )


@contactFormBlueprint.route('/informations-entreprise/modifier-metiers', methods=['GET', 'POST'])
@create_form(forms.OfficeUpdateJobsForm)
def update_jobs_form(form):
    try:
        office = get_office_from_siret(request.args['siret'])
    except NoResultFound:
        flash(unknown_siret_message(), 'error')
        return redirect(url_for('contact_form.change_info'))

    office_romes = mapping_util.romes_for_naf(office.naf)

    rome_fields = []
    for rome in office_romes:
        # Retrieve old values
        current_values = dict(request.form).get(rome.code, ['lbb', 'lba'])

        rome_fields.append({
            'code': rome.code,
            'name': rome.name,
            'current_values': current_values
        })

    if form.validate_on_submit():
        recruiter_message = models.UpdateJobsRecruiterMessage.create_from_form(
            form,
            is_certified_recruiter=peam_recruiter.is_certified_recruiter(),
            uid=peam_recruiter.get_recruiter_uid()
        )
        mail_content = mail.generate_update_jobs_mail(form, recruiter_message)

        try:
            mail.send_mail(mail_content, get_subject())
        except MailNoSendException as e:
            logger.exception(e)
            flash(generate_fail_flash_content(), 'error')
        else:
            redirect_params = get_success_value()
            return render_template('contact_form/success_message.html',
                title="Confirmation - Merci pour votre message",
                use_lba_template=is_recruiter_from_lba(),
                site_name=redirect_params.get('site_name'),
                email=redirect_params.get('email'),
                home_url=redirect_params.get('home_url'),
                rome_fields=rome_fields,
                suggest_update_coordinates=True,
                params=extract_recruiter_data(),
                action_form_url=url_for('contact_form.ask_action', **request.args),
                custom_ga_pageview='/recruteur/update_jobs/success',
            )


    return render_template('contact_form/change_job_infos.html',
        title='Erreur - Demande de modification des métiers' if form.errors else 'Demande de modification des métiers',
        form=form,
        submit_text='Modifier mes métiers',
        params=extract_recruiter_data(),
        use_lba_template=is_recruiter_from_lba(),
        manually_added_jobs=extract_manually_added_jobs(office),
        rome_fields=rome_fields,
        custom_ga_pageview='/recruteur/update_jobs/update_jobs',
    )


@contactFormBlueprint.route('/informations-entreprise/supprimer', methods=['GET', 'POST'])
@create_form(forms.OfficeRemoveForm)
def delete_form(form):
    if form.validate_on_submit():
        recruiter_message = models.RemoveRecruiterMessage.create_from_form(
            form,
            is_certified_recruiter=peam_recruiter.is_certified_recruiter(),
            uid=peam_recruiter.get_recruiter_uid()
        )
        mail_content = mail.generate_delete_mail(form, recruiter_message)

        try:
            mail.send_mail(mail_content, get_subject())
        except MailNoSendException as e:
            logger.exception(e)
            flash(generate_fail_flash_content(), 'error')
        else:
            redirect_params = get_success_value()
            return render_template('contact_form/success_message.html',
                title="Confirmation - Merci pour votre message",
                use_lba_template=is_recruiter_from_lba(),
                site_name=redirect_params.get('site_name'),
                email=redirect_params.get('email'),
                home_url=redirect_params.get('home_url'),
                action_form_url=url_for('contact_form.ask_action', **request.args),
                custom_ga_pageview='/recruteur/delete/success',
            )


    return render_template('contact_form/form.html',
        title='Erreur - Supprimer mon entreprise' if form.errors else 'Supprimer mon entreprise',
        form=form,
        submit_text='Supprimer mon entreprise',
        params=extract_recruiter_data(),
        use_lba_template=is_recruiter_from_lba(),
        custom_ga_pageview='/recruteur/delete/delete',
    )


@contactFormBlueprint.route('/informations-entreprise/autre-demande', methods=['GET', 'POST'])
@create_form(forms.OfficeOtherRequestForm)
def other_form(form):
    if form.validate_on_submit():
        recruiter_message = models.OtherRecruiterMessage.create_from_form(
            form,
            is_certified_recruiter=peam_recruiter.is_certified_recruiter(),
            uid=peam_recruiter.get_recruiter_uid()
        )
        mail_content = mail.generate_other_mail(form, recruiter_message)

        try:
            mail.send_mail(mail_content, get_subject())
        except MailNoSendException as e:
            logger.exception(e)
            flash(generate_fail_flash_content(), 'error')
        else:
            redirect_params = get_success_value()
            return render_template('contact_form/success_message.html',
                title="Confirmation - Merci pour votre message",
                use_lba_template=is_recruiter_from_lba(),
                site_name=redirect_params.get('site_name'),
                email=redirect_params.get('email'),
                home_url=redirect_params.get('home_url'),
                action_form_url=url_for('contact_form.ask_action', **request.args),
                custom_ga_pageview='/recruteur/other/success',
            )


    return render_template(
        'contact_form/form.html',
        title='Erreur - Autre demande' if form.errors else 'Autre demande',
        form=form,
        submit_text='Envoyer votre message',
        params=extract_recruiter_data(),
        use_lba_template=is_recruiter_from_lba(),
        show_required_disclaimer=True,
        custom_ga_pageview='/recruteur/other/other',
    )


def get_office_from_siret(siret):
    return models.Office.query.filter(models.Office.siret == siret).one()


def is_recruiter_from_lba():
    return request.args.get('origin', '') == 'labonnealternance'


def get_success_value():
    if is_recruiter_from_lba():
        return {
            'site_name': 'La Bonne alternance',
            'home_url': 'https://labonnealternance.pole-emploi.fr',
            'email': 'labonnealternance@pole-emploi.fr',
        }

    return {
        'site_name': 'La Bonne Boite',
        'home_url': url_for('root.home'),
        'email': 'labonneboite@pole-emploi.fr',
    }

def get_subject():
    return 'Nouveau message entreprise depuis LBA' if is_recruiter_from_lba() else 'Nouveau message entreprise depuis LBB'

def generate_fail_flash_content():
    email = 'labonnealternance@pole-emploi.fr' if is_recruiter_from_lba() else 'labonneboite@pole-emploi.fr'
    message = """
            <div class="text-center">
                Erreur lors de l\'envoi de l\'e-mail.
                Vous pouvez nous contacter directement à l\'adresse suivante : <a href="mailto:{}">{}</a>
            </div>
        """.format(email, email)
    return Markup(message)


def extract_manually_added_jobs(office):
    """
    Return manually added_job as a string : rome1,lbb,lba||rome2,lbb||....
    """
    values = dict(request.form)
    office_romes = [item.code for item in mapping_util.romes_for_naf(office.naf)]

    added_romes_codes = [key for key in values if key not in office_romes and key in ROME_CODES]
    added_romes = []

    for rome_code in added_romes_codes:
        added_romes.append({
            'id': rome_code,
            'label': settings.ROME_DESCRIPTIONS[rome_code],
            'lbb': True if 'lbb' in values.get(rome_code, []) else False,
            'lba': True if 'lba' in values.get(rome_code, []) else False,
        })

    return added_romes


def unknown_siret_message():
    email = 'labonnealternance@pole-emploi.fr' if is_recruiter_from_lba() else 'labonneboite@pole-emploi.fr'
    msg = """
        Ce siret n\'est pas connu de notre service.
        Vous pouvez nous contacter directement à l\'adresse suivante : <a href="mailto:{}">{}</a>
    """.format(email, email)
    return Markup(msg)



def extract_recruiter_data():
    """
    We extract from the URL, the data given in the "identifiez-vous" step of the contact process
    """

    keys = ['siret', 'last_name', 'first_name', 'phone', 'email']

    params = {
        k: request.args[k] for k in keys if k in request.args
    }

    return urlencode(params)
