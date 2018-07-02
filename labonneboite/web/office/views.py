# coding: utf8

from datetime import date
import os

from slugify import slugify
from sqlalchemy.orm.exc import NoResultFound

from flask import abort, render_template
from flask import Blueprint
from flask import make_response, send_file
from flask import request, session

from labonneboite.common import pdf as pdf_util
from labonneboite.common import util
from labonneboite.conf import settings
from labonneboite.common.contact_mode import CONTACT_MODE_STAGES
from labonneboite.common.models import Office

officeBlueprint = Blueprint('office', __name__)


@officeBlueprint.route('/<siret>/details')
def details(siret):
    """
    Display the details of an office.
    In case the context of a rome_code is given, display appropriate score value for this rome_code
    """
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
    return render_template('office/details.html', **context)


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

    contact_mode = util.get_contact_mode_for_rome_and_office(rome, company)

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


@officeBlueprint.route('/<siret>/download')
def download(siret):
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

        contact_mode = dic['contact_mode']
        dic['stages'] = CONTACT_MODE_STAGES.get(contact_mode, [contact_mode])
        dic['date'] = date.today()

        # Render pdf file
        pdf_data = render_template('office/pdf_detail.html', **dic)
        pdf_target = pdf_util.convert_to_pdf(pdf_data)
        data_to_write = pdf_target.getvalue()
        pdf_util.write_file(office, data_to_write)

        # Return pdf
        response = make_response(data_to_write)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=%s' % attachment_name
        return response
