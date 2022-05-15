"""Intranet de la Rez - Gris Pages Routes"""

import contextlib
import io
import traceback
import sys

import flask
from flask_babel import _

from app import context
from app.routes.gris import bp, forms
from app.models import PCeen, Role, PermissionScope, PermissionType
from app.routes.gris.utils import (
    add_perm,
    add_remove_role,
    get_perm_elements,
    remove_perm,
)
from app.utils import helpers, typing


@bp.route("/pceens", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.pceen)
def pceens() -> typing.RouteReturn:
    """PCéens list page."""
    form = forms.AddRemoveRoleForm()
    if form.is_submitted():
        # Check request is well formed
        if form.validate():
            return add_remove_role(
                form.action.data, form.pceen_id.data, form.role_id.data
            )
        else:
            return "Bad formed request", 400

    return flask.render_template(
        "gris/pceens.html",
        form=form,
        pceens=PCeen.query.all(),
        roles=Role.query.all(),
        title=_("Gestion des PCéens"),
    )


@bp.route("/roles", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.role)
def roles() -> typing.RouteReturn:
    """Roles list page."""
    form = forms.AddRemovePermissionForm()
    if form.is_submitted():
        # Check request is well formed
        if not form.validate():
            return "Bad formed request", 400
        match form.action.data:
            case "get_elements":
                return get_perm_elements(form.scope_name.data)
            case "add":
                return add_perm(
                    form.role_id.data,
                    form.perm_id.data,
                    form.type_name.data,
                    form.scope_name.data,
                    form.ref_id.data,
                )
            case "remove":
                return remove_perm(form.role_id.data, form.perm_id.data)
            case action:
                return f"Invalid action '{action}'", 400

    return flask.render_template(
        "gris/roles.html",
        form=form,
        roles=Role.query.all(),
        title=_("Gestion des rôles"),
    )


@bp.route("/run_script", methods=["GET", "POST"])
@context.gris_only
def run_script() -> typing.RouteReturn:
    """Run an IntraRez script."""
    form = forms.ChoseScriptForm()
    if form.validate_on_submit():
        # Exécution du script
        _stdin = sys.stdin
        sys.stdin = io.StringIO()  # Block script for wainting for stdin
        try:
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                with contextlib.redirect_stderr(sys.stdout):
                    try:
                        helpers.run_script(form.script.data)
                    except Exception:
                        output = stdout.getvalue() + traceback.format_exc()
                    else:
                        output = stdout.getvalue()
        finally:
            sys.stdin = _stdin

        output_str = str(flask.escape(output))
        output = flask.Markup(output_str.replace("\n", "<br/>").replace(" ", "&nbsp;"))
        return flask.render_template(
            "gris/run_script.html",
            form=form,
            output=output,
            title=_("Exécuter un script"),
        )
    return flask.render_template(
        "gris/run_script.html", form=form, output=None, title=_("Exécuter un script")
    )
