"""PC est magique - V4A Pages Blueprint"""

import flask

bp = flask.Blueprint("v4a", __name__)

from app.routes.v4a import routes