"""PC est magique - V4A Pages Routes"""

import os

import flask
from flask import jsonify
from flask_babel import _

from app.routes.v4a import bp
from app import helpers, db, context
from app.utils import typing, wysiwyg
from app.models import V4A, PermissionScope, PermissionType
from app.routes.v4a import forms

@bp.route("")
@bp.route("/")
def main() -> typing.RouteReturn:
    v4a = V4A.query.filter_by(visible=True).all()

    return flask.render_template(
        "v4a/main.html",
        title=_("V4A - Voyage 4ème année"),
        v4a=v4a
    )

@bp.route("/<v4a_id>")
def full_description(v4a_id: int) -> typing.RouteReturn:
    """Homepage of one V4A"""

    v4a = V4A.query.filter_by(id=v4a_id).first()

    return flask.render_template(
        "v4a/full_description.html",
        title=v4a.name,
        v4a=v4a,
        can_edit=True
    )

@bp.route("/<v4a_id>/edit", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.v4a)
def edit(v4a_id: int) -> typing.RouteReturn:
    """Edit page of V4A"""

    v4a = V4A.query.filter_by(id=v4a_id).first()
    edit_form = forms.EditV4A(obj=v4a)

    if edit_form.validate_on_submit():
        edit_form.populate_obj(v4a)
        v4a.full_description = wysiwyg.parse_delta_to_html(
            edit_form.delta_full_description.data
        )

        if edit_form.image_file.data:
            with open(os.path.join("app", "static", "img", "v4a",
            f"{v4a.id}.png"), "wb") as fh:
                fh.write(edit_form.image_file.data.read())

        db.session.commit()

        flask.flash(_("V4A mis à jour avec succès."), "success")

        return helpers.ensure_safe_redirect("v4a.full_description", v4a_id=v4a.id)


    return flask.render_template(
        "v4a/edit.html",
        title=v4a.name,
        v4a=v4a,
        edit_form=edit_form
    )