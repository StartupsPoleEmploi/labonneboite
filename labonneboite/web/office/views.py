# coding: utf8

import os

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
    }
    activity.log('details', siret=siret)
    return render_template('office/details.html', **context)


@officeBlueprint.route('/<siret>/download')
def download(siret):
    """
    Download the PDF of an office.
    """
    try:
        office = Office.query.filter(Office.siret == siret).one()
    except NoResultFound:
        abort(404)

    activity.log('telecharger-pdf', siret=siret)

    attachment_name = 'fiche_entreprise_%s.pdf' % slugify(office.name, separator='_')
    full_path = pdf_util.get_file_path(office)
    if os.path.exists(full_path):
        return send_file(full_path, mimetype='application/pdf', as_attachment=True, attachment_filename=attachment_name)

    # Render pdf file
    contact_mode = util.get_contact_mode_for_rome_and_office(None, office)
    pdf_data = render_template('office/pdf_detail.html', **{
        'company': office,
        'contact_mode': contact_mode,
        'stages': CONTACT_MODE_STAGES.get(contact_mode, [contact_mode]),
    })
    pdf_target = pdf_util.convert_to_pdf(pdf_data)
    data_to_write = pdf_target.getvalue()
    pdf_util.write_file(office, data_to_write)

    # Return pdf
    response = make_response(data_to_write)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=%s' % attachment_name
    return response


@officeBlueprint.route('/events/toggle-details/<siret>', methods=['POST'])
def toggle_details_event(siret):
    try:
        Office.query.filter(Office.siret == siret).one()
    except NoResultFound:
        abort(404)

    activity.log('afficher-details', siret=siret)
    return jsonify({})
