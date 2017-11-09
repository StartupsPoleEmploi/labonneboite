# coding: utf8

from slugify import slugify
from sqlalchemy.orm.exc import NoResultFound

from flask import abort, redirect, render_template, flash
from flask import Blueprint, current_app
from flask import send_file
from flask import request, url_for

from labonneboite.common.email_util import MandrillClient
from labonneboite.common.models import Office
from labonneboite.conf import settings

from labonneboite.web.office.forms import OfficeRemovalForm
from . import pdf as pdf_util


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
                - Commentaire : %s<br><br>
                Cordialement,<br>
                La Bonne Boite""" % (
                    form.action.data,
                    form.siret.data,
                    form.first_name.data,
                    form.last_name.data,
                    form.email.data,
                    form.phone.data,
                    form.comment.data,
               )
            )
            msg = u"Merci pour votre message, nous reviendrons vers vous dès que possible."
            flash(msg, 'success')

        except Exception as e:  # pylint: disable=W0703
            current_app.logger.error(
                u"/informations-entreprise - An error occurred while sending an email: %s", e.message)
            msg = u"Erreur dans l'envoi du mail, vous pouvez envoyer un email directement à %s" % settings.CONTACT_EMAIL
            flash(msg, 'error')

        return redirect(url_for('office.change_info'))
    return render_template('office/change_info.html', form=form)


@officeBlueprint.route('/<siret>/download')
def download(siret=None):
    """
    Download the PDF of an office.
    """
    try:
        office = Office.query.filter(Office.siret == siret).one()
    except NoResultFound:
        abort(404)

    rome = request.args.get('r')
    rome = rome if rome in settings.ROME_DESCRIPTIONS else None
    full_path = pdf_util.render(office, rome)
    attachment_name = 'fiche_entreprise_%s.pdf' % slugify(office.name, separator='_')
    return send_file(full_path, mimetype='application/pdf', as_attachment=True, attachment_filename=attachment_name)
