from flask import flash, url_for
from flask_login import current_user

from labonneboite.common.models.auth import TokenRefreshFailure


def attempt_to_refresh_peam_token():
    if current_user.is_authenticated:
        try:
            current_user.refresh_peam_access_token_if_needed()
        except TokenRefreshFailure:
            message = "Votre session PE Connect a expiré. Veuillez vous reconnecter."
            flash(message, 'warning')
            return {
                "token_has_expired": True,
                "redirect_url": url_for('auth.logout'),
            }
    return {
        "token_has_expired": False,
    }

def refresh_peam_token(func):
    def decorator(*args, **kwarg):
        refresh_token_result = attempt_to_refresh_peam_token()
        if refresh_token_result["token_has_expired"]:
            return redirect(refresh_token_result["redirect_url"])
        return func(*args, **kwarg)
    return decorator