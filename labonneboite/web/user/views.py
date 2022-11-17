import time
import urllib.error
import urllib.parse
import urllib.request
import io
from typing import Optional

from flask import Blueprint, Markup
from flask import abort, current_app, flash, make_response
from flask import redirect, render_template, request, send_file, url_for

import flask_login
from flask_login import current_user
from flask_wtf import csrf
from social_flask_sqlalchemy.models import UserSocialAuth

from labonneboite.common import activity, csv
from labonneboite.common.database import db_session
from labonneboite.common.models import get_user_social_auth
from labonneboite.common.models import Office
from labonneboite.common.models import User
from labonneboite.common.models import UserFavoriteOffice
from labonneboite.common import pdf as pdf_util
from labonneboite.common import pro
from labonneboite.common import util
from labonneboite.web.auth.views import logout
from labonneboite.common.pagination import Pagination, FAVORITES_PER_PAGE
from labonneboite.web.user.forms import UserAccountDeleteForm
from labonneboite.web.utils import fix_csrf_session
from labonneboite.web import WEB_DIR

userBlueprint = Blueprint('user', __name__)


@userBlueprint.route('/account')
@flask_login.login_required
def account():
    """
    The current user account main page.
    """
    fix_csrf_session()
    user_social_auth = get_user_social_auth(current_user.id)
    context = {}
    if user_social_auth:
        context['token'] = user_social_auth.extra_data['access_token']
        context['token_age_in_seconds'] = int(
            time.time()) - user_social_auth.extra_data['auth_time'],
    return render_template('user/account.html', **context)


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
        db_session.query(UserSocialAuth).filter_by(
            user_id=current_user.id).delete()

        # Delete the current user.
        # The user's favorites will be deleted at the same time because of the `ondelete='CASCADE'`
        # on the `user_id` field of the `UserFavoriteOffice` model.
        db_session.query(User).filter_by(id=current_user.id).delete()

        db_session.commit()

        message = "La suppression de votre compte a bien été effectuée."
        flash(message, 'warning')

        # Return the `logout` view directly. It allows us to pass the full
        # `user_social_auth` object as a parameter.
        return logout(user_social_auth=user_social_auth)

    context = {
        'form': form,
    }
    return render_template('user/account_delete.html', **context)


@userBlueprint.route('/account/download/csv')
@flask_login.login_required
def personal_data_as_csv():
    """
    Download as a CSV the personal data of a user.
    """
    output = io.StringIO()
    writer = csv.writer(output, dialect='excel-semi')
    writer.writerow(['prénom', 'nom', 'email'])
    writer.writerow([
        current_user.first_name,
        current_user.last_name,
        current_user.email,
    ])

    return make_csv_response(
        csv_text=output.getvalue(),
        attachment_name='mes_données_personnelles.csv',
    )


@userBlueprint.route('/favorites/list/download/csv')
@flask_login.login_required
def favorites_list_as_csv():
    """
    Download as a CSV the list of the favorited offices of a user.
    """
    return make_csv_response(
        csv_text=UserFavoriteOffice.user_favs_as_csv(current_user),
        attachment_name='mes_favoris.csv',
    )


@userBlueprint.route('/favorites/list/download/pdf')
@flask_login.login_required
def favorites_list_as_pdf():
    favorites = UserFavoriteOffice.query.filter(
        UserFavoriteOffice.user_id == current_user.id)
    # TODO this is probably wildly inefficient. Can we do this in just one query?
    companies = [favorite.office for favorite in favorites]
    pdf_file = pdf_util.render_favorites(companies, WEB_DIR)
    return send_file(pdf_file,
                     mimetype='application/pdf',
                     as_attachment=True,
                     attachment_filename='mes_favoris.pdf',
                     max_age=5)


def make_csv_response(csv_text, attachment_name):
    # Return csv file
    response = make_response(csv_text)
    response.headers['Content-Type'] = 'application/csv'
    response.headers[
        'Content-Disposition'] = 'attachment; filename=%s' % attachment_name
    return response


@userBlueprint.route('/favorites/list')
@flask_login.login_required
def favorites_list():
    """
    List the favorited offices of a user.
    """
    fix_csrf_session()
    try:
        page = int(request.args.get('page'))
    except (TypeError, ValueError):
        page = 1

    favorites = UserFavoriteOffice.query.filter(
        UserFavoriteOffice.user_id == current_user.id)
    limit = FAVORITES_PER_PAGE
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
@userBlueprint.route('/favorites/add/<siret>/<rome_code>', methods=['POST'])
@flask_login.login_required
def favorites_add(siret: str, rome_code: Optional[str] = None):
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

    UserFavoriteOffice.add_favorite(user=current_user,
                                    office=office,
                                    rome_code=rome_code)

    message = '"%s - %s" a été ajouté à vos favoris !' % (office.name,
                                                          office.city)
    flash(Markup(message), 'success')
    activity.log('ajout-favori', siret=siret)

    return get_redirect_after_favorite_operation()


def get_redirect_after_favorite_operation():
    next_url = request.form.get('next')
    if next_url:
        decoded_next_url = urllib.parse.unquote(next_url)
        if util.is_decoded_url_safe(decoded_next_url):
            return redirect(decoded_next_url)
        else:
            return 'invalid next_url', 400
    else:
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

    fav = UserFavoriteOffice.query.filter_by(office_siret=siret,
                                             user_id=current_user.id).first()
    if not fav:
        abort(404)

    fav.delete()

    message = '"%s - %s" a été supprimé de vos favoris !' % (fav.office.name,
                                                             fav.office.city)
    flash(message, 'success')
    activity.log('suppression-favori', siret=siret)

    return get_redirect_after_favorite_operation()


@userBlueprint.route('/pro-version')
def pro_version():
    """
    Enable or disable "Version PRO" which is only visible to "PRO users".
    """
    if not pro.user_is_pro():
        abort(401)

    pro.toggle_pro_version()

    redirect_url = urllib.parse.unquote(request.args.get('next', '/'))

    if not redirect_url or not util.is_decoded_url_safe(redirect_url):
        redirect_url = '/'

    return redirect(redirect_url)


@userBlueprint.route('/header.html')
def header():
    return render_template("user/header.html", next_url=request.referrer)
