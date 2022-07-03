"""PC est magique - Profile Pages Blueprint"""

import flask

bp = flask.Blueprint("profile", __name__)

# ! Keep at the bottom to avoid circular import issues !
from app.routes.profile import routes
