"""PC est magique - Calendar Blueprint"""

import flask

bp = flask.Blueprint("calendar", __name__)

from app.routes.calendar import routes
