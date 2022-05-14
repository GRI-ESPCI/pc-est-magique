"""PC est magique - Gris-only Pages Blueprint"""

import flask

bp = flask.Blueprint("gris", __name__, template_folder="templates")

# ! Keep at the bottom to avoid circular import issues !
from app.gris import routes
