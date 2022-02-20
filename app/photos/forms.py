"""PC est magique - Photos Gallery Forms"""

import wtforms
from wtforms.fields import html5
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm

from app.tools.validators import (DataRequired, Optional, Email, EqualTo,
                                  Length, NewEmail)


class EditAlbumForm(FlaskForm):
    """WTForm used to edit an album."""
    name = wtforms.StringField(_l("Nom de l'album"),
                               validators=[DataRequired(), Length(max=120)])
    description = wtforms.StringField(_l("Description (optionnel)"),
                                      validators=[Optional(), Length(max=280)])
    start = html5.DateField(_l("Date de début (optionnel)"),
                            validators=[Optional()])
    end = html5.DateField(_l("Date de fin (optionnel)"),
                          validators=[Optional()])
    visible = wtforms.BooleanField(_l("Album visible"))
    submit = wtforms.SubmitField(_l("Modifier l'album"))


class EditCollectionForm(FlaskForm):
    """WTForm used to edit a collection."""
    name = wtforms.StringField(_l("Nom de la collection"),
                               validators=[DataRequired(), Length(max=120)])
    description = wtforms.StringField(_l("Description (optionnel)"),
                                      validators=[Optional(), Length(max=280)])
    start = html5.DateField(_l("Date de début (optionnel)"),
                            validators=[Optional()])
    end = html5.DateField(_l("Date de fin (optionnel)"),
                          validators=[Optional()])
    visible = wtforms.BooleanField(_l("Collection visible"))
    submit = wtforms.SubmitField(_l("Modifier la collection"))
