from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp
from flask_babel import lazy_gettext as _l

class EditClub(FlaskForm):
    name = StringField(_l("Nom du club"), validators=[DataRequired(), Length(max=64)])
    color = StringField(_l("Couleur"), validators=[DataRequired(), Regexp(r'^#[0-9A-Fa-f]{6}$', message=_l("Couleur invalide"))], default="#000000")
    submit = SubmitField(_l("Enregistrer"))
