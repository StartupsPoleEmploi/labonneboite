# coding: utf8
import logging

from flask import Blueprint, render_template, request, url_for
from flask_login import current_user

from labonneboite.common.models.office import Office
from . import utils


logger = logging.getLogger('main')
tilkeeBlueprint = Blueprint('tilkee', __name__)


@tilkeeBlueprint.route('/upload', methods=['GET', 'POST'])
def upload():
    company = Office.query.filter_by(siret=request.args.get('siret')).first()
    if not company:
        return 'Cette entreprise n\'existe pas', 400

    error_template = None
    if not current_user.is_authenticated:
        error_template = "tilkee/login.html"
    elif not current_user.email:
        error_template = "tilkee/missing_email.html"
    if error_template:
        next_url = request.referrer + u'#company-{}'.format(company.siret) if request.referrer else ''
        login_url = url_for('social.auth', backend='peam-openidconnect', next=next_url)
        return render_template(error_template, login_url=login_url)

    if request.method == 'GET':
        return render_template("tilkee/upload.html", company=company)

    files = request.files.getlist('files')
    if not files:
        return u'Aucun fichier sélectionné', 400

    try:
        project_url = utils.process(files, company, current_user)
    except utils.TilkeeError as e:
        logger.exception(e)
        return render_template("tilkee/error.html")

    return render_template('tilkee/uploaded.html', project_url=project_url)


@tilkeeBlueprint.route('/postuler')
def postuler():
    if not current_user.is_authenticated:
        return render_template("tilkee/login.html")
