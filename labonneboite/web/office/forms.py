# coding: utf8

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField
from wtforms import validators
from wtforms.fields.html5 import EmailField, TelField
from wtforms.validators import DataRequired, Email, Regexp


class OfficeRemovalForm(FlaskForm):

    ACTION_CHOICES = (
        ('promouvoir', 'Promouvoir mon entreprise sur le site'),
        ('enlever', 'Retirer mon entreprise du site'),
        ('modifier', 'Modifier les coordonnées de mon entreprise sur le site'),
        ('autre', 'Autre')
    )

    action = SelectField('Je souhaite *', choices=ACTION_CHOICES, default='promouvoir')
    siret = StringField(
        'Siret *',
        validators=[
            DataRequired(),
            Regexp(
                '[0-9]{10,14}',
                message=("Le siret de l'établissement dont vous êtes le dirigeant est invalide (14 chiffres)")
            )
        ],
        description="14 chiffres, sans espace. Exemple: 36252187900034"
    )
    first_name = StringField('Prénom *', validators=[DataRequired()])
    last_name = StringField('Nom *', validators=[DataRequired()])
    email = EmailField('Email *', validators=[DataRequired(), Email()], description="Exemple : example@domaine.com")
    phone = TelField('Téléphone', description="Exemples: 01 77 86 39 49, +33 1 77 86 39 49")
    comment = TextAreaField('Commentaires', [validators.optional(), validators.length(max=15000)], description="15000 caractères maximum")
