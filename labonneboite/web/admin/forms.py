from wtforms import ValidationError

from labonneboite.common.siret import is_siret


def siret_validator(form, field):
    """
    Validate siret number.
    http://wtforms.readthedocs.io/en/latest/validators.html#custom-validators
    """
    if not is_siret(field.data):
        raise ValidationError("Le numéro SIRET doit être composé de 14 chiffres")


def phone_validator(form, field):
    """
    Validate phone number.
    """
    if not field.data.isdigit() or len(field.data) != 10:
        raise ValidationError("Le numéro de téléphone doit être composé de 10 chiffres")


def zip_code_validator(form, field):
    """
    Validate zip code.
    """
    if not field.data.isdigit() or len(field.data) != 5:
        raise ValidationError("Le code postal doit être composé de 5 chiffres.")


def code_commune_validator(form, field):
    """
    Validate code commune.
    """
    if not field.data.isdigit() or len(field.data) != 5:
        raise ValidationError("Le code commune doit être composé de 5 chiffres.")


def nospace_filter(value):
    """
    Remove spaces from user input.
    """
    if value is not None and hasattr(value, "replace"):
        return value.replace(" ", "")
    return value


def strip_filter(value):
    """
    Strip the spaces from user input.
    """
    if value is not None and hasattr(value, "strip"):
        return value.strip()
    return value
