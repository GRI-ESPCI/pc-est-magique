"""PC est magique - BD-related Forms"""

from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
import wtforms


class UploadCatalogueForm(FlaskForm):
    """WTForm to upload the BD catalogue XLSX file."""

    fichier = wtforms.FileField(
        _l("Fichier catalogue (.xlsx)"),
        validators=[
            FileRequired(),
            FileAllowed(["xlsx"], _l("Seuls les fichiers .xlsx sont acceptés.")),
        ],
    )
    submit = wtforms.SubmitField(_l("Importer le catalogue"))
