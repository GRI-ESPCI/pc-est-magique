"""PC est magique - Club Q Pages Blueprint"""

import flask

bp = flask.Blueprint("club_q", __name__)

# ! Keep at the bottom to avoid circular import issues !
from app.routes.club_q import routes
