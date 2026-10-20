"""PC est magique - Jeux-related Forms"""

from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
import wtforms
from wtforms.validators import DataRequired, Length, Optional


class UploadCatalogueForm(FlaskForm):
    """WTForm to upload the Jeux catalogue ODS or XLSX file."""

    fichier = wtforms.FileField(
        _l("Fichier catalogue (.ods, .xlsx)"),
        validators=[
            FileRequired(),
            FileAllowed(
                ["ods", "xlsx"],
                _l("Seuls les fichiers .ods et .xlsx sont acceptés."),
            ),
        ],
    )
    submit = wtforms.SubmitField(_l("Importer le catalogue"))


class AddJeuForm(FlaskForm):
    """WTForm to manually add a single game in the Jeux catalogue."""

    nom = wtforms.StringField(
        _l("Nom du jeu"),
        validators=[DataRequired(), Length(max=500)],
    )
    categorie = wtforms.StringField(
        _l("Catégorie"),
        default="Autres",
        validators=[DataRequired(), Length(max=100)],
    )
    temps_de_jeu = wtforms.StringField(
        _l("Temps de jeu"),
        validators=[Optional(), Length(max=100)],
    )
    nb_joueurs = wtforms.StringField(
        _l("Nombre de joueurs"),
        validators=[Optional(), Length(max=100)],
    )
    popularite = wtforms.StringField(
        _l("Popularité"),
        validators=[Optional(), Length(max=100)],
    )
    nota_bene = wtforms.TextAreaField(
        _l("Nota Bene / Commentaires"),
        validators=[Optional()],
    )
    resume = wtforms.TextAreaField(
        _l("Résumé / Description"),
        validators=[Optional()],
    )
    image_url = wtforms.StringField(
        _l("Lien externe de couverture"),
        validators=[Optional(), Length(max=500)],
    )
    cover_file = wtforms.FileField(
        _l("Ou importer une image de couverture"),
        validators=[
            Optional(),
            FileAllowed(
                ["jpg", "jpeg", "png", "webp", "gif"],
                _l("Seules les images JPG, PNG, WEBP ou GIF sont acceptées."),
            ),
        ],
    )
    submit_add = wtforms.SubmitField(_l("Ajouter le jeu"))
