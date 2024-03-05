"""PC est magique - Panier Bio Forms"""

import wtforms
from wtforms.fields import html5
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from datetime import date
from app.utils.validators import DataRequired, Optional, Length


class PanierBio(FlaskForm):
    """WTForm used to manage Panier Bio."""

    id = wtforms.HiddenField("")
    pceen_id = wtforms.HiddenField(validators=[Optional()])
    nom = wtforms.StringField(_l("Nom"), validators=[DataRequired(), Length(max=20)])
    prenom = wtforms.StringField(_l("Prénom"), validators=[DataRequired(), Length(max=20)])
    service = wtforms.StringField(_l("Promo, labo..."), validators=[DataRequired(), Length(max=20)])
    payment_method = wtforms.SelectField(_l("Méthode de payement"), choices = ["Espèces lors du retrait", "Par virement"])
    date = html5.DateField(_l("Date"), validators=[DataRequired()], default=date.today)
    phone = html5.TelField(_l("Numéro de téléphone (Optionnel)"), validators=[Optional()])
    comment = wtforms.TextAreaField(_l("Commentaire"), validators=[Optional(), Length(max=500)])
    payed = wtforms.BooleanField(_l("Payée ?"), validators=[Optional()], default=False)
    consent = wtforms.BooleanField(_l("En commandant, je m'engage à payer et à venir prendre le panier."), default=False)

    #Submission buttons
    add = wtforms.SubmitField(_l("Commander"))
    edit = wtforms.SubmitField(_l("Modifier"))
    delete = wtforms.SubmitField(_l("Supprimer"))


class SettingsPanierBio(FlaskForm):
    """WTForm for options of panier bio"""
    submit = wtforms.SubmitField(_l("Mettre à jour"))

