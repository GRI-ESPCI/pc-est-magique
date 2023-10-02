"""PC est magique - Profile-related Forms"""

import wtforms
from wtforms.fields import html5
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from flask import Flask
from flask_wtf.file import FileField, FileAllowed
from app.utils.validators import (
    DataRequired,
    Optional,
    InputRequired,
    Email,
    Length,
)

app = Flask(__name__)


class ClubQForm(FlaskForm):
    """WTForm used to send the wish for the current Club Q Season"""

    submit = wtforms.SubmitField(_l("Mettre à jour"))


class SettingClubQPage(FlaskForm):
    """WTForm used to say if the page should be visible or not"""

    submit = wtforms.SubmitField(_l("Mettre à jour"))


class SettingAlgoClubQPage(FlaskForm):
    """WTForm for the various options of the algorithm of club q"""

    save_attribution = wtforms.BooleanField(_l("Sauvegarder l'attribution"), default=False)
    corruption = wtforms.BooleanField(_l("Corruption"), default=False)
    submit = wtforms.SubmitField(_l("Mettre à jour"))
    launch_algorithm = wtforms.SubmitField(_l("Lancer l'algorithme"))


class AddVoeu(FlaskForm):
    priorite_add = wtforms.IntegerField(_l("Priorité"), validators=[InputRequired()])
    places_demandees_add = wtforms.IntegerField(_l("Places demandées"), validators=[InputRequired()])
    places_minimum_add = wtforms.IntegerField(_l("Places minimum"), validators=[Optional()])
    places_attribuees_add = wtforms.IntegerField(_l("Places attribuées"), validators=[InputRequired()])
    submit_add = wtforms.SubmitField(_l("Ajouter"))


class EditVoeu(FlaskForm):
    id_edit = wtforms.HiddenField("", validators=[InputRequired()])
    priorite_edit = wtforms.IntegerField("Priorité", validators=[InputRequired()])
    places_demandees_edit = wtforms.IntegerField("Places demandées", validators=[InputRequired()])
    places_minimum_edit = wtforms.IntegerField("Places minimum", validators=[Optional()])
    places_attribuees_edit = wtforms.IntegerField("Places attribuées", validators=[InputRequired()])
    submit_edit = wtforms.SubmitField(_l("Modifier"))
    delete_edit = wtforms.SubmitField(_l("Supprimer"))


class EditSaison(FlaskForm):
    id = wtforms.HiddenField("")
    nom = wtforms.StringField("Nom de la saison", validators=[DataRequired()])
    promo = wtforms.IntegerField("Promo organisatrice", validators=[DataRequired()])
    debut = html5.DateField("Date de début de la saison", validators=[Optional()])
    fin = html5.DateField("Date de fin de la saison", validators=[Optional()])
    fin_inscription = html5.DateField("Date de fin d'inscription", validators=[Optional()])
    add = wtforms.SubmitField(_l("Ajouter"))
    modify = wtforms.SubmitField(_l("Modifier"))
    delete = wtforms.SubmitField(_l("Supprimer"))


class EditSalle(FlaskForm):
    id = wtforms.HiddenField("")
    nom = wtforms.StringField("Nom de la salle", validators=[DataRequired()])
    description = wtforms.TextAreaField("Description de la salle", validators=[Optional(), Length(max=2500)])
    url = wtforms.StringField("Site internet", validators=[Optional()])
    adresse = wtforms.StringField("Adresse de la salle", validators=[Optional()])
    latitude = wtforms.DecimalField("Latitude", validators=[Optional()], default=0)
    longitude = wtforms.DecimalField("Longitude", validators=[Optional()], default=0)
    add = wtforms.SubmitField(_l("Ajouter"))
    modify = wtforms.SubmitField(_l("Modifier"))
    delete = wtforms.SubmitField(_l("Supprimer"))


class EditSpectacle(FlaskForm):
    id = wtforms.HiddenField("")
    nom = wtforms.StringField("Nom", validators=[DataRequired()])
    description = wtforms.TextAreaField("Description", validators=[Optional(), Length(max=2500)])
    categorie = wtforms.StringField("Catégorie", validators=[Optional()])
    image = wtforms.FileField(_l(""), validators=[FileAllowed(["jpg"], "JPG uniquement!")])
    date = html5.DateField("Date", validators=[InputRequired()])
    time = html5.TimeField("Heure", validators=[InputRequired()])
    nb_tickets = wtforms.IntegerField("Nombre de places", validators=[DataRequired()])
    price = wtforms.DecimalField("Prix par place (€)", places=2, validators=[DataRequired()])
    add = wtforms.SubmitField(_l("Ajouter"))
    modify = wtforms.SubmitField(_l("Modifier"))
    delete = wtforms.SubmitField(_l("Supprimer"))


class EditDiscontent(FlaskForm):
    id = wtforms.HiddenField("")
    discontent = wtforms.DecimalField(_l("Mécontentement"), validators=[DataRequired()], default=0)
    modify = wtforms.SubmitField(_l("Modifier"))


class Mail(FlaskForm):
    reply_to = html5.EmailField(
        _l("Adresse e-mail de réponse"),
        validators=[DataRequired(), Length(max=120), Email()],
    )
    date = html5.DateField("Date de payement", validators=[DataRequired()])
    threshold = wtforms.IntegerField(
        "Envoyer à partir du x-ème email (à utiliser en cas de bug)", validators=[Optional()]
    )
    submit_mail = wtforms.SubmitField(_l("Envoyer les e-mails"))

class Brochure(FlaskForm):
    """WTForm used to upload club Q brochures."""

    id = wtforms.HiddenField("")
    pdf_file = FileField(_l(""), validators=[FileAllowed(["pdf"], "PDF uniquement!")])
    add = wtforms.SubmitField(_l("Ajouter"))
