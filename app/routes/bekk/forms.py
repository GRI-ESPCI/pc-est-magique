"""PC est magique - Photos Gallery Forms"""

import wtforms
from wtforms.fields import html5
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm

from app.models import Collection
from app.routes.photos.utils import get_dir_name
from app.utils.validators import DataRequired, Optional, Length, NumberRange


class Bekk(FlaskForm):
    """WTForm used to edit a photo."""

    id = wtforms.HiddenField("")
    bekk_name = wtforms.StringField(_l("Nom du Bekk"), validators=[DataRequired()])
    promo = wtforms.StringField(_l("Promo"), validators=[DataRequired()])
    date = html5.DateField(_l("Date"), validators=[DataRequired()])
    add = wtforms.SubmitField(_l("Ajouter le Bekk"))
    submit = wtforms.SubmitField(_l("Modifier le Bekk"))
    delete = wtforms.SubmitField(_l("Supprimer le Bekk"))
