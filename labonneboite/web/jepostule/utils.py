import hashlib

from labonneboite.conf import settings


def jepostule_enabled(user, company):
    return is_user_enabled(user) and is_company_enabled(company)


def is_user_enabled(user):
    """
    Return True if jepostule is enabled for this specific user.
    """
    if user.is_authenticated and not user.is_anonymous:
        if user.email.lower() in settings.JEPOSTULE_BETA_EMAILS:
            return True
        if not is_valid_email(user.email):
            return False
        if settings.JEPOSTULE_QUOTA > 0:
            fingerprint = hashlib.sha256((settings.FLASK_SECRET_KEY + user.external_id).encode())
            if int(fingerprint.hexdigest(), 16) % settings.JEPOSTULE_QUOTA == 0:
                return True
    return False


def is_company_enabled(company):
    return company and company.email and is_valid_email(company.email)


def is_valid_email(email):
    """
    Perform a lightweight validation verification.
    """
    invalid_characters = set([',', '\'', '*', '"'])
    return len(invalid_characters.intersection(email)) == 0
