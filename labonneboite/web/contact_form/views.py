from functools import wraps
from urllib.parse import urlencode
import logging

from flask import flash, redirect, render_template, session
from flask import Blueprint, Markup
from flask import url_for, request
from sqlalchemy.orm.exc import NoResultFound

from labonneboite.common import models
from labonneboite.common.mailjet import MailjetAPIError
from labonneboite.common.models import OfficeAdminUpdate
from labonneboite.conf import settings
from labonneboite.web.admin.views.office_admin_update import CONTACT_MODES
from labonneboite.web.auth.backends import peam_recruiter
from labonneboite.web.contact_form import forms, mail
from labonneboite.web.utils import fix_csrf_session

import time

logger = logging.getLogger('main')

contactFormBlueprint = Blueprint('contact_form', __name__)

ERROR_CONTACT_MODE_MESSAGE = 'Vous avez indiqué vouloir être contacté \'{}\' mais le champ \'{}\' n\'est pas renseigné. Nous vous invitons à le remplir.'

ERROR_MISSING_CONTACT_INFO = "Veuillez tout d'abord renseigner vos informations de contact"

# Get form value from office.contact_mode text
CONTACT_MODES_LABEL_TO_FORM_VALUE = {v:k for k, v in CONTACT_MODES.items()}

ACTION_NAMES = [
    'update_coordinates',
    'update_jobs',
    'delete',
    'other',
]

ACTION_NAME_TO_TITLE = {
    'update_coordinates':
        "Demande de modification des informations d'une entreprise",
    'update_jobs':
        """
            Demande de modification des métiers pour lesquels
            une entreprise reçoit des candidatures spontanées
        """,
    'delete':
        "Demande de suppression d'une entreprise",
    'other':
        "Autre demande",
}


def office_identification_required(function):
    """
    Decorator that validates office identification info.
    """
    @wraps(function)
    def decorated(*args, **kwargs):
        form = forms.OfficeHiddenIdentificationForm(data=request.values, meta={'csrf': False})
        if not form.validate():
            flash(ERROR_MISSING_CONTACT_INFO, 'error')
            return redirect(url_for('contact_form.change_info'))
        return function(*args, **kwargs)
    return decorated


def is_recruiter_from_lba():
    return request.args.get('origin', '') == 'labonnealternance'


def get_action_name():
    action_name = request.args.get('action_name', None)
    if action_name not in ACTION_NAMES:
        action_name = None
    return action_name


def get_subject():
    source = "LBA" if is_recruiter_from_lba() else "LBB"
    return f"Nouveau message entreprise depuis {source}"


def generate_fail_flash_content():
    email = settings.LBA_EMAIL if is_recruiter_from_lba() else settings.LBB_EMAIL
    message = f"""
        <div class="text-center">
            Erreur lors de l'envoi de l'e-mail.
            Vous pouvez nous contacter directement à l'adresse suivante : <a href="mailto:{email}">{email}</a>
        </div>
    """
    return Markup(message)


def unknown_siret_message():
    email = settings.LBA_EMAIL if is_recruiter_from_lba() else settings.LBB_EMAIL
    msg = f"""
        Ce siret n'est pas connu de notre service.
        Vous pouvez nous contacter directement à l'adresse suivante : <a href="mailto:{email}">{email}</a>
    """
    return Markup(msg)


def get_office_identification_data():
    return forms.OfficeHiddenIdentificationForm(data=request.args, meta={'csrf': False}).data

