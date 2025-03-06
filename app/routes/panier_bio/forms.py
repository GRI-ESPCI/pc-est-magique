"""PC est magique - Panier Bio Forms"""

import wtforms
from wtforms.fields import html5
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from datetime import date
from app.utils.validators import DataRequired, Optional, Length


# This code from WTForms docs, this class changes the way SelectMultipleField
# is rendered by jinja
# https://wtforms.readthedocs.io/en/3.0.x/specific_problems/
class MultiCheckboxField(wtforms.SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = wtforms.widgets.ListWidget(prefix_label=False)
    option_widget = wtforms.widgets.CheckboxInput()



class PanierBio(FlaskForm):
    """WTForm used to manage Panier Bio."""

    id = wtforms.HiddenField("")
    pceen_id = wtforms.HiddenField(validators=[Optional()])
    nom = wtforms.StringField(_l("Nom"), validators=[DataRequired(), Length(max=20)])
    prenom = wtforms.StringField(_l("Prénom"), validators=[DataRequired(), Length(max=20)])
    service = wtforms.StringField(_l("Promo, labo..."), validators=[DataRequired(), Length(max=20)])
    payment_method = wtforms.SelectField(_l("Méthode de payement"), validators=[DataRequired()], choices=["Espèces lors du retrait", "Par virement"])
    dates = MultiCheckboxField(_l("Date du Panier Bio"), validators=[Optional()])
    date = html5.DateField(_l("Date du Panier Bio"), validators=[Optional()])
    phone = html5.TelField(_l("Numéro de téléphone (Optionnel)"), validators=[Optional()])
    comment = wtforms.TextAreaField(_l("Commentaire"), validators=[Optional(), Length(max=500)])
    payed = wtforms.BooleanField(_l("Payée ?"), validators=[Optional()], default=False)
    treasurer_validate = wtforms.BooleanField(
        _l("Payement validé par trésorier ?"), validators=[Optional()], default=False
    )
    taken = wtforms.BooleanField(_l("Récupérée ?"), validators=[Optional()], default=False)

    consent = wtforms.BooleanField(
        _l("En commandant, je m'engage à payer et à venir prendre le panier."), default=False
    )

    # Submission buttons
    add = wtforms.SubmitField(_l("Commander"))
    edit = wtforms.SubmitField(_l("Modifier"))
    delete = wtforms.SubmitField(_l("Supprimer"))


class Period(FlaskForm):
    """WTForm used to manage Panier Bio."""

    id = wtforms.HiddenField("")
    start_date = html5.DateField(_l("Date de début"), validators=[DataRequired()])
    end_date = html5.DateField(_l("Date de fin"), validators=[DataRequired()])
    disabled_days = wtforms.TextAreaField(_l("Jours sans panier bio"), validators=[Optional(), Length(max=500)])
    activate = wtforms.BooleanField(_l("Activée ?"), validators=[Optional()], default=False)

    # Submission buttons
    add = wtforms.SubmitField(_l("Commander"))
    edit = wtforms.SubmitField(_l("Modifier"))
    delete = wtforms.SubmitField(_l("Supprimer"))


class SettingsPanierBio(FlaskForm):
    """WTForm for options of panier bio"""

    submit = wtforms.SubmitField(_l("Mettre à jour"))
