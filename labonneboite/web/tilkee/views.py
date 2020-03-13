import logging

from flask import Blueprint, render_template, request
from flask.helpers import BadRequest
from flask_login import current_user

from labonneboite.common.models.office import Office
from labonneboite.conf import settings
from labonneboite.web.auth.utils import login_url

from . import utils


logger = logging.getLogger("main")
tilkeeBlueprint = Blueprint("tilkee", __name__)


@tilkeeBlueprint.route("/upload", methods=["GET", "POST"])
def upload():
    if not settings.TILKEE_ENABLED:
        raise BadRequest

    company = Office.query.filter_by(siret=request.args.get("siret")).first()
    if not company:
        return "Cette entreprise n'existe pas", 400

    error_template = None
    if not current_user.is_authenticated:
        error_template = "tilkee/login.html"
    elif not current_user.email:
        error_template = "tilkee/missing_email.html"
    if error_template:
        next_url = request.referrer + "#company-{}".format(company.siret) if request.referrer else ""
        return render_template(error_template, login_url=login_url(next_url=next_url))

    if request.method == "GET":
        return render_template("tilkee/upload.html", company=company, file_extensions=utils.ALLOWED_FILE_EXTENSIONS)

    return upload_files(company, request.files.getlist("files"))


def upload_files(company, files):
    if not files:
        return "Aucun fichier sélectionné", 400
    for f in files:
        filename = f.filename
        if not utils.is_allowed(filename):
            return "Fichier non supporté: {}".format(filename), 400

    try:
        project_url = utils.process(files, company, current_user)
    except utils.TilkeeError as e:
        logger.exception(e)
        return render_template("tilkee/error.html")

    return render_template("tilkee/uploaded.html", project_url=project_url)


@tilkeeBlueprint.route("/postuler")
def postuler():
    if not current_user.is_authenticated:
        return render_template("tilkee/login.html")
    return None
