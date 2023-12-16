from wtforms import (
    HiddenField,
    SubmitField,
    FileField,
    BooleanField,
    StringField,
    IntegerField
)
from app.utils.validators import(
    DataRequired,
    Length,
    FutureDate,
    NumberRange
)
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms.fields import html5

class EditV4A(FlaskForm):
    """WTForm for editing V4A content"""

    visible = BooleanField(
        label=_l("Visible ?")
    )
    name = StringField(
        label=_l("Nom du V4A"),
        validators=[
            DataRequired(),
            Length(max=120)
        ]
    )
    description = StringField(
        label=_l("Description courte"),
        validators=[
            Length(max=250)
        ]
    )
    ticketing_open = BooleanField(
        label=_l("Billeterie ouverte ?")
    )
    delta_full_description = HiddenField()
    image_file = FileField(_l("Image de couverture"))

    submit = SubmitField(_l("Modifier"))

class EditRepresentation(FlaskForm):
    """WTForms for editing V4A representation"""

    date = html5.DateTimeLocalField(
        _l("Date et heure de la représentation"),
        validators=[
            DataRequired(),
            FutureDate()
        ],
        format="%Y-%m-%dT%H:%M"
    )
    sits = IntegerField(
        _l("Nombre de places"),
        validators=[
            DataRequired(),
            NumberRange(
                min=0,
                message=_l("Le nombre de places doit être supérieur ou égal à zéro.")
            )
        ]
    )
    submit = SubmitField(_l("Ajouter"))