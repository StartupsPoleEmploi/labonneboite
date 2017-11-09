# coding: utf8

import urllib

from flask import Blueprint, Markup
from flask import abort, current_app, flash, redirect, render_template, request, send_file, url_for

import flask_login
from flask_login import current_user
from flask_wtf import csrf
from social_flask_sqlalchemy.models import UserSocialAuth

from labonneboite.common.database import db_session
from labonneboite.common.models import get_user_social_auth
from labonneboite.common.models import Office
from labonneboite.common.models import User
from labonneboite.common.models import UserFavoriteOffice
from labonneboite.common import pro
from labonneboite.common import util
from labonneboite.web.auth.views import logout
from labonneboite.web.office import pdf as pdf_util
from labonneboite.web.pagination import Pagination
from labonneboite.web.user.forms import UserAccountDeleteForm


userBlueprint = Blueprint('user', __name__)


@userBlueprint.route('/account')
@flask_login.login_required
def account():
    """
    The current user account main page.
    """
    return render_template('user/account.html')


@userBlueprint.route('/account/delete', methods=['GET', 'POST'])
@flask_login.login_required
def account_delete():
    """
    Ask for a confirmation, then delete the current user account and all of its information.
    """
    form = UserAccountDeleteForm(request.form)

    if request.method == 'POST' and form.validate():

        # Store the current `UserSocialAuth` instance in memory because it will be deleted
        # but it will also be needed later to properly logout the user from PEAM.
        user_social_auth = get_user_social_auth(current_user.id)

        # Now we can safely delete the current `UserSocialAuth` instance.
        # We have to delete it because it has a foreign key to the User table.
        # We don't need to deal with the other tables of Social Auth, see:
        # https://python-social-auth.readthedocs.io/en/latest/storage.html
        db_session.query(UserSocialAuth).filter_by(id=user_social_auth.id).delete()

        # Delete the current user.
        # The user's favorites will be deleted at the same time because of the `ondelete='CASCADE'`
        # on the `user_id` field of the `UserFavoriteOffice` model.
        db_session.query(User).filter_by(id=current_user.id).delete()

        db_session.commit()

        message = u"La suppression de votre compte a bien été effectuée."
        flash(message, 'warning')

        # Return the `logout` view directly. It allows us to pass the full
        # `user_social_auth` object as a parameter.
        return logout(user_social_auth=user_social_auth)

    context = {
        'form': form,
    }
    return render_template('user/account_delete.html', **context)


@userBlueprint.route('/favorites/list')
@flask_login.login_required
def favorites_list():
    """
    List the favorites offices of a user.
    """
    try:
        page = int(request.args.get('page'))
    except (TypeError, ValueError):
        page = 1

    favorites = UserFavoriteOffice.query.filter(UserFavoriteOffice.user_id == current_user.id)
    limit = 10
    pagination = Pagination(page, limit, favorites.count())
    if page > 1:
        favorites = favorites.offset((page - 1) * limit)
    favorites = favorites.limit(limit)

    context = {
        'favorites': favorites,
        'pagination': pagination,
        'show_favorites': True,
    }
    return render_template('user/favorites_list.html', **context)


@userBlueprint.route('/favorites/add/<siret>', methods=['POST'])
@flask_login.login_required
def favorites_add(siret):
    """
    Add an office to the favorites of a user.
    """

    # Since we are not using a FlaskForm but a hidden input with the token in the
    # form, CSRF validation has to be done manually.
    # CSRF validation can be disabled globally (e.g. in unit tests), so ensure that
    # `WTF_CSRF_ENABLED` is enabled before.
    if current_app.config['WTF_CSRF_ENABLED']:
        csrf.validate_csrf(request.form.get('csrf_token'))

    office = Office.query.filter_by(siret=siret).first()
    if not office:
        abort(404)

    UserFavoriteOffice.get_or_create(user=current_user, office=office)

    message = u'"%s - %s" a été ajouté à vos favoris !' % (office.name, office.city)
    flash(Markup(message), 'success')

    next_url = request.form.get('next')
    if next_url and util.is_safe_url(next_url):
        return redirect(urllib.unquote(next_url))

    return redirect(url_for('user.favorites_list'))


@userBlueprint.route('/favorites/delete/<siret>', methods=['POST'])
@flask_login.login_required
def favorites_delete(siret):
    """
    Delete an office from the favorites of a user.
    """

    # Since we are not using a FlaskForm but a hidden input with the token in the
    # form, CSRF validation has to be done manually.
    # CSRF validation can be disabled globally (e.g. in unit tests), so ensure that
    # `WTF_CSRF_ENABLED` is enabled before.
    if current_app.config['WTF_CSRF_ENABLED']:
        csrf.validate_csrf(request.form.get('csrf_token'))

    fav = UserFavoriteOffice.query.filter_by(office_siret=siret, user_id=current_user.id).first()
    if not fav:
        abort(404)

    fav.delete()

    message = u'"%s - %s" a été supprimé de vos favoris !' % (fav.office.name, fav.office.city)
    flash(message, 'success')

    next_url = request.form.get('next')
    if next_url and util.is_safe_url(next_url):
        return redirect(urllib.unquote(next_url))

    return redirect(url_for('user.favorites_list'))


@userBlueprint.route('/favorites/download')
@flask_login.login_required
def favorites_download():
    favorites = UserFavoriteOffice.query.filter(UserFavoriteOffice.user_id == current_user.id)
    # TODO this is probably wildly inefficient. Can we do this in just one query?
    companies = [favorite.office for favorite in favorites]
    pdf_file = pdf_util.render_favorites(companies)
    return send_file(pdf_file, mimetype='application/pdf', as_attachment=True, attachment_filename='mes_favoris.pdf')


@userBlueprint.route('/pro-version')
def pro_version():
    """
    Enable or disable "Version PRO" which is only visible to "PRO users".
    """
    if not pro.user_is_pro:
        abort(401)

    pro.toggle_pro_version()

    redirect_url = request.args.get('next', '/')

    if not util.is_safe_url(redirect_url):
        redirect_url = '/'

    return redirect(redirect_url)
