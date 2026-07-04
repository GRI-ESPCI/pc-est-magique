"""PC est magique - Gris-only Pages Forms"""

import wtforms
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm

from app.utils.helpers import list_scripts
from app.utils.validators import (
    DataRequired,
    Optional,
    Length,
    ValidPCeenID,
    ValidBanID,
)


class ChoseScriptForm(FlaskForm):
    """WTForm used to chose a script to execute."""

    script = wtforms.SelectField(
        _l("Script"),
        choices=[(script_name, f"{script_name} – {descr}") for script_name, descr in list_scripts().items()],
        validators=[DataRequired()],
    )
    submit = wtforms.SubmitField(_l("Exécuter"))


class AddRemoveRoleForm(FlaskForm):
    """WTForm used to chose a script to execute."""

    action = wtforms.HiddenField("", validators=[DataRequired()])
    pceen_id = wtforms.HiddenField("", validators=[DataRequired()])
    role_id = wtforms.HiddenField("", validators=[DataRequired()])


class AddRemovePermissionForm(FlaskForm):
    """WTForm used to chose a script to execute."""

    action = wtforms.HiddenField("", validators=[DataRequired()])
    role_id = wtforms.HiddenField("", validators=[Optional()])
    perm_id = wtforms.HiddenField("", validators=[Optional()])
    scope_name = wtforms.HiddenField("", validators=[Optional()])
    type_name = wtforms.HiddenField("", validators=[Optional()])
    ref_id = wtforms.HiddenField("", validators=[Optional()])


class BanForm(FlaskForm):
    """WTForm used to ban someone."""

    pceen = wtforms.HiddenField("", validators=[DataRequired(), ValidPCeenID()])
    ban_id = wtforms.HiddenField("", validators=[Optional(), ValidBanID()])
    infinite = wtforms.BooleanField(_l("Illimité"), default=True)
    hours = wtforms.IntegerField(_l("Heures"), validators=[Optional()])
    days = wtforms.IntegerField(_l("Jours"), validators=[Optional()])
    months = wtforms.IntegerField(_l("Mois"), validators=[Optional()])
    reason = wtforms.StringField(_l("Motif court"), validators=[DataRequired(), Length(max=32)])
    message = wtforms.TextAreaField(_l("Message détaillé"), validators=[Optional(), Length(max=2000)])
    submit = wtforms.SubmitField(_l("Bannez-moi ça les modos || Mettre à jour le ban"))
    unban = wtforms.SubmitField(_l("Mettre fin au ban"))


class AddPCeenForm(FlaskForm):
    """WTForm used to manually create a PCéen."""

    nom = wtforms.StringField(_l("Nom"), validators=[DataRequired(), Length(max=64)])
    prenom = wtforms.StringField(_l("Prénom"), validators=[DataRequired(), Length(max=64)])
    promo = wtforms.IntegerField(_l("Promo (Optionnel)"), validators=[Optional()])
    email = wtforms.EmailField(_l("Email"), validators=[DataRequired(), Length(max=120)])
    roles = wtforms.SelectMultipleField(_l("Rôles"), coerce=int, validators=[Optional()])
    submit = wtforms.SubmitField(_l("Créer le PCéen"))

class PushNotificationForm(FlaskForm):
    """WTForm used to send push notifications."""

    target = wtforms.SelectField(
        _l("Cible"),
        choices=[
            ("all", _l("Tous les utilisateurs")),
            ("eleves", _l("Tous les élèves")),
            ("rez", _l("Résidents Rez (avec internet actif)")),
            ("role", _l("Rôle spécifique")),
        ],
        default="eleves",
        validators=[DataRequired()],
    )
    roles = wtforms.SelectMultipleField(_l("Rôles (si Cible = Rôle spécifique)"), coerce=int, validators=[Optional()])
    title = wtforms.StringField(_l("Titre"), validators=[DataRequired(), Length(max=128)])
    body = wtforms.TextAreaField(_l("Message"), validators=[DataRequired(), Length(max=512)])
    image = wtforms.StringField(_l("Image URL (optionnelle)"), validators=[Optional(), Length(max=256)])
    quiet = wtforms.BooleanField(_l("Notification silencieuse (ne pas afficher de popup)"), default=False)
    url = wtforms.StringField(_l("URL au clic (optionnel)"), validators=[Optional(), Length(max=256)])
    submit = wtforms.SubmitField(_l("Envoyer"))