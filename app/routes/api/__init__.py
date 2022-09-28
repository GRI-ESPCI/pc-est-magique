"""PC est magique - API routes Blueprint"""

from flask import Blueprint

bp = Blueprint("api", __name__)

from app.routes.api import handlers
from app.routes.api import routes

bp.register_blueprint(routes.bar.sbp, url_prefix="/bar")
bp.register_blueprint(routes.gris.sbp, url_prefix="/gris")
