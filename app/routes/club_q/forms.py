"""PC est magique - Profile-related Forms"""

import wtforms
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from flask import Flask
from app.utils.validators import (
    DataRequired,
    Optional
)

app = Flask(__name__)


class ClubQForm(FlaskForm):
    """WTForm used to send the wish for the current Club Q Season"""

    submit = wtforms.SubmitField(_l("Mettre à jour"))


class SettingClubQPage(FlaskForm):
    """WTForm used to say if the page should be visible or not"""

    submit = wtforms.SubmitField(_l("Mettre à jour"))


class SettingAlgoClubQPage(FlaskForm):
    """WTForm used to say if the page should be visible or not"""

    submit = wtforms.SubmitField(_l("Mettre à jour"))



class EditVoeu(FlaskForm):
    id = wtforms.HiddenField("", validators=[DataRequired()])
    priorite = wtforms.IntegerField("Priorité", validators=[DataRequired()])
    places_demandees = wtforms.IntegerField("Places demandées", validators=[DataRequired()])
    places_minimum = wtforms.IntegerField("Places minimum", validators=[Optional()])
    places_attribuees = wtforms.IntegerField("Places attribuées", validators=[DataRequired()])
    submit = wtforms.SubmitField(_l("Mettre à jour"))

class DeleteVoeu(FlaskForm):
    id_d = wtforms.HiddenField("", validators=[DataRequired()])
    submit = wtforms.SubmitField(_l("Supprimer"))