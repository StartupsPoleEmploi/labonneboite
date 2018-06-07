# coding: utf8

from urllib import urlencode

from flask import redirect, render_template, flash
from flask import Blueprint, current_app
from flask import url_for

from labonneboite.common.email_util import MandrillClient
from labonneboite.common.models import Office, OfficeAdminAdd, OfficeAdminUpdate, OfficeAdminRemove
from labonneboite.web.contact_form.forms import OfficeContactPreForm, OfficePromoteForm, OfficeUpdateCoordinatesForm, OfficeDeleteForm, OfficeFormCommon

contactFormBlueprint = Blueprint('contact_form', __name__)


REDIRECT_URLS = {
    'promote': 'contact_form.promote_form',
    'remove': 'contact_form.delete_form',
    'update': 'contact_form.update_coordinates_form',
    'other': 'contact_form.other_form',
}

@contactFormBlueprint.route('/verification-informations-entreprise/<siret>')
def change_info_or_apply_for_job(siret):
    """
    Ask user if he wants to change company information or apply for a job,
    in order to avoid the change_info page to be spammed so much by
    people thinking they are actually applying for a job.
    """
    return render_template('contact_form/change_info_or_apply_for_job.html', siret=siret)


@contactFormBlueprint.route('/postuler/<siret>')
def apply_for_job(siret):
    """
    If user arrives here, it means we successfully avoided having him spam the
    company modification form. Now we just have to explain him what is wrong.
    """
    return render_template('contact_form/apply_for_job.html', siret=siret)


@contactFormBlueprint.route('/informations-entreprise', methods=['GET', 'POST'])
def change_info():
    """
    Let a user fill a form to request a removal or information change about an office.
    """
    form = OfficeContactPreForm()
    if form.validate_on_submit():
        try:
            action = REDIRECT_URLS[form.data['action']]
            return redirect(url_for(action, siret=form.data['siret']))
        except KeyError:
            pass

    return render_template('contact_form/change_info.html', title='', submit_text=u'Allez au formulaire', form=form)


@contactFormBlueprint.route('/informations-entreprise/promouvoir/<siret>', methods=['GET', 'POST'])
def promote_form(siret):
    form = OfficePromoteForm()
    return render_template('contact_form/change_info.html', title='', form=form)


@contactFormBlueprint.route('/informations-entreprise/modifier-coordonnees/<siret>', methods=['GET', 'POST'])
def update_coordinates_form(siret):
    form = OfficeUpdateCoordinatesForm()
    return render_template('contact_form/change_info.html', title='', form=form)


@contactFormBlueprint.route('/informations-entreprise/supprimer/<siret>', methods=['GET', 'POST'])
def delete_form(siret):
    form = OfficeDeleteForm()
    return render_template('contact_form/change_info.html', title='', form=form)


@contactFormBlueprint.route('/informations-entreprise/supprimer/<siret>', methods=['GET', 'POST'])
def other_form(siret):
    form = OfficeFormCommon()
    if form.validate_on_submit():
        # TODO : generate_mail_content
        pass
    return render_template('contact_form/change_info.html', form=form)




def make_update_mail(form):
    pass

def make_promote_mail(form):
    pass


def make_delete_mail(form):
    pass


def make_other_mail(form):
    r




def make_save_suggestion(form):
    """
    TODO : improve this form to add more data in the generated link (like new_website, new_phone, new_phone_alternance)
    """

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
    office_admin_update = OfficeAdminUpdate.query.filter(
        OfficeAdminUpdate.sirets.like("%{}%".format(form.siret.data))
    ).first()

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
    params = {key: value.encode('utf8') for key, value in params.iteritems()}
    if form.action.data == "remove":
        url = url_for('officeadminremove.create_view')
        status_save = u" Une suppression a été demandée : <a href='%s'>Créer une fiche de suppression</a>"
    else:
        url = url_for('officeadminupdate.create_view')
        status_save = u"Entreprise non modifiée via Save : <a href='%s'>Créer une fiche de modification</a>"

    url = "%s?%s" % (url, urlencode(params))
    status_save = status_save % dirty_fix_url(url)
    return status_save