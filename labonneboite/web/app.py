# coding: utf8

# Python standard library.
from urllib.parse import urlparse
import locale
import logging

# External packages.
from raven.contrib.flask import Sentry
from social_core import exceptions as social_exceptions
from social_flask_sqlalchemy.models import init_social
from werkzeug.contrib.fixers import ProxyFix

# Flask.
from flask import g, flash, Flask, redirect, render_template, request, session, url_for
from flask_admin import Admin
from flask_assets import Environment, Bundle
from flask_babelex import Babel
from flask_login import current_user, LoginManager
from flask_mandrill import Mandrill
from flask_wtf.csrf import CSRFProtect

# labonneboite.
from labonneboite.common import hotjar
from labonneboite.common import pro
from labonneboite.common.database import db_session, engine  # This is how we talk to the database.
from labonneboite.common.models import User
from labonneboite.common.models import Office
from labonneboite.conf import settings

# labonneboite web.
from labonneboite.web.auth import utils as auth_utils
from labonneboite.web.auth.backends.exceptions import AuthFailedMissingReturnValues
from labonneboite.web.config import CONFIG
from labonneboite.web.jepostule.utils import jepostule_enabled


# Fix a bug with Python 2, strftime and Unicode.
# http://www.regisblog.fr/2015/01/08/python-strftime-unicode/
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')


# The login manager contains the code that lets the application and Flask-Login
# work together, such as how to load a user from an ID, where to send users when
# they need to log in, and the like:
# http://flask-login.readthedocs.io/en/0.4.0/#flask_login.LoginManager
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    """
    Tell the login manager how to reload the user object from the user ID stored in the session:
    http://flask-login.readthedocs.io/en/0.4.0/#flask_login.LoginManager.user_loader
    """
    return User.get(user_id)


def activate_logging(flask_app):
    """
    Activate the logging system.
    http://flask.pocoo.org/docs/0.12/errorhandling/
    """
    main_logger = logging.getLogger('main')
    main_logger.setLevel(settings.LOG_LEVEL)
    flask_app.logger.setLevel(settings.LOG_LEVEL)
    engine.logger.setLevel(settings.LOG_LEVEL_DB_ENGINE)

    # We are happy with how the flask app logger is configured, so we just copy
    # its configuration for the main and sqlalchemy loggers
    for handler in flask_app.logger.handlers:
        main_logger.addHandler(handler)
        engine.logger.addHandler(handler)

    if settings.SENTRY_DSN:
        Sentry(flask_app, dsn=settings.SENTRY_DSN, logging=True, level=logging.ERROR)
        flask_app.logger.debug("sentry is enabled")
    else:
        flask_app.logger.debug("sentry is disabled")


def register_extensions(flask_app):
    """
    Register Flask extensions.
    """
    Babel(flask_app)  # Babel is currently only used with Flask-Admin.
    CSRFProtect(flask_app)  # Enable CSRF protection globally.
    mandrill = Mandrill()
    mandrill.init_app(flask_app)
    flask_app.extensions['mandrill'] = mandrill  # Provide easy access to the mandrill extension in Blueprints.
    login_manager.init_app(flask_app)
    init_social(flask_app, db_session)


def register_blueprints(flask_app):
    """
    Register Flask blueprints to split the application into small modules.
    """
    from labonneboite.web.api.views import apiBlueprint
    from labonneboite.web.auth.views import authBlueprint
    from labonneboite.web.data.views import dataBlueprint
    from labonneboite.web.health.views import healthBlueprint
    from labonneboite.web.maps.views import mapsBlueprint
    from labonneboite.web.office.views import officeBlueprint
    from labonneboite.web.contact_form.views import contactFormBlueprint
    from labonneboite.web.jepostule.views import jepostuleBlueprint
    from labonneboite.web.root.views import rootBlueprint
    from labonneboite.web.search.views import searchBlueprint
    from labonneboite.web.tilkee.views import tilkeeBlueprint
    from labonneboite.web.user.views import userBlueprint
    from social_flask.routes import social_auth
    flask_app.register_blueprint(apiBlueprint, url_prefix='/api/v1')
    flask_app.register_blueprint(authBlueprint, url_prefix='/authentication')
    flask_app.register_blueprint(dataBlueprint, url_prefix='/data')
    flask_app.register_blueprint(healthBlueprint, url_prefix='/health')
    flask_app.register_blueprint(mapsBlueprint, url_prefix='/maps')
    flask_app.register_blueprint(officeBlueprint)
    flask_app.register_blueprint(contactFormBlueprint)
    flask_app.register_blueprint(jepostuleBlueprint, url_prefix='/jepostule')
    flask_app.register_blueprint(rootBlueprint)
    flask_app.register_blueprint(searchBlueprint)
    flask_app.register_blueprint(tilkeeBlueprint, url_prefix='/candidature')
    flask_app.register_blueprint(userBlueprint, url_prefix='/user')
    flask_app.register_blueprint(social_auth, url_prefix='/authorize')


