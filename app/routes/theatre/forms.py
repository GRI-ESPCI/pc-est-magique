"""Pc est magique - Theatre-related Forms"""

from flask_babel import lazy_gettext as _l

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired

import wtforms
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

class EditSpectacle(FlaskForm):
    """WTform used to edit a theatre spectacle"""

    name = wtforms.StringField(
        _l("Nom du spectacle"),
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

    director = wtforms.StringField(
        _l("Metteur ou metteuse en scène"),
        validators=[
            Length(max=64)
        ]
    )

    author = wtforms.StringField(
        _l("Auteur ou autrice de la pièce"),
        validators=[
            Length(max=64)
        ]
    )

    ticket_link = wtforms.StringField(
        _l("Lien vers la billeterie"),
        validators=[
            Length(max=120)
        ]
    )
    places = wtforms.StringField(
        _l("Lien vers la résérvation des places"),
        validators=[
            Length(max=255)
        ]
    )

class SendPicture(FlaskForm):
    """WTForm to send pictures"""

    picture = wtforms.FileField(
        _l("Photo à téléverser"),
        validators=[
            FileRequired()
        ]
    )