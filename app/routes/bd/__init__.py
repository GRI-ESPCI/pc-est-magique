"""PC est magique - BD (Bandes Dessinées) Blueprint"""

import flask

bp = flask.Blueprint("bd", __name__)

# ! Keep at the bottom to avoid circular import issues !
from app.routes.bd import routes  # noqa: E402, F401
