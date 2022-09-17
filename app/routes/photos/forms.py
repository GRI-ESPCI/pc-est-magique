"""PC est magique - Photos Gallery Forms"""

import wtforms
from wtforms.fields import html5
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm

from app.utils.validators import DataRequired, Optional, Length, NumberRange


class EditPhotoForm(FlaskForm):
    """WTForm used to edit a photo."""

    photo_name = wtforms.StringField(_l("Nom du fichier"), validators=[DataRequired()])
    caption = wtforms.StringField(_l("Légende (optionnel)"), validators=[Optional(), Length(max=280)])
    author_str = wtforms.StringField(_l("Auteur (optionnel)"), validators=[Optional(), Length(max=64)])
    date = html5.DateField(_l("Date (optionnel)"), validators=[Optional()])
    time = html5.TimeField(_l("Heure (optionnel)"), format="%H:%M:%S", validators=[Optional()])
    lat = html5.DecimalField(
        _l("Latitude (optionnel)"),
        validators=[Optional(), NumberRange(min=-90, max=90)],
    )
    lng = html5.DecimalField(
        _l("Longitude (optionnel)"),
        validators=[Optional(), NumberRange(min=-180, max=180)],
    )
    submit = wtforms.SubmitField(_l("Modifier la photo"))


class EditAlbumForm(FlaskForm):
    """WTForm used to edit an album."""

    name = wtforms.StringField(_l("Nom de l'album"), validators=[DataRequired(), Length(max=120)])
    description = wtforms.StringField(_l("Description (optionnel)"), validators=[Optional(), Length(max=280)])
    start = html5.DateField(_l("Date de début (optionnel)"), validators=[Optional()])
    end = html5.DateField(_l("Date de fin (optionnel)"), validators=[Optional()])
    visible = wtforms.BooleanField(_l("Album visible"))
    submit = wtforms.SubmitField(_l("Modifier l'album"))


class EditCollectionForm(FlaskForm):
    """WTForm used to edit a collection."""

    name = wtforms.StringField(_l("Nom de la collection"), validators=[DataRequired(), Length(max=120)])
    description = wtforms.StringField(_l("Description (optionnel)"), validators=[Optional(), Length(max=280)])
    start = html5.DateField(_l("Date de début (optionnel)"), validators=[Optional()])
    end = html5.DateField(_l("Date de fin (optionnel)"), validators=[Optional()])
    visible = wtforms.BooleanField(_l("Collection visible"))
    submit = wtforms.SubmitField(_l("Modifier la collection"))
