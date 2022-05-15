"""PC est magique - Gris-only Pages Forms"""

import os

import wtforms
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm

from app.utils.validators import DataRequired, Optional


def scripts_list() -> list[tuple[str, str]]:
    """Build the list of existing scripts in app/scripts.

    Returns:
        ``list((value, label))`` options for :class:`wtforms.SelectField`.
    """
    scripts = []
    for file in os.scandir("scripts"):
        if not file.is_file():
            continue
        name, ext = os.path.splitext(file.name)
        if ext != ".py":
            continue

        with open(file, "r") as fp:
            first_line = fp.readline()
        doc = first_line.lstrip("'\"")

        scripts.append((name, f"{name} — {doc}"))

    return scripts


class ChoseScriptForm(FlaskForm):
    """WTForm used to chose a script to execute."""

    script = wtforms.SelectField(
        _l("Script"), choices=scripts_list(), validators=[DataRequired()]
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
