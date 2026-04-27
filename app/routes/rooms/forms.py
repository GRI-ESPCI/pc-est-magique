"""PC est magique - Rooms-related Forms"""

import wtforms
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm

from app.utils.validators import DataRequired, Optional, ValidRoom, PastDate, FutureDate


class RentalRegistrationForm(FlaskForm):
    """WTForm used to register a room rental."""

    room = wtforms.IntegerField(_l("Chambre"), validators=[DataRequired(), ValidRoom()])
    start = wtforms.DateField(_l("Début de la location"), validators=[DataRequired(), PastDate()])
    end = wtforms.DateField(_l("Fin de la location (optionnel)"), validators=[Optional(), FutureDate()])
    submit = wtforms.SubmitField(_l("Enregistrer"))


class RentalModificationForm(FlaskForm):
    """WTForm used to modify a room rental."""

    start = wtforms.DateField(_l("Début de la location"), validators=[DataRequired(), PastDate()])
    end = wtforms.DateField(_l("Fin de la location (optionnel)"), validators=[Optional(), FutureDate()])
    submit = wtforms.SubmitField(_l("Modifier"))


class RentalTransferForm(FlaskForm):
    """WTForm used to terminate a room rental, before creating a new one."""

    end = wtforms.DateField(_l("Fin de la location"), validators=[DataRequired(), PastDate()])
    submit = wtforms.SubmitField(_l("Terminer la location"))