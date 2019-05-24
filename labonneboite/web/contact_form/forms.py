# coding: utf8
from flask import request

from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, TextAreaField, HiddenField, RadioField
from wtforms import validators
from wtforms.fields.html5 import EmailField, TelField
from wtforms.validators import DataRequired, Email, Optional, Regexp, URL, Length

from labonneboite.common.load_data import ROME_CODES

CONTACT_MODES = (
    ('mail', 'Par courrier'),
    ('email', 'Par email'),
    ('phone', 'Par téléphone'),
    ('office', 'Sur place'),
    ('website', 'Via votre site internet'),
)
CONTACT_MODES_LABELS = dict(CONTACT_MODES)
PHONE_REGEX = "^(0|\+33)[1-9]([-. ]?[0-9]{2}){4}$"


class OfficeIdentificationForm(FlaskForm):
    siret = StringField(
        'N° de Siret *',
        validators=[
            DataRequired(),
            Regexp('[0-9]{14}', message=("Le siret de l'établissement est invalide (14 chiffres sans espace)"))
        ],
        description="14 chiffres, sans espace. Exemple: 36252187900034",
    )

    last_name = StringField('Nom *', validators=[DataRequired()])
    first_name = StringField('Prénom *', validators=[DataRequired()])
    phone = TelField(
        'Téléphone *',
        description="Exemple: 01 77 86 39 49 ou +331 77 86 39 49",
        validators=[DataRequired(), Regexp(PHONE_REGEX, message="Entrée invalide. Exemple valide: 01 77 86 39 49 ou +331 77 86 39 49")],
    )
    email = EmailField(
        'Adresse email *',
        description="Exemple: exemple@domaine.com",
        validators=[DataRequired(), Email(message="Entrée invalide. Exemple valide: exemple@domaine.com")],
    )


class OfficeHiddenIdentificationForm(FlaskForm):
    siret = HiddenField('Siret *', validators=[DataRequired()])
    last_name = HiddenField('Nom *', validators=[DataRequired()])
    first_name = HiddenField('Prénom *', validators=[DataRequired()])
    phone = HiddenField('Téléphone *', validators=[DataRequired(), Regexp(PHONE_REGEX)])
    email = HiddenField('Adresse email *', validators=[DataRequired(), Email()])


class OfficeOtherRequestForm(OfficeHiddenIdentificationForm):
    comment = TextAreaField(
        'Votre message*',
        validators=[DataRequired(), validators.length(max=15000)],
        description="15000 caractères maximum"
    )


class OfficeUpdateJobsForm(OfficeHiddenIdentificationForm):
    pass


class OfficeUpdateCoordinatesForm(OfficeHiddenIdentificationForm):
    # Note : we add new_ to avoid conflict with request.args
    new_contact_mode = RadioField('Mode de contact à privilégier', choices=CONTACT_MODES, default='email')
    new_website = StringField(
        'Site Internet',
        description="Exemple: http://exemple.com",
        validators=[URL(message="Entrée invalide. Exemple: http://exemple.com"), Optional()]
    )
    new_email = EmailField(
        'Email recruteur',
        description="Exemple: exemple@domaine.com",
        validators=[Email(message="Entrée invalide. Exemple valide: exemple@domaine.com"), Optional()]
    )
    new_phone = StringField(
        'Téléphone',
        description="Exemple: 01 77 86 39 49 ou +331 77 86 39 49",
        validators=[Optional(), Regexp(PHONE_REGEX, message="Entrée invalide. Exemple valide: 01 77 86 39 49 ou +331 77 86 39 49")]
    )
    social_network = StringField(
        'Réseau social',
        description="Exemple: https://twitter.com/0123456_abcdef",
        validators=[URL(message="Entrée invalide. Exemple: https://twitter.com/0123456_abcdef"), Optional()]
    )
    new_email_alternance = EmailField(
        'Email recruteur spécialisé alternance',
        description="Exemple: exemple@domaine.com",
        validators=[validators.optional(), Email(message="Entrée invalide. Exemple valide: exemple@domaine.com")]
    )
    new_phone_alternance = StringField(
        'Téléphone du recruteur spécialisé alternance',
        description="Exemple: 01 77 86 39 49 ou +331 77 86 39 49",
        validators=[validators.optional(), Regexp(PHONE_REGEX, message="Entrée invalide. Exemple valide: 01 77 86 39 49 ou +331 77 86 39 49")]
    )
    rgpd_consent = BooleanField(
        'En cochant cette case, vous consentez à diffuser des données à caractère personnel sur les services numériques de Pôle emploi.',
        [validators.required()]
    )


class OfficeRemoveForm(OfficeHiddenIdentificationForm):
    remove_lbb = BooleanField(
        'Supprimer mon entreprise du service La Bonne Boite puisque je ne suis pas intéressé-e pour recevoir des candidatures spontanées via ce site',
        [validators.optional()]
    )
    remove_lba = BooleanField(
        'Supprimer mon entreprise du service La Bonne Alternance puisque je ne suis pas intéressé-e pour recevoir des candidatures spontanées via ce site',
        [validators.optional()]
    )


def compute_romes():
    """
    We use request.form because some ROME codes can be added manually on the client site.
    WTForm can't handle this case.
    """
    return extract_romes(), extract_romes('lbb'), extract_romes('lba'), extract_romes('hide')

def extract_romes(expected_value=None):
    return list(
        [
            key for key, value in dict(request.form).items()
            if key in ROME_CODES and (expected_value is None or expected_value in value)
        ]
    )
