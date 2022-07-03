"""PC est magique - Photos Gallery Blueprint"""

import flask

bp = flask.Blueprint("photos", __name__)

# ! Keep at the bottom to avoid circular import issues !
from app.routes.photos import routes