def register_admin(flask_app):
    """
    Register Flask admin views.
    """
    from labonneboite.web.admin.views.index import LbbAdminIndexView
    admin = Admin(flask_app, name='Administration LBB', index_view=LbbAdminIndexView(), template_mode='bootstrap3')

    from labonneboite.web.admin.views.user import UserModelView
    # Use the `endpoint` argument to avoid a Blueprint name collision:
    # https://github.com/flask-admin/flask-admin/issues/1474
    admin.add_view(UserModelView(User, db_session, endpoint='users', name='Utilisateurs'))

    from labonneboite.common.models import OfficeAdminAdd
    from labonneboite.web.admin.views.office_admin_add import OfficeAdminAddModelView
    admin.add_view(OfficeAdminAddModelView(OfficeAdminAdd, db_session, name='Ajouter une entreprise'))

    from labonneboite.common.models import OfficeAdminRemove
    from labonneboite.web.admin.views.office_admin_remove import OfficeAdminRemoveModelView
    admin.add_view(OfficeAdminRemoveModelView(OfficeAdminRemove, db_session, name='Supprimer une entreprise'))

    from labonneboite.common.models import OfficeAdminUpdate
    from labonneboite.web.admin.views.office_admin_update import OfficeAdminUpdateModelView
    admin.add_view(OfficeAdminUpdateModelView(OfficeAdminUpdate, db_session, name='Modifier une entreprise'))

    from labonneboite.common.models import OfficeAdminExtraGeoLocation
    from labonneboite.web.admin.views.office_admin_extra_geolocation import OfficeAdminExtraGeoLocationModelView
    admin.add_view(OfficeAdminExtraGeoLocationModelView(OfficeAdminExtraGeoLocation, db_session,
        name='Géolocalisations'))


def register_before_requests(flask_app):
    """
    Register before_request functions.
    """
    def global_user():
        """
        Retrieve the current user from Flask-Login and make it available
        to the current thread via the Flask `g` object:
        https://github.com/python-social-auth/social-examples/blob/15f87f/example-flask/example/__init__.py#L57-L60
        """
        g.user = current_user._get_current_object()

    def make_session_permanent():
        """
        Make the session permanent. Flask defaults to timedelta(days=31).
        """
        session.permanent = True

    flask_app.before_request(global_user)
    flask_app.before_request(make_session_permanent)


def register_context_processors(flask_app):
    """
    Register context_processor functions.
    """
    def inject_dict_for_all_templates():
        return {
            'hotjar_tag': hotjar.get_hotjar_tag(),
            'memo_js_url': settings.MEMO_JS_URL,
            'user_is_pro': pro.user_is_pro(),
            'pro_version_enabled': pro.pro_version_enabled(),
            'last_data_deploy_date': Office.get_date_of_last_data_deploy(),
            'google_analytics_id': settings.GOOGLE_ANALYTICS_ID,
            'seo_google_analytics_id': settings.SEO_GOOGLE_ANALYTICS_ID,
            'enable_google_optimize': settings.ENABLE_GOOGLE_OPTIMIZE,
            'google_optimize_id': settings.GOOGLE_OPTIMIZE_ID,
            'tilkee_enabled': settings.TILKEE_ENABLED,
            'google_site_verification_code': settings.GOOGLE_SITE_VERIFICATION_CODE,
            'login_url': auth_utils.login_url,
            'jepostule_globally_enabled': settings.JEPOSTULE_QUOTA > 0,
        }

    def inject_user():
        """
        Make current user available in templates.
        """
        try:
            return {'user': g.user}
        except AttributeError:
            return {'user': None}

    def inject_jepostule_enabled():
        return {'jepostule_enabled': jepostule_enabled}

    flask_app.context_processor(inject_dict_for_all_templates)
    flask_app.context_processor(inject_user)
    flask_app.context_processor(inject_jepostule_enabled)


def register_teardown_appcontext(flask_app):
    """
    Register teardown_appcontext functions.
    """
    def shutdown_session(exception=None):
        db_session.remove()
        engine.dispose()
    flask_app.teardown_appcontext(shutdown_session)


