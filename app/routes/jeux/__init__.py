"""PC est magique - Jeux Blueprint"""

import flask
from flask_babel import _

bp = flask.Blueprint("jeux", __name__)


@bp.before_request
def check_jeux_access():
    """Check login and role/permission access for all Jeux routes."""
    from app import context
    from app.enums import PermissionScope, PermissionType
    from app.utils import helpers

    if not context.g.logged_in:
        flask.flash(
            _("Veuillez vous authentifier pour accéder à cette page."),
            "warning",
        )
        return helpers.ensure_safe_redirect("auth.auth_needed")

    is_eleve = context.g.logged_in_user.has_role("Élève")
    has_access = context.has_permission(PermissionType.read, PermissionScope.jeux)

    if not (is_eleve or has_access):
        flask.flash(_("Vous n'avez pas accès au module Jeux."), "danger")
        return flask.redirect(flask.url_for("main.index"))

    return None


# ! Keep at the bottom to avoid circular import issues !
from app.routes.jeux import routes
