"""PC est magique - Gris-only Pages Forms"""


import wtforms
from wtforms.fields import html5
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
    hours = html5.IntegerField(_l("Heures"), validators=[Optional()])
    days = html5.IntegerField(_l("Jours"), validators=[Optional()])
    months = html5.IntegerField(_l("Mois"), validators=[Optional()])
    reason = wtforms.TextField(_l("Motif court"), validators=[DataRequired(), Length(max=32)])
    message = wtforms.TextAreaField(_l("Message détaillé"), validators=[Optional(), Length(max=2000)])
    submit = wtforms.SubmitField(_l("Bannez-moi ça les modos || Mettre à jour le ban"))
    unban = wtforms.SubmitField(_l("Mettre fin au ban"))
