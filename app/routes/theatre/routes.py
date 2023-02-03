"""PC est magique - Profile Pages Routes"""

import flask
from flask_babel import _

from app import context, db
from app.models import Spectacle, Representation
from app.routes.theatre import bp
from app.utils import helpers, typing


@bp.route("/")
def main() -> typing.RouteReturn:
    """PC est magique profile page."""
    spectacles = Spectacle.query.all()
    representations = Representation.query.all()
    return flask.render_template("theatre/main.html", title=_("Théâtre"), spectacles=spectacles, representations=representations)

