"""PC est magique - Bar Forms"""

from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, IntegerField, BooleanField, FieldList, HiddenField
from wtforms.validators import DataRequired, Optional, NumberRange, Length

from app.utils.validators import NewBarItemName, ValidBarItemID


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


class GlobalSettingsForm(FlaskForm):
    """Global settings form."""

    value = FieldList(IntegerField(_l("Key")))
    submit = SubmitField(_l("Submit"))

    def __init__(self, *args, **kwargs):
        """Populate form with existing values."""
        super(GlobalSettingsForm, self).__init__l(*args, **kwargs)
        if "obj" in kwargs and kwargs["obj"] is not None:
            self.value.label.text = kwargs["obj"].key
