"""PC est magique - Bar Pages Blueprint"""

from flask import Blueprint

bp = Blueprint("bar", __name__)

from app.routes.bar import routes
