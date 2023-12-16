"""PC est magique - V4A Pages Routes"""

import os

import flask
from flask import jsonify
from flask_babel import _

from app.routes.v4a import bp
from app import helpers, db, context
from app.utils import typing, wysiwyg
from app.models import V4A, PermissionScope, PermissionType, V4ARepresentation
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
    can_edit = context.has_permission(
        PermissionType.write,
        PermissionScope.v4a
    )

    add_rep_form = forms.EditRepresentation()

    return flask.render_template(
        "v4a/full_description.html",
        title=v4a.name,
        v4a=v4a,
        can_edit=can_edit,
        add_rep_form=add_rep_form
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

@bp.route("/<v4a_id>/add_representation", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.v4a)
def add_representation(v4a_id: int) -> typing.RouteReturn:
    v4a = V4A.query.get(v4a_id)
    rep = V4ARepresentation()
    edit_form = forms.EditRepresentation()

    if edit_form.validate_on_submit:
        db.session.add(rep)
        rep.date = edit_form.date.data
        rep.sits = edit_form.sits.data
        rep._v4a_id = v4a.id
        v4a.representations.append(rep)
        db.session.commit()

        flask.flash(_("Représentaiton ajouté avec succès."), "success")

        return helpers.ensure_safe_redirect("v4a.full_description", v4a_id=v4a.id)

@bp.route("/<rep_id>/del_representation")
@context.permission_only(PermissionType.write, PermissionScope.v4a)
def del_representation(rep_id: int) -> typing.RouteReturn:
    rep = V4ARepresentation.query.get(rep_id)
    v4a = V4A.query.get(rep._v4a_id)
    v4a.representations.remove(rep)
    db.session.delete(rep)
    db.session.commit()
    return jsonify("{'deleted': 'success'}")

@bp.route("/<rep_id>/edit_representation", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.v4a)
def edit_representation(rep_id: int) -> typing.RouteReturn:
    edit_form = forms.EditRepresentation()
    if edit_form.validate_on_submit:
        rep = V4ARepresentation.query.get(rep_id)
        edit_form.populate_obj(rep)
        print(rep.date)
        db.session.commit()
        return jsonify({'edited': 'success', 'date': rep.date, 'sits': rep.sits})
    return jsonify({'edited': 'failed'})