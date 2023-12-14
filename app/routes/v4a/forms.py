from wtforms import (
    HiddenField,
    SubmitField,
    FileField,
    BooleanField,
    StringField
)
from app.utils.validators import(
    DataRequired,
    Length
)
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm

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