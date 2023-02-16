"""PC est magique - Club Q Pages Routes"""

import flask
from flask_babel import _

from app import context, db
from app.models import Client, Season, Salle, Spectacle, Voeux
from app.routes.club_q import bp
from app.utils import helpers, typing


@bp.route("")
@bp.route("/")
def main() -> typing.RouteReturn:
    """PC est magique profile page."""
    return flask.render_template("club-q/main.html", title=_("Club Q"))


