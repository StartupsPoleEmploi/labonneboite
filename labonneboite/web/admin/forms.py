from flask_admin.form import BaseForm
from wtforms import ValidationError
from wtforms.fields import Field
from labonneboite_common.siret import is_siret
from labonneboite.common.mapping import naf_is_valid


def siret_validator(form: BaseForm, field: Field) -> None:
    """
    Validate siret number.
    http://wtforms.readthedocs.io/en/latest/validators.html#custom-validators
    """
    if not is_siret(field.data):
        raise ValidationError("Le numéro SIRET doit être composé de 14 chiffres")


def naf_validator(form: BaseForm, field: Field) -> None:
    """
    Validate NAF code.
    """
    if not naf_is_valid(field.data):
        raise ValidationError("Le code NAF n'est pas valide")


def phone_validator(form: BaseForm, field: Field) -> None:
    """
    Validate phone number.
    """
    if not field.data.isdigit() or len(field.data) != 10:
        raise ValidationError("Le numéro de téléphone doit être composé de 10 chiffres")


def zip_code_validator(form: BaseForm, field: Field) -> None:
    """
    Validate zip code.
    """
    if not field.data.isdigit() or len(field.data) != 5:
        raise ValidationError("Le code postal doit être composé de 5 chiffres.")


def code_commune_validator(form: BaseForm, field: Field) -> None:
    """
    Validate code commune.
    """
    if not field.data.isdigit() or len(field.data) != 5:
        raise ValidationError("Le code commune doit être composé de 5 chiffres.")


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
