"""PC est magique - Main Pages Blueprint"""

import flask

bp = flask.Blueprint("main", __name__, template_folder="templates")

# ! Keep at the bottom to avoid circular import issues !
from app.main import routes
