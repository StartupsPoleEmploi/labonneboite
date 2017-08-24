# coding: utf8

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField
from wtforms import validators
from wtforms.fields.html5 import EmailField, TelField
from wtforms.validators import DataRequired, Email, Regexp


class OfficeRemovalForm(FlaskForm):

    ACTION_CHOICES = (
        (u'promouvoir', u'Que mon entreprise soit davantage mise en avant'),
        (u'enlever', u'Supprimer mon entreprise des résultats'),
        (u'modifier', u'Mettre à jour les informations de mon entreprise'),
        (u'autre', u'Autre')
    )

    action = SelectField(u'Je souhaite :', choices=ACTION_CHOICES, default=u'promouvoir')
    siret = StringField(
        u'Siret (14 chiffres)',
        validators=[
            DataRequired(),
            Regexp(
                '[0-9]{10,14}',
                message=(u"Le siret de l'établissement dont vous êtes le dirigeant est invalide (14 chiffres)")
            )
        ]
    )
    first_name = StringField(u'Prénom', validators=[DataRequired()])
    last_name = StringField(u'Nom', validators=[DataRequired()])
    email = EmailField(u'Email', validators=[DataRequired(), Email()])
    phone = TelField(u'Téléphone')
    comment = TextAreaField(u'Commentaires', [validators.optional(), validators.length(max=200)])
