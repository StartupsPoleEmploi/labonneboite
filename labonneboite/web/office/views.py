# coding: utf8

from datetime import date
import os
import StringIO

from slugify import slugify
from sqlalchemy.orm.exc import NoResultFound
from xhtml2pdf import pisa
from urllib import urlencode

from flask import abort, redirect, render_template, flash
from flask import Blueprint, current_app
from flask import make_response, send_file
from flask import request, session, url_for

from labonneboite.common import pdf as pdf_util
from labonneboite.common import util
from labonneboite.common.email_util import MandrillClient
from labonneboite.common.models import Office, OfficeAdminAdd, OfficeAdminUpdate, OfficeAdminRemove
from labonneboite.conf import settings
from labonneboite.common.contact_mode import CONTACT_MODE_STAGES

from labonneboite.web.office.forms import OfficeRemovalForm


officeBlueprint = Blueprint('office', __name__)


@officeBlueprint.route('/<siret>/details', methods=['GET'])
def details(siret=None):
    """
    Display the details of an office.
    In case the context of a rome_code is given, display appropriate score value for this rome_code
    """
    rome_code = request.args.get('rome_code', None)
    company = Office.query.filter_by(siret=siret).first()
    if not company:
        abort(404)
    context = {
        'company': company,
        'rome_code': rome_code,
    }
    return render_template('office/details.html', **context)


@officeBlueprint.route('/informations-entreprise', methods=['GET', 'POST'])
def change_info():
    """
    Let a user fill a form to request a removal or information change about an office.
    """
    form = OfficeRemovalForm()
    if form.validate_on_submit():
        try:
            client = MandrillClient(current_app.extensions['mandrill'])
            client.send(
                u"""Un email a été envoyé par le formulaire de contact de la Bonne Boite :<br>
                - Action : %s<br>
                - Siret : %s,<br>
                - Prénom : %s,<br>
                - Nom : %s, <br>
                - E-mail : %s,<br>
                - Tél. : %s,<br>
                - Commentaire : %s<br>
                <hr>
                - Status SAVE : %s
                <hr>

                Cordialement,<br>
                La Bonne Boite""" % (
                    form.action.data,
                    form.siret.data,
                    form.first_name.data,
                    form.last_name.data,
                    form.email.data,
                    form.phone.data,
                    form.comment.data,
                    make_save_suggestion(form)
                )
            )
            msg = u"Merci pour votre message, nous reviendrons vers vous dès que possible."
            flash(msg, 'success')

        except Exception as e:  # pylint: disable=W0703
            current_app.logger.error(
                u"/informations-entreprise - An error occurred while sending an email: %s", repr(e))
            msg = u"Erreur dans l'envoi du mail, vous pouvez envoyer un email directement à %s" % settings.CONTACT_EMAIL
            flash(msg, 'error')

        return redirect(url_for('office.change_info'))
    return render_template('office/change_info.html', form=form)


def detail(siret):
    company = Office.query.filter(Office.siret == siret).one()

    if 'search_args' in session:
        search_url = util.get_search_url('/resultat', session['search_args'])
    else:
        search_url = None
    rome = request.args.get('r')
    if rome not in settings.ROME_DESCRIPTIONS:
        rome = None
        rome_description = None
    else:
        rome_description = settings.ROME_DESCRIPTIONS[rome]

    contact_mode = util.get_contact_mode_for_rome_and_naf(rome, company.naf)

    google_search = "%s+%s" % (company.name.replace(' ', '+'), company.city.replace(' ', '+'))
    google_url = "https://www.google.fr/search?q=%s" % google_search

    return {
        'company': company,
        'contact_mode': contact_mode,
        'rome': rome,
        'rome_description': rome_description,
        'google_url': google_url,
        'kompass_url': "http://fr.kompass.com/searchCompanies?text=%s" % company.siret,
        'search_url': search_url,
    }

