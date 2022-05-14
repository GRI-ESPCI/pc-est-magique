"""PC est magique - Authentication Blueprint"""

import flask

bp = flask.Blueprint("auth", __name__, template_folder="templates")

# ! Keep at the bottom to avoid circular import issues !
from app.auth import routes
