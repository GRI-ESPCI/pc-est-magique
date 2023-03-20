"""PC est magique - Profile-related Forms"""

import wtforms
from wtforms.fields import html5
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm

from app.utils.validators import DataRequired, Email, EqualTo, Length, NewEmail


class ClubQForm(FlaskForm):
    """WTForm used to send the wish for the current Club Q Season"""

    priorite = wtforms.SelectField('Priorité', choices=[(1),(2),(3),(4),(5),(6),(7),(8),(9),(10),(11),(12),(13),(14),(15)], coerce=int)
    nb_places = wtforms.SelectField('Nombre places demandées', choices=[(1),(2),(3),(4),(5)], coerce=int)
    nb_places_minimum = wtforms.SelectField('Nombre places minimum demandées', choices=[(1),(2),(3),(4),(5)], coerce=int)

    submit = wtforms.SubmitField(_l("Mettre à jour"))