def make_save_suggestion(form):
    # Save informations
    company = Office.query.filter_by(siret=form.siret.data).first()

    def dirty_fix_url(url):
        from labonneboite.common.env import get_current_env, ENV_STAGING, ENV_PRODUCTION
        if get_current_env() == ENV_STAGING:
            return 'http://labonneboite.beta.pole-emploi.fr' + url
        elif get_current_env() == ENV_PRODUCTION:
            return 'https://labonneboite.pole-emploi.fr' + url
        else:
            return url

    if not company:
        # OfficeAdminRemove already exits ?
        office_admin_remove = OfficeAdminRemove.query.filter_by(siret=form.siret.data).first()
        if office_admin_remove:
            url = url_for("officeadminremove.edit_view", id=office_admin_remove.id)
            return u"Entreprise retirée via Save : <a href='%s'>Voir la fiche de suppression</a>" % dirty_fix_url(url)
        else:
            return u'Aucune entreprise trouvée avec le siret %s' % form.siret.data

    # OfficeAdminAdd already exits ?
    office_admin_add = OfficeAdminAdd.query.filter_by(siret=form.siret.data).first()
    if office_admin_add:
        url = url_for("officeadminadd.edit_view", id=office_admin_add.id)
        return u"Entreprise créée via Save : <a href='%s'>Voir la fiche d'ajout</a>" % dirty_fix_url(url)

    # OfficeAdminUpdate already exits ?
    office_admin_update = OfficeAdminUpdate.query.filter(OfficeAdminUpdate.sirets.like("%{}%".format(form.siret.data))).first()

    if office_admin_update:
        url = url_for("officeadminupdate.edit_view", id=office_admin_update.id)
        return u"Entreprise modifiée via Save : <a href='%s'>Voir la fiche de modification</a>" % dirty_fix_url(url)


    # No office AdminOffice found : suggest to create an OfficeAdminRemove and OfficeRemoveUpdate
    params = {
        'siret': form.siret.data,
        'name': company.company_name,
        'requested_by_email': form.email.data,
        'requested_by_first_name': form.first_name.data,
        'requested_by_last_name': form.last_name.data,
        'requested_by_phone': form.phone.data,
        'reason': form.comment.data,
    }
    if form.action.data == "enlever":
        url = '%s?%s' % (url_for("officeadminremove.create_view"), urlencode(params))
        status_save = u" Une suppression a été demandée : <a href='%s'>Créer une fiche de suppression</a>" % dirty_fix_url(url)
    else:
        url = '%s?%s' % (url_for("officeadminupdate.create_view"), urlencode(params))
        status_save = u"Entreprise non modifiée via Save : <a href='%s'>Créer une fiche de modification</a>" % dirty_fix_url(url)

    return status_save


def fetch_resources(uri, rel):
    url = "https://%s%s" % (settings.HOST, uri)
    return url


@officeBlueprint.route('/<siret>/download')
def download(siret=None):
    """
    Download the PDF of an office.
    """
    try:
        office = Office.query.filter(Office.siret == siret).one()
    except NoResultFound:
        abort(404)
    attachment_name = 'fiche_entreprise_%s.pdf' % slugify(office.name, separator='_')
    full_path = pdf_util.get_file_path(office)
    if os.path.exists(full_path):
        return send_file(full_path, mimetype='application/pdf', as_attachment=True, attachment_filename=attachment_name)
    else:
        dic = detail(siret)
        office = dic['company']
        pdf_target = StringIO.StringIO()
        dic['stages'] = CONTACT_MODE_STAGES[dic['contact_mode']]
        dic['date'] = date.today()
        pdf_data = render_template('office/pdf_detail.html', **dic)
        pisa.CreatePDF(StringIO.StringIO(pdf_data), pdf_target, link_callback=fetch_resources)
        data_to_write = pdf_target.getvalue()
        response = make_response(data_to_write)
        pdf_util.write_file(office, data_to_write)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=%s' % attachment_name
        return response
