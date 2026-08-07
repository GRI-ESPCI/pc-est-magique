"""PC est magique Flask App - Casino Blueprint"""

import flask
from flask import Blueprint
from flask_babel import _

bp = Blueprint("casino", __name__)

@bp.before_request
def check_casino_access():
    """Check login, role access, and admin permissions for all casino routes."""
    from app import context
    from app.enums import PermissionType, PermissionScope
    
    if not context.g.logged_in:
        return context.redirect_login()
    
    is_eleve = context.g.logged_in_user.has_role("Élève")
    is_admin = context.has_permission(PermissionType.read, PermissionScope.casino)
    
    if not (is_eleve or is_admin):
        flask.flash(_("Vous n'avez pas accès au Casino."), "danger")
        return flask.redirect(flask.url_for("main.index"))
    
    # Admin routes require write permission
    if flask.request.path.startswith("/casino/admin"):
        if not context.has_permission(PermissionType.write, PermissionScope.casino):
            flask.flash(_("Vous n'avez pas la permission de gérer le Casino."), "danger")
            return flask.redirect(flask.url_for("casino.index"))
    
    return None

from app.routes.casino import main, admin
