"""PC est magique - Profile-related Forms"""

import wtforms
from wtforms.fields import html5
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from flask import Flask
from app.utils.validators import (
    DataRequired, 
    Optional, 
    InputRequired,
    Email,
    Length,
    NewEmail
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


class AddVoeu(FlaskForm):
    priorite_add = wtforms.IntegerField("Priorité", validators=[InputRequired()])
    places_demandees_add = wtforms.IntegerField("Places demandées", validators=[InputRequired()])
    places_minimum_add = wtforms.IntegerField("Places minimum", validators=[Optional()])
    places_attribuees_add = wtforms.IntegerField("Places attribuées", validators=[InputRequired()])
    submit_add = wtforms.SubmitField(_l("Ajouter"))


class EditVoeu(FlaskForm):
    id_edit = wtforms.HiddenField("", validators=[InputRequired()])
    priorite_edit = wtforms.IntegerField("Priorité", validators=[InputRequired()])
    places_demandees_edit = wtforms.IntegerField("Places demandées", validators=[InputRequired()])
    places_minimum_edit = wtforms.IntegerField("Places minimum", validators=[Optional()])
    places_attribuees_edit = wtforms.IntegerField("Places attribuées", validators=[InputRequired()])
    submit_edit = wtforms.SubmitField(_l("Modifier"))
    delete_edit = wtforms.SubmitField(_l("Supprimer"))


class Mail(FlaskForm):
    reply_to = html5.EmailField(
        _l("Adresse e-mail de réponse"),
        validators=[DataRequired(), Length(max=120), Email()],
    )
    date = html5.DateField("Date de payement", validators=[DataRequired()])
    threshold = wtforms.IntegerField("Envoyer à partir du x-ème email (à utiliser en cas de bug)" ,validators=[Optional()])
    submit_mail = wtforms.SubmitField(_l("Envoyer les e-mails"))