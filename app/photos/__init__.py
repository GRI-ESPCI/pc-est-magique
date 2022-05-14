"""PC est magique - Photos Gallery Blueprint"""

import flask

bp = flask.Blueprint("photos", __name__, template_folder="templates")

# ! Keep at the bottom to avoid circular import issues !
from app.photos import routes
