"""PC est magique - Club Q Pages Routes"""

import flask
from flask_babel import _

from app import context, db
from app.models import ClubQClient, ClubQSeason, ClubQSalle, ClubQSpectacle, ClubQVoeux
from app.routes.club_q import bp, forms
from app.utils import helpers, typing


@bp.route("")
@bp.route("/")
def main() -> typing.RouteReturn:
    """PC est magique profile page."""
    form = forms.ClubQForm()
    spectacles = ClubQSpectacle.query.order_by(ClubQSpectacle.id).all()
    
    return flask.render_template("club_q/main.html", title=_("Club Q"), form=form, spectacles=spectacles)

