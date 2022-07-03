"""PC est magique - Gris Pages Routes"""

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
    add_edit_ban,
)
from app.utils import helpers, typing


@bp.route("/pceens", methods=["GET", "POST"])
@context.gris_only
def pceens() -> typing.RouteReturn:
    """PCéens list page."""
    roles_form = forms.AddRemoveRoleForm()
    ban_form = forms.BanForm()

    if roles_form.is_submitted():
        # Check request is well formed
        if roles_form.validate():
            return add_remove_role(
                roles_form.action.data,
                roles_form.pceen_id.data,
                roles_form.role_id.data,
            )
        else:
            return {"message": "Bad formed request", "detail": roles_form.errors}, 400

    if ban_form.validate_on_submit():
        add_edit_ban(
            unban=ban_form.unban.data,
            pceen=ban_form.pceen.data,
            ban_id=ban_form.ban_id.data,
            infinite=ban_form.infinite.data,
            hours=ban_form.hours.data,
            days=ban_form.days.data,
            months=ban_form.months.data,
            reason=ban_form.reason.data,
            message=ban_form.message.data,
        )

    return flask.render_template(
        "gris/pceens.html",
        roles_form=roles_form,
        ban_form=ban_form,
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
    """Run a PC est magique script."""
    form = forms.ChoseScriptForm()
    if form.validate_on_submit():
        script = form.script.data
        helpers.log_action(f"Executing script from GRI menu: {script}")
        # Exécution du script
        _stdin = sys.stdin
        sys.stdin = io.StringIO()  # Block script for wainting for stdin
        try:
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                with contextlib.redirect_stderr(sys.stdout):
                    try:
                        helpers.run_script(script)
                    except Exception as exc:
                        helpers.log_action(f" -> ERROR: {exc}", warning=True)
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


@bp.route("/monitoring_ds")
@context.gris_only
def monitoring_ds() -> typing.RouteReturn:
    """Integration of Darkstat network monitoring."""
    return flask.render_template(
        "gris/monitoring_ds.html", title=_("Darkstat network monitoring")
    )


@bp.route("/monitoring_bw")
@context.gris_only
def monitoring_bw() -> typing.RouteReturn:
    """Integration of Bandwidthd network monitoring."""
    return flask.render_template(
        "gris/monitoring_bw.html", title=_("Bandwidthd network monitoring")
    )
