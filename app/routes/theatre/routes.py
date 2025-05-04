"""PC est magique - Theater Pages Routes"""

import os
import mimetypes
import pathlib

from babel.util import missing
import flask
from flask import url_for, request, current_app
from flask_babel import _

from app import context, db
from app.models import (
    PermissionScope,
    PermissionType,
    Spectacle,
    Saison
)
from app.models.theatre import Representation
from app.routes.theatre.forms import EditRepresentation, EditSaison, EditSpectacle, SendPicture
from app.routes.theatre import bp
from app.utils import typing

"""
TODO:
    - HTML editor for spectacle and saison
    - Add representation to spectacle and edit
    - (Maybe) Custom reservation
    - Update frontend for user
"""


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

    picture_form = SendPicture()

    return flask.render_template(
        "theatre/admin_saison.html",
        saison=saison,
        picture_form=picture_form
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

    picture_form = SendPicture()

    spectacle = Spectacle.query.get(id)
    if spectacle is None:
        flask.abort(404)
    
    return flask.render_template(
        "theatre/admin_spectacle.html",
        spectacle=spectacle,
        picture_form=picture_form
    )

@bp.route("/admin/spectacle/edit/<id>", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.theatre)
def admin_spectacle_edit(id: int):

    spectacle = Spectacle.query.get(id)
    if spectacle is None:
        flask.abort(404)

    form = EditSpectacle(obj=spectacle)

    if form.validate_on_submit():

        spectacle.name = form.name.data
        spectacle.description = form.description.data
        spectacle.director = form.director.data
        spectacle.author = form.author.data
        spectacle.ticket_link = form.ticket_link.data
        spectacle.places = form.places.data        

        db.session.commit()

        return flask.redirect(
            url_for("theatre.admin_spectacle", id=spectacle.id)
        )

    return flask.render_template(
        "theatre/admin_spectacle_edit.html",
        spectacle=spectacle,
        form=form
    )

@bp.route("/admin/spectacle/new/<saison_id>", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.theatre)
def admin_spectacle_new(saison_id: int):

    form = EditSpectacle()
    saison = Saison.query.get(saison_id)
    if saison is None:
        flask.abort(404)

    if form.validate_on_submit():
        spectacle = Spectacle()
        spectacle.name = form.name.data
        spectacle.description = form.description.data
        spectacle.director = form.director.data
        spectacle.author = form.author.data
        spectacle.ticket_link = form.ticket_link.data
        spectacle.places = form.places.data
        spectacle.saison = saison

        # Legacy compatibility
        spectacle.year = 0

        print(spectacle.id)

        db.session.add(spectacle)
        db.session.commit()

        return flask.redirect(
            url_for("theatre.admin_spectacle", id=spectacle.id)
        )

    return flask.render_template(
        "theatre/admin_spectacle_new.html",
        form=form,
        saison=saison
    )

@bp.route("/admin/representation/new/<spectacle_id>", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, scope=PermissionScope.theatre)
def admin_representation_new(spectacle_id: int):

    form = EditRepresentation()
    spectacle = Spectacle.query.get(spectacle_id)
    if spectacle is None:
        return flask.abort(404)

    if form.validate_on_submit():
        rep = Representation()
        rep.date = form.date.data
        rep.spectacle = spectacle

        db.session.add(rep)
        db.session.commit()

        return flask.redirect(
            url_for("theatre.admin_spectacle", id=spectacle.id)
        )

    return flask.render_template(
        "theatre/admin_representation_new.html",
        spectacle=spectacle,
        form=form
    )

@bp.route("/admin/representation/delete/<rep_id>")
@context.permission_only(PermissionType.write, scope=PermissionScope.theatre)
def admin_representation_delete(rep_id: int):
    rep = Representation.query.get(rep_id)
    if rep is None:
        flask.abort(404)

    s_id = rep.spectacle.id

    db.session.delete(rep)
    db.session.commit()

    flask.flash(_("Réprésentation annulée."), category="success")
    return flask.redirect(
        url_for("theatre.admin_spectacle", id=s_id)
    )

@bp.route("/admin/picture_upload/<type>/<id>", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.theatre)
def picture_upload(type: str, id: int):
    """
    Handle picture uploading for season and spectacle posters.

    Path structure:

    - `saison_<id>/saison_<id>.<jpg|png>` for season poster
    - `saison_<id>/spectacle_<id>.<jpg|png>` for spectacle poster
    """

    next_url = request.args.get('next_url')
    form = SendPicture()

    if form.validate_on_submit():

        ext = form.picture.data.filename.split(".")[-1]

        if type == "saison":
            saison = Saison.query.get(id)
            if saison is None:
                flask.abort(404)
            old_filename = f"saison_{saison.id}.{saison.image_extension}"
            filename = f"saison_{saison.id}.{ext}"
            path = f"saison_{saison.id}/"

            # Remove old picture
            pathlib.Path(os.path.join(
                current_app.config['THEATRE_BASE_PATH'],
                path,
                old_filename
            )).unlink(missing_ok=True)

            # Create folder
            pathlib.Path(os.path.join(
                current_app.config['THEATRE_BASE_PATH'],
                path
            )).mkdir(parents=True, exist_ok=True)

            # Save new picture
            form.picture.data.save(
                os.path.join(
                    current_app.config['THEATRE_BASE_PATH'],
                    path,
                    filename
                )
            )

            saison.image_extension = ext
            db.session.commit()

        elif type == "spectacle":
            spectacle = Spectacle.query.get(id)
            if spectacle is None:
                flask.abort(404) 
            old_filename = f"spectacle_{spectacle.id}.{spectacle.image_extension}"
            filename = f"spectacle_{spectacle.id}.{ext}"
            path = f"saison_{spectacle.saison.id}/"

            # Remove old picture
            pathlib.Path(os.path.join(
                current_app.config['THEATRE_BASE_PATH'],
                path,
                old_filename
            )).unlink(missing_ok=True)

            # Create folder
            pathlib.Path(os.path.join(
                current_app.config['THEATRE_BASE_PATH'],
                path
            )).mkdir(parents=True, exist_ok=True)

            # Save new picture
            form.picture.data.save(
                os.path.join(
                    current_app.config['THEATRE_BASE_PATH'],
                    path,
                    filename
                )
            )

            spectacle.image_extension = ext
            db.session.commit()
            
        else:
            flask.flash(_("Type de téléversement non valide."))
            return flask.redirect(next_url)
            
        flask.flash(_("Image téléversée."), category="success")
    else:
        flask.flash(_("Erreur lors du téléversement de l'image."), category="error")


    return flask.redirect(next_url)