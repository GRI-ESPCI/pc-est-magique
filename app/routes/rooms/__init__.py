"""PC est magique - Rooms Pages Blueprint"""

import flask

bp = flask.Blueprint("rooms", __name__)

# ! Keep at the bottom to avoid circular import issues !
from app.routes.rooms import routes
