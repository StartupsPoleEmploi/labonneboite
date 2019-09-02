# Authentication system
User instances are stored in the `labonneboite.common.models.auth.User` model.

To handle registration and login of users, we rely on the following tools:

- `Flask-Login` to manage Flask user session
- `Python Social Auth` to delegate identification and authentication

## Requirements

Requirements of the authentication system:

- [`Flask-Login`](https://github.com/maxcountryman/flask-login)
- [`social-auth-app-flask-sqlalchemy`](https://github.com/python-social-auth/social-app-flask-sqlalchemy) (explicit)
- [`social-auth-app-flask`](https://github.com/python-social-auth/social-app-flask) (explicit)
    - [`social-auth-core`](https://github.com/python-social-auth/social-core) (implicit)
        - `pyjwkest` (explicit, [see](https://github.com/python-social-auth/social-core/blob/0e2cce/requirements-openidconnect.txt))
    - [`social-auth-storage-sqlalchemy`](https://github.com/python-social-auth/social-storage-sqlalchemy) (implicit)

## Documentation and examples

- [Python Social Auth's documentation](https://python-social-auth.readthedocs.io/en/latest/)
- [Examples implementation of `python-social-auth` for Flask](https://github.com/python-social-auth/social-examples/tree/15f87f/example-flask)

## User session storage

The user is stored in the session which is a dictionary that the application can use to store values that are “remembered” between requests.

User sessions are stored in client-side cookies that are cryptographically signed using the configured `SECRET_KEY`. Any tampering with the cookie content would render the signature invalid, thus invalidating the session.

`Flask-Login` stores the active user's ID in the session, and let us log them in and out easily.

The whole mecanism is based on Flask sessions:

- [Flask Quickstart - Sessions](http://flask.pocoo.org/docs/0.12/quickstart/#sessions)
- [Flask API - Sessions](http://flask.pocoo.org/docs/0.12/api/#sessions)

## PEAM

PEAM stands for *Pôle Emploi Access Management*. See the [documentation](https://www-r.es-qvr-dev.fr/portail-developpeur-cms/home/catalogue-des-api/documentation-des-api/utiliser-les-api/authorization-code-flow.html).

One image of our project is used by the PEAM website: `logo-lbb-square.jpg`.

PEAM is built on top of the [OAuth2](https://oauth.net/2/) and [OpenIdConnect](http://openid.net/connect/) protocols:

- [OAuth 2 Simplified](https://aaronparecki.com/oauth-2-simplified/)
- [An Introduction to OAuth 2](https://www.digitalocean.com/community/tutorials/an-introduction-to-oauth-2)
- [OpenID Connect explained](https://connect2id.com/learn/openid-connect)

## The PEAM backend for `Python Social Auth`

`labonneboite.web.auth.backends.peam.PEAMOpenIdConnect` is a backend for `Python Social Auth` that allows us to register and login users using PEAM.

### High level flow

Here is how `Python Social Auth` is used to handle the OAuth2/OpenIdConnect *dance*:

1. A user click on the "Login with PEAM" link on LBB
2. The user is redirected to the PEAM website for identification and data-sharing agreement
3. The user is redirected to LBB with an `authorization code`
4. LBB use the `authorization code` to obtain an `access token` from PEAM
5. LBB gets an `access token` from PEAM
6. LBB use the `access token` to access a PEAM `userinfo` endpoint
7. The user is registered (an entry in the LBB database is created) and logged in

## PEAM backend flow with `Python Social Auth`

### Models used by `Python Social Auth`

[5 database tables](https://python-social-auth.readthedocs.io/en/latest/storage.html) are used by `Python Social Auth`.

- [`social_auth_usersocialauth`](https://github.com/python-social-auth/social-app-flask-sqlalchemy/blob/09610f/social_flask_sqlalchemy/models.py#L31) (used by the PEAM backend)
- [`social_auth_association`](https://github.com/python-social-auth/social-app-flask-sqlalchemy/blob/09610f/social_flask_sqlalchemy/models.py#L52) (used by the PEAM backend)
- [`social_auth_code`](https://github.com/python-social-auth/social-app-flask-sqlalchemy/blob/09610f/social_flask_sqlalchemy/models.py#L57) (unused by the PEAM backend, but could be used by another backend)
- [`social_auth_nonce`](https://github.com/python-social-auth/social-app-flask-sqlalchemy/blob/09610f/social_flask_sqlalchemy/models.py#L47) (unused by the PEAM backend, but could be used by another backend)
- [`social_auth_partial`](https://github.com/python-social-auth/social-app-flask-sqlalchemy/blob/09610f/social_flask_sqlalchemy/models.py#L62) (unused by the PEAM backend, but could be used by another backend)

### Detailed flow

This is a reminder of the highlights of the `Python Social Auth` flow with PEAM. We suggest that you use `ipdb` or a similar tool to fully grasp the flow. See also [*A stroll through the python-social-auth code*](http://www.leehodgkinson.com/blog/a-stroll-through-the-python-social-auth-code/).

1. We enter the PEAM flow by clicking on a "Login" link found in a LBB template: `{{ url_for('social.auth', backend='peam-openidconnect') }}`

2. When the link is clicked, it triggers the `social-auth-app-flask`'s [`auth` route](https://github.com/python-social-auth/social-app-flask/blob/747481/social_flask/routes.py#L11-L14):
    - the `@psa` decorator is triggered and sets:
        - `g.strategy` as [`social_flask.strategy.FlaskStrategy`](https://github.com/python-social-auth/social-app-flask/blob/747481/social_flask/strategy.py#L16-L56) (and `g.strategy.storage` as [`social_flask_sqlalchemy.models.FlaskStorage`](https://github.com/python-social-auth/social-app-flask-sqlalchemy/blob/09610f/social_flask_sqlalchemy/models.py#L67-L72))
        - `g.backend` as `labonneboite.web.auth.backends.peam.PEAMOpenIdConnect`
    - the `auth` route returns `social_core.actions.do_auth()`

3. [`social_core.actions.do_auth()`](https://github.com/python-social-auth/social-core/blob/0e2cce/social_core/actions.py#L7-L27) amongst other things:
    - stores a `nonce` in the `social_auth_association` ; a `nonce` is a unique value chosen by an entity in a protocol, and it is used to protect that entity against attacks which fall under the very large umbrella of "replay"
    - redirects the user to the PEAM website for identification and data-sharing agreement

4. After a successful identification on the PEAM website, the user is redirected to the LBB website on the `social-auth-app-flask`'s [`complete`](https://github.com/python-social-auth/social-app-flask/blob/747481/social_flask/routes.py#L17-L23) route with an `authorization code`:
    - the `@psa` decorator is triggered once again
    - the `auth` route returns `social_core.actions.do_complete()`

5. [`social_core.actions.do_complete()`](https://github.com/python-social-auth/social-core/blob/0e2cce/social_core/actions.py#L30-L98) goes through a number of steps:
    - [`backend.complete`](https://github.com/python-social-auth/social-core/blob/0e2cce/social_core/actions.py#L41) triggers `social_core.backends.base.complete()`
    - [`social_core.backends.base.complete()`](https://github.com/python-social-auth/social-core/blob/0e2cce/social_core/backends/base.py#L38-L39) triggers `social_core.backends.oauth.BaseOAuth2.auth_complete()`
    - [`social_core.backends.oauth.BaseOAuth2.auth_complete()`](https://github.com/python-social-auth/social-core/blob/0e2cce/social_core/backends/oauth.py#L383-L398):
        - validate the `state` parameter
        - fetches an `access_token` from PEAM
        - returns `social_core.backends.oauth.BaseOAuth2.do_auth()`
    - [`social_core.backends.oauth.BaseOAuth2.do_auth()`](https://github.com/python-social-auth/social-core/blob/0e2cce/social_core/backends/oauth.py#L400-L409):
        - fetches user data through the `userinfo` endpoint of PEAM
        - returns `social_core.strategy.BaseStrategy.authenticate()`
    - [`social_core.strategy.BaseStrategy.authenticate()`](https://github.com/python-social-auth/social-core/blob/0e2cce/social_core/strategy.py#L150-L157) returns `social_core.backends.base.authenticate()`
    - [`social_core.backends.base.authenticate()`](https://github.com/python-social-auth/social-core/blob/0e2cce/social_core/backends/base.py#L58-L79) returns `social_core.backends.base.pipeline()`
    - [`social_core.backends.base.pipeline()`](https://github.com/python-social-auth/social-core/blob/0e2cce/social_core/backends/base.py#L81-L89)
    - `social_core.backends.base.pipeline()` goes through [`social_core.backends.base.run_pipeline()`](https://github.com/python-social-auth/social-core/blob/0e2cce/social_core/backends/base.py#L97-L111) with the [`DEFAULT_AUTH_PIPELINE`](https://github.com/python-social-auth/social-core/blob/0e2cce/social_core/pipeline/__init__.py#L1-L43), some importants parts are:
        - [`social_core.pipeline.social_auth.social_user`](https://github.com/python-social-auth/social-core/blob/0e2cce/social_core/pipeline/social_auth.py#L17-L29) associates a social account data with a user in the system (in the `social_auth_usersocialauth` table)
        - [`social_core.pipeline.user.create_user`](https://github.com/python-social-auth/social-core/blob/0e2cce/social_core/pipeline/user.py#L64-L76) through [`social_sqlalchemy.storage.SQLAlchemyUserMixin.create_user()`](https://github.com/python-social-auth/social-storage-sqlalchemy/blob/e9223f/social_sqlalchemy/storage.py#L138-L140)

6. Then `social_core.actions.do_complete()` can finish his work:
    - check that the user is active (a check on the `active` User model field)
    - log the user in
    - redirect the user a LBB page

## Social Flask SQLAlchemy tables

This is how the Social Flask SQLAlchemy tables were initially created. [See this explanation for more info.](http://python-social-auth.readthedocs.io/en/latest/configuration/flask.html#models-setup).

```python
def register_extensions(flask_app):

    ...

    # Create the social_flask_sqlalchemy models:
    from social_flask_sqlalchemy.models import PSABase
    from labonneboite.common.database import engine
    from social_flask_sqlalchemy.models import UserSocialAuth, Nonce, Association, Code, Partial
    PSABase.metadata.create_all(engine)

    ...
```

Once the tables were created, a migration file was generated and the code above could be removed.
