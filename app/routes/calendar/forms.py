from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_babel import lazy_gettext as _l

class EditClub(FlaskForm):
    name = StringField(_l("Nom du club"), validators=[DataRequired(), Length(max=64)])
    color = StringField(_l("Couleur"), validators=[DataRequired(), Length(max=7)], default="#000000")
    submit = SubmitField(_l("Enregistrer"))
