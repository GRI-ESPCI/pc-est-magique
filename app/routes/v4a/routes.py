"""PC est magique - V4A Pages Routes"""

import flask
from flask_babel import _

from app.routes.v4a import bp
from app.utils import typing

from app.models import V4A

@bp.route("")
@bp.route("/")
def main() -> typing.RouteReturn:
    v4a = V4A.query.filter_by(visible=True).all()

    return flask.render_template(
        "v4a/main.html",
        title=_("V4A - Voyage 4ème année"),
        v4a=v4a
    )