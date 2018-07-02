# coding: utf8

from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, SelectField, TextAreaField
from wtforms import validators
from wtforms.fields.html5 import EmailField, TelField
from wtforms.validators import DataRequired, Email, Regexp, Length


class OfficeContactPreForm(FlaskForm):

    ACTION_CHOICES = (
        (u'promote', u'Promouvoir mon entreprise sur le site'),
        (u'remove', u'Retirer mon entreprise du site'),
        (u'update', u'Modifier les coordonnées de mon entreprise sur le site'),
        (u'other', u'Autre')
    )

    action = SelectField(u'Je souhaite *', choices=ACTION_CHOICES, default=u'promouvoir')
    siret = StringField(
        u'Siret *',
        validators=[
            DataRequired(),
            Regexp(
                '[0-9]{10,14}',
                message=(u"Le siret de l'établissement est invalide (14 chiffres)")
            )
        ],
        description="14 chiffres, sans espace. Exemple: 36252187900034",
    )


class OfficeFormCommon(OfficeContactPreForm):
    first_name = StringField(u'Prénom *', validators=[DataRequired()])
    last_name = StringField(u'Nom *', validators=[DataRequired()])
    email = EmailField(u'Email *', validators=[DataRequired(), Email()], description="Exemple : example@domaine.com")
    phone = TelField(u'Téléphone', description="Exemples: 01 77 86 39 49, +33 1 77 86 39 49")
    comment = TextAreaField(u'Commentaires', [validators.optional(), validators.length(max=15000)], description=u"15000 caractères maximum")

class OfficePromoteForm(OfficeFormCommon):
    pass

class OfficeUpdateCoordinatesForm(OfficeFormCommon):
    pass

class OfficeDeleteForm(OfficeFormCommon):
    hide_lbb = BooleanField('lbb')
    hide_lba = BooleanField('lba')