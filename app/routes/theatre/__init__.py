"""PC est magique - Theater Pages Blueprint"""

import flask

bp = flask.Blueprint("theatre", __name__)

# ! Keep at the bottom to avoid circular import issues !
from app.routes.theatre import routes
