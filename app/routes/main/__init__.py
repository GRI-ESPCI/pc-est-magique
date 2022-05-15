"""PC est magique - Main Pages Blueprint"""

import flask

bp = flask.Blueprint("main", __name__)

# ! Keep at the bottom to avoid circular import issues !
from app.routes.main import routes
