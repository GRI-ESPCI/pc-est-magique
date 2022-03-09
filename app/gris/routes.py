"""Intranet de la Rez - Gris Pages Routes"""

import contextlib
import io
import traceback
import sys

import flask
from flask_babel import _

from app import context, db
from app.gris import bp, forms
from app.models import PCeen, Role, PermissionScope, PermissionType
from app.tools import utils, typing


def add_remove_role(action: str,
                    pceen_id: str,
                    role_id: str) -> tuple[str | dict, int]:
    """Process a role add/remove request, or return an error.

    Args:
        action: Should be one of ``"add"`` or ``"remove"`` (else
            returns a 400).
        pceen_id: The ID of the PCeen to edit roles of (returns a 404
            if not existing).
        role_id: The ID of the role to add or delete (returns a 404 if
            not existing, or a 409 if the PCeen already has / do not
            has the role).

    Returns a 403 if the PCeen do not have the
    :attr:`~.models.PermissionType.write` permission for this role.

    Returns:
        If something is not good, the message and HTTP code to return.
        If the role was successfully removed, an empty dict with a 204.
        If the role was successfully added, a dict containing the ``"id"``,
            ``"name"``, ``"color"`` and ``"dark"`` informations of the role
            with a 201.
    """
    # Check request refer to existing objects
    if action not in ("add", "remove"):
        return f"Invalid action '{action}'", 400
    pceen = PCeen.query.get(pceen_id)
    if not pceen:
        return f"Invalid pceen_id #{pceen_id}", 404
    role = Role.query.get(role_id)
    if not role:
        return f"Invalid role {role_id}", 404
    # Check request is acceptable
    if action == "add" and role in pceen.roles:
        return f"PCeen #{pceen_id} already has role #{role_id}", 409
    if action == "remove" and role not in pceen.roles:
        return f"PCeen #{pceen_id} does not has role #{role_id}", 409
    if not flask.g.pceen.has_permission(type=PermissionType.write,
                                        scope=PermissionScope.role,
                                        elem=role):
        return "Unauthorized (you nasty cheater)", 403
    # Proceed
    try:
        if action == "add":
            pceen.roles.append(role)
            db.session.commit()
            return {
                "id": role.id,
                "name": role.name,
                "color": role.color or "ffffff",
                "dark": role.is_dark_colored,
            }, 201
        else:
            pceen.roles.remove(role)
            db.session.commit()
            return {}, 204
    except Exception as exc:
        db.session.rollback()
        return f"Unexpected error: {exc}", 500


@bp.route("/pceens", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.pceen)
def pceens() -> typing.RouteReturn:
    """PCéens list page."""
    form = forms.SecurityForm()
    if form.is_submitted():
        # Check request is well formed
        if form.validate():
            return add_remove_role(form.action.data, form.pceen_id.data,
                                   form.role_id.data)
        else:
            return "Bad formed request", 400

    return flask.render_template("gris/pceens.html", form=form,
                                 pceens=PCeen.query.all(),
                                 roles=Role.query.all(),
                                 title=_("Gestion des PCéens"))


@bp.route("/roles", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.role)
def roles() -> typing.RouteReturn:
    """PCéens list page."""
    form = forms.SecurityForm()
    # if form.is_submitted():
    #     # Check request is well formed
    #     if form.validate():
    #         return add_remove_role(form.action.data, form.pceen_id.data,
    #                                form.role_id.data)
    #     else:
    #         return "Bad formed request", 400

    return flask.render_template("gris/roles.html", form=form,
                                 roles=Role.query.all(),
                                 title=_("Gestion des rôles"))


@bp.route("/run_script", methods=["GET", "POST"])
@context.gris_only
def run_script() -> typing.RouteReturn:
    """Run an IntraRez script."""
    form = forms.ChoseScriptForm()
    if form.validate_on_submit():
        # Exécution du script
        _stdin = sys.stdin
        sys.stdin = io.StringIO()   # Block script for wainting for stdin
        try:
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                with contextlib.redirect_stderr(sys.stdout):
                    try:
                        utils.run_script(form.script.data)
                    except Exception:
                        output = stdout.getvalue() + traceback.format_exc()
                    else:
                        output = stdout.getvalue()
        finally:
            sys.stdin = _stdin

        output_str = str(flask.escape(output))
        output = flask.Markup(
            output_str.replace("\n", "<br/>").replace(" ", "&nbsp;")
        )
        return flask.render_template("gris/run_script.html", form=form,
                                     output=output,
                                     title=_("Exécuter un script"))
    return flask.render_template("gris/run_script.html", form=form,
                                 output=None,
                                 title=_("Exécuter un script"))
