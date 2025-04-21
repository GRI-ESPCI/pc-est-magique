"""Pc est magique - Theatre-related Forms"""

import wtforms
from flask_wtf import FlaskForm
from flask_babel import lazy_gettext as _l
from wtforms.validators import DataRequired, Length

class EditSaison(FlaskForm):
    """WTform used to edit a theatre season"""

    name = wtforms.StringField(
        _l("Nom de la saison"),
        validators=[
            DataRequired(),
            Length(max=120)
        ]
    )

    description = wtforms.TextAreaField(
        _l("Description"),
        validators=[
            Length(max=2000)
        ]
    )

    start_date = wtforms.DateField(
        _l("Date de début"),
        validators=[
            DataRequired()
        ]
    )