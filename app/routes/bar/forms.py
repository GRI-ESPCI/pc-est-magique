"""PC est magique - Bar Forms"""

import flask
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField,
    FloatField,
    IntegerField,
    BooleanField,
    FieldList,
)
from wtforms.validators import ValidationError, DataRequired, Optional, NumberRange, Length
from app.models import BarItem


class AddOrEditItemForm(FlaskForm):
    """Item editing form."""

    name = StringField(_l("Nom"), validators=[DataRequired(), Length(max=64)])
    quantity = IntegerField(
        _l("Quantité (laisser vide si non quantifiable)"), validators=[Optional(), NumberRange(min=0)]
    )
    price = FloatField(_l("Price"), validators=[DataRequired(), NumberRange(min=0)])
    is_alcohol = BooleanField(_l("Alcool"))
    is_quantifiable = BooleanField(_l("Quantifiable"))
    is_favorite = BooleanField(_l("Favori"))

    submit = SubmitField(_l("Valider"))

    def __init__(self, original_name=None, *args, **kwargs):
        """Store original name to validate the new one."""
        super().__init__l(*args, **kwargs)
        self.original_name = original_name

    def validate_name(self, name):
        """Validate name."""
        if name.data != self.original_name and BarItem.query.filter_by(name=name.data).first():
            raise ValidationError("Please use a different name.")


class SearchForm(FlaskForm):
    """User search form."""

    class Meta:
        """Search form doesn't need CSRF."""

        csrf = False

    q = StringField(_l("Search"))

    def __init__(self, *args, **kwargs):
        """Store GET arguments."""
        if "formdata" not in kwargs:
            kwargs["formdata"] = flask.request.args
        super().__init__(*args, **kwargs)


class GlobalSettingsForm(FlaskForm):
    """Global settings form."""

    value = FieldList(IntegerField(_l("Key")))
    submit = SubmitField(_l("Submit"))

    def __init__(self, *args, **kwargs):
        """Populate form with existing values."""
        super(GlobalSettingsForm, self).__init__l(*args, **kwargs)
        if "obj" in kwargs and kwargs["obj"] is not None:
            self.value.label.text = kwargs["obj"].key