MAX_ATTEMPTS = 2
def sendMail(mail_content, subject):
    '''
        This function will send an email to us and retry in case of failure
        With 2 attempts - i.e. 1 retry, the wait time will be 5s at worst
    '''
    for attempt in range(MAX_ATTEMPTS):
        try:
            mail.send_mail(mail_content=mail_content, subject=subject)
        except MailjetAPIError as e:
            logger.exception(e)
            if attempt < MAX_ATTEMPTS - 1:
                time.sleep(5)
        else:
            break
    else:
        logger.critical('Mail not sent (to settings.TO_EMAIL)', subject, mail_content)
        flash(generate_fail_flash_content(), 'error')

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
    in order to validate their identity more quickly/easily.
    """
    action_name = get_action_name()
    if not action_name:
        flash('Une erreur inattendue est survenue, veuillez sélectionner à nouveau une action', 'error')
        return redirect(url_for('contact_form.ask_action'))

    title = ACTION_NAME_TO_TITLE.get(action_name, '')

    return render_template(
        'contact_form/ask_recruiter_pe_connect.html',
        use_lba_template=is_recruiter_from_lba(),
        siret=request.args.get('siret', ''),
        action_name=action_name,
        title=title,
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
            flash(unknown_siret_message(), 'error')
        else:
            params = {key: form.data[key] for key in ['siret', 'last_name', 'first_name', 'phone', 'email']}
            if is_recruiter_from_lba():
                params.update({"origin":"labonnealternance"})
            action_form_url = "contact_form.%s_form" % action_name
            url = url_for(action_form_url, **params)
            return redirect(url)

    return render_template('contact_form/form.html',
        title='Identifiez-vous',
        submit_text='suivant',
        extra_submit_class='identification-form',
        form=form,
        is_certified_recruiter=peam_recruiter.is_certified_recruiter(),
        is_recruiter=peam_recruiter.is_recruiter(),
        use_lba_template=is_recruiter_from_lba(),
        show_disclaimer=True,
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
@office_identification_required
def update_coordinates_form():
    """
    Allow a recruiter to update his company's coordinates.
    """
    form_data = request.values

    try:
        office = models.Office.query.filter(models.Office.siret == form_data['siret']).one()
    except NoResultFound:
        flash(unknown_siret_message(), 'error')
        return redirect(url_for('contact_form.change_info'))

    form = forms.OfficeUpdateCoordinatesForm(data=form_data)

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

            sendMail(mail_content=mail_content, subject=get_subject())

            params = request.args.to_dict()
            params.update({
                'custom_ga_pageview': '/recruteur/update_coordinates/success',
                'suggest_update_jobs': '1',
            })
            return redirect(url_for('contact_form.success', **params))

    return render_template('contact_form/form.html',
        title='Modifier ma fiche entreprise',
        form=form,
        params=urlencode(get_office_identification_data()),
        use_lba_template=is_recruiter_from_lba(),
        show_entreprise_page=True,
        show_coordinates_disclaimer=True,
        custom_ga_pageview='/recruteur/update_coordinates/update_coordinates',
    )


@contactFormBlueprint.route('/informations-entreprise/modifier-metiers', methods=['GET', 'POST'])
@office_identification_required
def update_jobs_form():
    """
    Allow a recruiter to add or delete ROME codes related to his company.
    """
    # Use POST params if available, GET params otherwise.
    form_data = request.form or request.args.copy()

    try:
        office = models.Office.query.filter(models.Office.siret == form_data['siret']).one()
    except NoResultFound:
        flash(unknown_siret_message(), 'error')
        return redirect(url_for('contact_form.change_info'))

    if request.method == 'GET':

        # Prepare form's initial data.
        romes_to_boost = office.romes_codes
        romes_alternance_to_boost = office.romes_codes
        extra_romes_to_add = set()
        extra_romes_alternance_to_add = set()

        office_update = OfficeAdminUpdate.query.filter(OfficeAdminUpdate.sirets == office.siret).first()
        if office_update:
            if office_update.romes_to_boost:
                romes_to_boost = set(OfficeAdminUpdate.as_list(office_update.romes_to_boost))
                extra_romes_to_add = romes_to_boost - office.romes_codes
            if office_update.romes_alternance_to_boost:
                romes_alternance_to_boost = set(OfficeAdminUpdate.as_list(office_update.romes_alternance_to_boost))
                extra_romes_alternance_to_add = romes_alternance_to_boost - office.romes_codes

        form_data['romes_to_keep'] = romes_to_boost
        form_data['romes_alternance_to_keep'] = romes_alternance_to_boost

    else:
        # Those form fields are defined outside of the form class, we use `request.form` to get them.
        extra_romes_to_add = set(request.form.getlist('extra_romes_to_add'))
        extra_romes_alternance_to_add = set(request.form.getlist('extra_romes_alternance_to_add'))

    form = forms.OfficeUpdateJobsForm(data=form_data, office=office)

    if form.validate_on_submit():
        recruiter_message = models.UpdateJobsRecruiterMessage.create_from_form(
            form,
            is_certified_recruiter=peam_recruiter.is_certified_recruiter(),
            uid=peam_recruiter.get_recruiter_uid()
        )
        mail_content = mail.generate_update_jobs_mail(form, recruiter_message)

        sendMail(mail_content=mail_content, subject=get_subject())

        params = request.args.to_dict()
        params.update({
            'custom_ga_pageview': '/recruteur/update_jobs/success',
            'suggest_update_coordinates': '1',
        })
        return redirect(url_for('contact_form.success', **params))

    extra_added_jobs = [
        {
            'rome_code': rome_code,
            'label': settings.ROME_DESCRIPTIONS[rome_code],
            'lbb': rome_code in extra_romes_to_add,
            'lba': rome_code in extra_romes_alternance_to_add,
        }
        for rome_code in extra_romes_to_add | extra_romes_alternance_to_add
    ]

    return render_template('contact_form/change_job_infos.html',
        title='Demande de modification des métiers',
        form=form,
        params=urlencode(get_office_identification_data()),
        use_lba_template=is_recruiter_from_lba(),
        extra_added_jobs=extra_added_jobs,
        custom_ga_pageview='/recruteur/update_jobs/update_jobs',
    )


@contactFormBlueprint.route('/informations-entreprise/supprimer', methods=['GET', 'POST'])
@office_identification_required
def delete_form():
    """
    Allow a recruiter to remove his company from LBB/LBA.
    """
    form = forms.OfficeRemoveForm(data=request.values)

    if form.validate_on_submit():
        recruiter_message = models.RemoveRecruiterMessage.create_from_form(
            form,
            is_certified_recruiter=peam_recruiter.is_certified_recruiter(),
            uid=peam_recruiter.get_recruiter_uid()
        )
        mail_content = mail.generate_delete_mail(form, recruiter_message)

        sendMail(mail_content=mail_content, subject=get_subject())

        params = request.args.to_dict()
        params.update({
            'custom_ga_pageview': '/recruteur/delete/success',
        })
        return redirect(url_for('contact_form.success', **params))

    return render_template('contact_form/form.html',
        title='Supprimer mon entreprise',
        form=form,
        params=urlencode(get_office_identification_data()),
        use_lba_template=is_recruiter_from_lba(),
        custom_ga_pageview='/recruteur/delete/delete',
    )


@contactFormBlueprint.route('/informations-entreprise/autre-demande', methods=['GET', 'POST'])
@office_identification_required
def other_form():
    """
    Allow a recruiter to make another demand.
    """
    form = forms.OfficeOtherRequestForm(data=request.values)

    if form.validate_on_submit():
        recruiter_message = models.OtherRecruiterMessage.create_from_form(
            form,
            is_certified_recruiter=peam_recruiter.is_certified_recruiter(),
            uid=peam_recruiter.get_recruiter_uid()
        )
        mail_content = mail.generate_other_mail(form, recruiter_message)

        sendMail(mail_content=mail_content, subject=get_subject())

        params = request.args.to_dict()
        params.update({
            'custom_ga_pageview': '/recruteur/other/success',
        })
        return redirect(url_for('contact_form.success', **params))

    return render_template(
        'contact_form/form.html',
        form=form,
        title='Autre demande',
        params=urlencode(get_office_identification_data()),
        use_lba_template=is_recruiter_from_lba(),
        show_required_disclaimer=True,
        custom_ga_pageview='/recruteur/other/other',
    )


@contactFormBlueprint.route('/success', methods=['GET'])
def success():
    is_lba = is_recruiter_from_lba()

    params = get_office_identification_data()
    if is_lba:
        params.update({'origin': 'labonnealternance'})

    return render_template('contact_form/success_message.html',
        use_lba_template=is_lba,
        email=settings.LBA_EMAIL if is_lba else settings.LBB_EMAIL,
        home_url="https://labonnealternance.pole-emploi.fr" if is_lba else url_for('root.home'),
        site_name="La Bonne alternance" if is_lba else "La Bonne Boite",
        params=urlencode(params),
        action_form_url=url_for('contact_form.ask_action', **request.args),
        suggest_update_coordinates='suggest_update_coordinates' in request.args,
        suggest_update_jobs='suggest_update_jobs' in request.args,
        custom_ga_pageview=request.args.get('custom_ga_pageview'),
    )
