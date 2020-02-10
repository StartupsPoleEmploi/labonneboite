
import os
import time

from slugify import slugify
from sqlalchemy.orm.exc import NoResultFound

from flask import abort, render_template, jsonify
from flask import Blueprint
from flask import make_response, send_file
from flask import request

from labonneboite.common import activity
from labonneboite.common import pdf as pdf_util
from labonneboite.common import util
from labonneboite.common.contact_mode import CONTACT_MODE_STAGES
from labonneboite.web.utils import fix_csrf_session
from labonneboite.common.models import Office
from labonneboite.conf import settings

officeBlueprint = Blueprint('office', __name__)


@officeBlueprint.route('/<siret>/details')
def details(siret):
    """
    Display the details of an office.
    In case the context of a rome_code is given, display appropriate score value for this rome_code
    """
    fix_csrf_session()
    rome_code = request.args.get('rome_code', None)
    company = Office.query.filter_by(siret=siret).first()
    if not company:
        abort(404)

    # Check if company is hidden by SAVE
    if not company.score:
        abort(404)

    context = {
        'company': company,
        'rome_code': rome_code,
        'hide_memo_introjs': True,
        'next_url_modal': f'{settings.SERVER_NAME}/jepostule/candidater/{siret}',
    }
    activity.log(
        event_name='details',
        siret=siret,
        # GA tracking is used in PSE 2019-2020 experiment
        utm_medium=request.args.get('utm_medium', ''),
        utm_source=request.args.get('utm_source', ''),
        utm_campaign=request.args.get('utm_campaign', ''),
    )
    return render_template('office/details.html', **context)


@officeBlueprint.route('/<siret>/download')
def download(siret):
    """
    Download the PDF of an office.
    """
    office = get_office_or_404(siret)

    activity.log('telecharger-pdf', siret=siret)

    attachment_name = 'fiche_entreprise_%s.pdf' % slugify(office.name, separator='_')
    pdf_path = office_detail_pdf_path(office)
    return send_file(pdf_path, mimetype='application/pdf', as_attachment=True, attachment_filename=attachment_name)


@officeBlueprint.route('/<siret>/download.html')
def download_html(siret):
    office = get_office_or_404(siret)
    return make_response(office_detail_html(office))


def get_office_or_404(siret):
    try:
        return Office.query.filter(Office.siret == siret).one()
    except NoResultFound:
        abort(404)


def office_detail_pdf_path(office):
    path = pdf_util.get_file_path(office)
    seconds_in_a_day = 24 * 60 * 60
    if os.path.exists(path) and time.time() - os.path.getmtime(path) > seconds_in_a_day:
        os.remove(path)
    if not os.path.exists(path):
        pdf_data = office_detail_html(office)
        pdf_target = pdf_util.convert_to_pdf(pdf_data)
        data_to_write = pdf_target.getvalue()
        pdf_util.write_file(office, data_to_write, path)
    return path


def office_detail_html(office):
    """
    Return the html corresponding to the office details.
    """
    contact_mode = util.get_contact_mode_for_rome_and_office(None, office)
    return render_template('office/pdf_detail.html', **{
        'company': office,
        'contact_mode': contact_mode,
        'stages': CONTACT_MODE_STAGES.get(contact_mode, [contact_mode]),
    })


@officeBlueprint.route('/events/toggle-details/<siret>', methods=['POST'])
def toggle_details_event(siret):
    try:
        Office.query.filter(Office.siret == siret).one()
    except NoResultFound:
        abort(404)

    activity.log('afficher-details', siret=siret)
    return jsonify({})
