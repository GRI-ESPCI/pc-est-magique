"""PC est magique - Photos Gallery Forms"""

import wtforms
from wtforms.fields import html5
from flask_wtf.file import FileField, FileAllowed
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from datetime import date
from app.utils.validators import DataRequired


class Bekk(FlaskForm):
    """WTForm used to manage Bekks."""

    id = wtforms.HiddenField("")
    bekk_name = wtforms.StringField(_l("Nom du Bekk"), validators=[DataRequired()])
    promo = wtforms.StringField(_l("Promo"), validators=[DataRequired()])
    date = html5.DateField(_l("Date"), validators=[DataRequired()], default=date.today)
    pdf_file = FileField(_l(""), validators=[FileAllowed(["pdf"], "PDF uniquement!")])
    add = wtforms.SubmitField(_l("Ajouter"))
    submit = wtforms.SubmitField(_l("Modifier"))
    delete = wtforms.SubmitField(_l("Supprimer"))
