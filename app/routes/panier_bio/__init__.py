"""PC est magique - Panier Bio Pages Blueprint"""

import flask

bp = flask.Blueprint("panier_bio", __name__)

# ! Keep at the bottom to avoid circular import issues !
from app.routes.panier_bio import routes