def create_app():

    flask_app = Flask(__name__)
    flask_app.config.from_object(CONFIG)

    # The application is deployed on servers behind an HTTP proxy, we need ProxyFix
    # and the X-Forwarded-* HTTP headers in the proxy configuration.
    # http://flask.pocoo.org/docs/0.12/deploying/wsgi-standalone/#proxy-setups
    flask_app.wsgi_app = ProxyFix(flask_app.wsgi_app)

    if CONFIG.DEBUG:
        try:
            from flask_debugtoolbar import DebugToolbarExtension
            flask_app.config['DEBUG_TB_PROFILER_ENABLED'] = True
            flask_app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
            DebugToolbarExtension(flask_app)
        except ImportError:
            pass

    register_extensions(flask_app)
    register_blueprints(flask_app)
    register_admin(flask_app)
    register_before_requests(flask_app)
    register_context_processors(flask_app)
    register_teardown_appcontext(flask_app)
    register_teardown_appcontext(flask_app)

    # Assets.
    assets = Environment(app=flask_app)
    js = Bundle(
        # Vendor.
        'js/vendor/jquery.min.js',
        'js/vendor/jquery-ui.1.11.4.min.js',
        'js/vendor/bootstrap-tooltip.js',
        'js/vendor/js.cookie.js',
        # LBB.
        'js/alerts.js',
        'js/rgpd.js',
        'js/clipboard.js',
        'js/dropdowns.js',
        'js/homepage-form.js',
        'js/map.js',
        'js/modal.js',
        'js/prevent-double-form-submit.js',
        'js/results-toggle-sidebar.js',
        'js/results.js',
        'js/tilkee.js',
        'js/toggle-long-text.js',
        'js/tooltip.js',  # Depends on 'js/vendor/bootstrap-tooltip.js'.
        'js/unobfuscate.js',
        'js/transparent-sso.js',
        filters='jsmin',
        output='gen/packed.%(version)s.js',
    )
    assets.register('js_all', js)

    assets.register(
        'recruiter_form',
        Bundle(
            'js/recruiter-forms.js',
            filters='jsmin',
            output='gen/packed.recruiter_form.%(version)s.js',
        )
    )

    css = Bundle(
        # LBB.
        'css/_base.css',  # Order is important.
        'css/_global_classes.css',  # Order is important.
        'css/_layout.css',  # Order is important.
        'css/alerts.css',
        'css/badges.css',
        'css/breadcrumb.css',
        'css/buttons.css',
        'css/cookbook.css',
        'css/rgpd_banner.css',
        'css/doorbell.css',
        'css/dropdowns.css',
        'css/forms.css',
        'css/grid.css',
        'css/jepostule.css',
        'css/home.css',
        'css/modal.css',
        'css/pagination.css',
        'css/progressbar.css',
        'css/ratings.css',
        'css/search_results.css',
        'css/switch.css',
        'css/tilkee.css',
        # Vendor.
        'css/vendor/bootstrap-tooltip.css',
        'css/vendor/jquery-ui.css',
        # Vendor overrides
        'css/tooltip.css',
        filters='cssmin',
        output='gen/packed.%(version)s.css',
    )
    assets.register('css_all', css)

    return flask_app


app = create_app()

activate_logging(app)


def log_extra_context():
    extra = (
        ('ip', request.remote_addr),
        ('method', request.method),
        ('path', request.full_path),
    )
    extra_msg = " - ".join([(i[1] or '') for i in extra])
    return extra_msg


@app.errorhandler(social_exceptions.AuthException)
@app.errorhandler(AuthFailedMissingReturnValues)
def social_auth_error(error):
    """
    Handle the situation where a user clicks the `cancel` button on a third party auth provider website.
    """
    flash_message = "Une erreur est survenue lors de votre connexion. Veuillez réessayer."

    # Don't log errors that are not our responsibility
    if isinstance(error, social_exceptions.AuthFailed) and error.args[0] == 'The request requires some interaction that is not allowed.':
        # We thought user was connected on PE.fr, but in fact he wasn't, so we
        # can't log the user in without interaction
        pass
    elif isinstance(error, social_exceptions.AuthForbidden):
        # "Your credentials aren't allowed"
        pass
    elif isinstance(error, (social_exceptions.AuthMissingParameter, AuthFailedMissingReturnValues)):
        flash_message = "Veuillez vérifier vos emails et procéder à la validation de votre compte Pôle Emploi."
    elif not isinstance(error, (
            social_exceptions.AuthCanceled,
            social_exceptions.AuthUnreachableProvider,
            social_exceptions.AuthStateForbidden,
            social_exceptions.AuthStateMissing,
    )):
        app.logger.exception(error)
    flash(flash_message, 'error')

    # If there us a next url in session and it's safe, redirect to it.
    next_url = session.get('next')
    if next_url:
        parsed_host_url = urlparse(request.host_url)
        parsed_next_url = urlparse(next_url)
        if parsed_host_url.netloc == parsed_next_url.netloc and parsed_next_url.scheme in ('http', 'https'):
            return redirect(next_url)
    # Otherwise redirect to the home page.
    return redirect(url_for('root.home'))

@app.errorhandler(401)
def error_401(error):
    return render_template('error/401.html'), 401


@app.errorhandler(404)
def error_404(error):
    return render_template('error/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    # Exception was already logged by flask somewhere, no need to process it
    return render_template('error/500.html'), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0')
