"""PC est magique - Bekk Pages Blueprint"""

import flask

bp = flask.Blueprint("bekk", __name__)

# ! Keep at the bottom to avoid circular import issues !
from app.routes.bekk import routes
