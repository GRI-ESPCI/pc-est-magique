"""PC est magique - SAML Authentication Blueprint"""

import flask

bp = flask.Blueprint("auth_saml", __name__)

# ! Keep at the bottom to avoid circular import issues !
from app.routes.auth.saml import routes
