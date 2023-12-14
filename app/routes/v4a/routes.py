"""PC est magique - V4A Pages Routes"""

import flask
from flask_babel import _

from app.routes.v4a import bp
from app.utils import typing

from app.models import V4A
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
def edit(v4a_id: int) -> typing.RouteReturn:
    """Edit page of V4A"""

    v4a = V4A.query.filter_by(id=v4a_id).first()
    edit_form = forms.EditV4A(obj=v4a)

    if edit_form.validate_on_submit():
        pass

    return flask.render_template(
        "v4a/edit.html",
        title=v4a.name,
        v4a=v4a,
        edit_form=edit_form
    )