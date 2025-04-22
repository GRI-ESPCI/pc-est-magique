"""PC est magique - Theater Pages Routes"""

import os

import flask
from flask import url_for
from flask_babel import _

from app import context, db
from app.models import (
    PermissionScope,
    PermissionType,
    Spectacle,
    Saison
)
from app.routes.theatre.forms import EditSaison
from app.routes.theatre import bp
from app.utils import typing


@bp.route("")
@bp.route("/")
@bp.route("/<saison_id>")
def main(saison_id="") -> typing.RouteReturn:
    """PC est magique profile page."""
    saisons = Saison.query.order_by(Saison.start_date.desc()).all()

    if saison_id == "":
        current_saison = saisons[0]
    else:
        current_saison = Saison.query.get(saison_id)
        if current_saison == None:
            flask.abort(404)

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
        title=_("Saison Théâtrale du Club Théâtre"),
        can_edit=can_edit,
        folder=folder,
        html_file=html_file,
        saisons=saisons,
        current_saison=current_saison
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

@bp.route("/admin")
@context.permission_only(PermissionType.write, PermissionScope.theatre)
def admin():

    saisons = Saison.query.order_by(Saison.start_date.desc()).all()

    return flask.render_template(
        "theatre/admin.html",
        saisons=saisons
    )

@bp.route("/admin/saison/<id>")
@context.permission_only(PermissionType.write, PermissionScope.theatre)
def admin_saison(id: int):

    saison = Saison.query.get(id)
    if saison is None:
        flask.abort(404)

    return flask.render_template(
        "theatre/admin_saison.html",
        saison=saison
    )

@bp.route("/admin/saison/new", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.theatre)
def admin_saison_new():

    form = EditSaison()

    if form.validate_on_submit():
        saison = Saison()
        saison.name = form.name.data
        saison.description = form.description.data
        saison.start_date = form.start_date.data

        db.session.add(saison)
        db.session.commit()

        return flask.redirect(
            url_for("theatre.admin_saison", id=saison.id)
        )

    return flask.render_template(
        "theatre/admin_saison_new.html",
        form=form
    )

@bp.route("/admin/saison/edit/<id>", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.theatre)
def admin_saison_edit(id: int):

    saison = Saison.query.get(id)
    if saison is None:
        flask.abort(404)

    form = EditSaison(obj=saison)

    if form.validate_on_submit():
        saison.name = form.name.data
        saison.description = form.description.data
        saison.start_date = form.start_date.data

        db.session.commit()

        return flask.redirect(
            url_for("theatre.admin_saison", id=saison.id)
        )

    return flask.render_template(
        "theatre/admin_saison_edit.html",
        saison=saison,
        form=form
    )

@bp.route("/admin/spectacle/<id>")
@context.permission_only(PermissionType.write, PermissionScope.theatre)
def admin_spectacle(id: int):
    spectacle = Spectacle.query.get(id)
    if spectacle is None:
        flask.abort(404)
    
    return flask.render_template(
        "theatre/admin_spectacle.html",
        spectacle=spectacle
    )