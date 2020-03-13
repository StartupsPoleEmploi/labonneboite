from flask import session


def fix_csrf_session():
    """
    csrf_token session cookies placed by python 2.7 is stored in bytes format.
    This causes a crash when calling csrf_token() (e.g: in templates) with
    python 3. To address this, we manually convert cookies in some views.

    This is a temporary fix that should be removed a couple days after python 3
    migration is completed.
    """
    if isinstance(session.get("csrf_token", ""), bytes):
        session["csrf_token"] = session["csrf_token"].decode()
