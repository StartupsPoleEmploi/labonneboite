# coding: utf8

from wtforms import ValidationError


def siret_validator(form, field):
    """
    Validate siret number.
    http://wtforms.readthedocs.io/en/latest/validators.html#custom-validators
    """
    if not field.data.isdigit() or len(field.data) != 14:
        raise ValidationError(u"Le numéro SIRET doit être composé de 14 chiffres")


def phone_validator(form, field):
    """
    Validate phone number.
    """
    if not field.data.isdigit() or len(field.data) != 10:
        raise ValidationError(u"Le numéro de téléphone doit être composé de 10 chiffres")


def zip_code_validator(form, field):
    """
    Validate zip code.
    """
    if not field.data.isdigit() or len(field.data) != 5:
        raise ValidationError(u"Le code postal doit être composé de 5 chiffres.")


def code_commune_validator(form, field):
    """
    Validate code commune.
    """
    if not field.data.isdigit() or len(field.data) != 5:
        raise ValidationError(u"Le code commune doit être composé de 5 chiffres.")


def nospace_filter(value):
    """
    Remove spaces from user input.
    """
    if value is not None and hasattr(value, 'replace'):
        return value.replace(' ', '')
    return value


def strip_filter(value):
    """
    Strip the spaces from user input.
    """
    if value is not None and hasattr(value, 'strip'):
        return value.strip()
    return value
