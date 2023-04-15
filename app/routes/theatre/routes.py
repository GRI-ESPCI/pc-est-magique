"""PC est magique - Theater Pages Routes"""

import flask
from flask_babel import _

from app.models import Spectacle
from app.routes.theatre import bp
from app.utils import typing


@bp.route("")
@bp.route("/")
def main() -> typing.RouteReturn:
    """PC est magique profile page."""
    spectacles = Spectacle.query.order_by(Spectacle.id).all()
    return flask.render_template("theatre/main.html", title=_("Saison Théâtrale du Club Théâtre 140"), spectacles=spectacles)


