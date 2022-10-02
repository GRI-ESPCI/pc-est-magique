"""PC est magique - Bar Forms"""

import operator
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, IntegerField, BooleanField, HiddenField, DateField, FileField
from wtforms.validators import DataRequired, Optional, NumberRange, Length

from app.utils.validators import CompareFields, NewBarItemName, PastDate, ValidBarItemID


class AddOrEditItemForm(FlaskForm):
    """Item editing form."""

    id = HiddenField(_l("Nom"), validators=[Optional(), ValidBarItemID()])
    name = StringField(_l("Nom"), validators=[DataRequired(), Length(max=64), NewBarItemName()])
    is_quantifiable = BooleanField(_l("Quantifiable"))
    quantity = IntegerField(_l("Quantité"), validators=[Optional(), NumberRange(min=0)])
    price = FloatField(_l("Prix (en euros)"), validators=[DataRequired(), NumberRange(min=0)])
    is_alcohol = BooleanField(_l("Article alcoolisé"))
    is_quantifiable = BooleanField(_l("Quantifiable"))
    is_favorite = BooleanField(_l("Favori"))
    favorite_index = IntegerField(_l("Priorité dans la liste"), validators=[Optional(), NumberRange(min=0)])

    submit = SubmitField(_l("Valider"))


class DataExport(FlaskForm):
    """Data export form."""

    start = DateField("", validators=[DataRequired(), PastDate()])
    end = DateField(
        "",
        validators=[
            DataRequired(),
            CompareFields(operator.ge, "start", _l("Doit être postérieur à la date de début !")),
        ],
    )
    filename = StringField(_l("Nom du fichier"), validators=[Optional()])
    submit = SubmitField(_l("Télécharger"))


class GlobalSettingsForm(FlaskForm):
    """Global settings form."""

    max_daily_alcoholic_drinks_per_user = IntegerField("", validators=[DataRequired(), NumberRange(min=0)])
    background_image = FileField("", validators=[Optional()])
    delete_background_image = BooleanField(_l("Supprimer l'image actuelle"))

    submit = SubmitField(_l("Sauvegarder"))
