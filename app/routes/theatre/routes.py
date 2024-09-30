"""PC est magique - Theater Pages Routes"""

import flask, os
from flask_babel import _

from app import context, db
from app.models import PermissionScope, PermissionType, Spectacle
from app.routes.theatre import bp
from app.utils import typing


@bp.route("")
@bp.route("/")
def main() -> typing.RouteReturn:
    """PC est magique profile page."""
    spectacles = Spectacle.query.order_by(Spectacle.id).all()

    can_edit = context.has_permission(PermissionType.write, PermissionScope.theatre)

    folder = "theatre"
    filename = "introduction.html"
    filepath = os.path.join(flask.current_app.config["THEATRE_BASE_PATH"], filename)
    if not os.path.exists(filepath):
        open(filepath, "w").close()
    with open(filepath, "r") as f:
        html_file = f.read()

    return flask.render_template(
        "theatre/main.html",
        title=_("Saison Théâtrale du Club Théâtre 140"),
        spectacles=spectacles,
        can_edit=can_edit,
        folder=folder,
        html_file=html_file,
    )


@bp.route("/edit_text", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.theatre)
def edit_text():
    content = flask.request.form.get("content")  # Retrieve the content from the POST request
    path = os.path.join(flask.current_app.config["THEATRE_BASE_PATH"], "introduction.html")
    with open(path, "w") as file:
        file.write(content)

    flask.flash(_("Introduction mise à jour."))
    return flask.redirect(flask.url_for("theatre.main"))
