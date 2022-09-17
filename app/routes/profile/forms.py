"""PC est magique - Profile-related Forms"""

import wtforms
from wtforms.fields import html5
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm

from app.utils.validators import DataRequired, Email, EqualTo, Length, NewEmail


class AccountModificationForm(FlaskForm):
    """WTForm used to modify the account of a PCéen."""

    nom = wtforms.StringField(_l("Nom"), validators=[DataRequired(), Length(max=64)])
    prenom = wtforms.StringField(_l("Prénom"), validators=[DataRequired(), Length(max=64)])
    promo = wtforms.IntegerField(_l("Promotion"), validators=[DataRequired()])
    email = html5.EmailField(
        _l("Adresse e-mail"),
        validators=[DataRequired(), Length(max=120), Email(), NewEmail()],
    )
    submit = wtforms.SubmitField(_l("Mettre à jour"))


class PasswordUpdateForm(FlaskForm):
    """WTForm used to update the password of a PCéen."""

    current_password = wtforms.PasswordField(_l("Mot de passe actuel"), validators=[DataRequired()])
    password = wtforms.PasswordField(_l("Nouveau mot de passe"), validators=[DataRequired()])
    password2 = wtforms.PasswordField(
        _l("Nouveau mot de passe (validation)"),
        validators=[DataRequired(), EqualTo("password")],
    )
    submit = wtforms.SubmitField(_l("Mettre à jour"))
