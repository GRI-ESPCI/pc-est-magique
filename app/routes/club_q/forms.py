"""PC est magique - Profile-related Forms"""

import wtforms
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from flask import Flask

app = Flask(__name__)


class ClubQForm(FlaskForm):
    """WTForm used to send the wish for the current Club Q Season"""

    submit = wtforms.SubmitField(_l("Mettre à jour"))


class SettingClubQPage(FlaskForm):
    """WTForm used to say if the page should be visible or not"""

    submit = wtforms.SubmitField(_l("Mettre à jour"))


