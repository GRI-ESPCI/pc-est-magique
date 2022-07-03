"""PC est magique - Gris Pages Routes"""

import datetime
import flask
from flask_babel import _

from dateutil import relativedelta

from app import context, db
from app import models
from app.models import Ban, PCeen, Permission, Role, PermissionScope, PermissionType
from app.utils import helpers


def add_remove_role(action: str, pceen_id: str, role_id: str) -> tuple[str | dict, int]:
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
    if not context.has_permission(
        type=PermissionType.write, scope=PermissionScope.role, elem=role
    ):
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


def add_perm(
    role_id: str, perm_id: str, type_name: str, scope_name: str, ref_id: str
) -> tuple[str | dict, int]:
    """Process a permisson add request, or return an error.

    Args:
        role_id: The ID of the role to edit permissions of (returns a 404
            if not existing).
        perm_id: The ID of the permission to add to the role (if empty,
            get it using following arguments; returns a 404 if not existing).
        type_name: The :class:`~.models.PermissionType` of the permission to
            add (ignored if ``perm_id`` is set, returns a 404 if not existing).
        scope_name: The :class:`~.models.PermissionScope` of the permission to
            add (ignored if ``perm_id`` is set, returns a 404 if not existing).
        ref_id: The ID of the object concerned by the permission, if applicable
            (ignored if ``perm_id`` is set, returns a 404 if not existing).

    Returns a 409 if the role already has / do not has the permission.

    Returns a 403 if the PCeen do not have the
    :attr:`~.models.PermissionType.write` permission for this role.

    Returns:
        If something is not good, the message and HTTP code to return.
        If the permission was successfully added, an empty dict with a 204.
    """
    # Check request refer to existing objects
    role: Role = Role.query.get(role_id)
    if not role:
        return f"Invalid role '{role_id}'", 404
    # Check rights
    if not context.has_permission(
        type=PermissionType.write, scope=PermissionScope.role, elem=role
    ):
        return "Unauthorized (you nasty cheater)", 403
    # Check request refer to existing objects
    if perm_id:
        perm: Permission = Permission.query.get(perm_id)
        if not perm:
            return f"Invalid perm '{perm_id}'", 404
    else:
        try:
            type_ = PermissionType[type_name]
        except KeyError:
            return f"Invalid permission type '{type_name}'", 404
        try:
            scope = PermissionScope[scope_name]
        except KeyError:
            return f"Invalid permission scope '{scope_name}'", 404
        if ref_id:
            if not scope.allow_elem:
                return f"Permission scope '{scope_name}' does not allow elems", 400
            if not ref_id.isdigit():
                return f"Invalid element id '{ref_id}'", 400
            ref_id = int(ref_id)
            if not scope.query(models).get(ref_id):
                return f"No element '{scope_name}' with id '{ref_id}'", 404
        else:
            if scope.need_elem:
                return f"Permission scope '{scope_name}' need an element", 400
            ref_id = None
        perm = Permission.get_or_create(scope=scope, type_=type_, ref_id=ref_id)
    # Check request is acceptable
    if role in perm.roles:
        return f"This exact permission already exists", 409
    # Proceed
    try:
        role.permissions.append(perm)
        db.session.commit()
        if not perm_id:
            flask.flash(_("Permission ajoutée"), "success")
        return {}, 201
    except Exception as exc:
        db.session.rollback()
        return f"Unexpected error: {exc}", 500


def remove_perm(role_id: str, perm_id: str) -> tuple[str | dict, int]:
    """Process a permisson remove request, or return an error.

    Args:
        role_id: The ID of the role to edit permissions of (returns a 404
            if not existing).
        perm_id: The ID of the permission to remove from role (returns a 404
            if not existing).

    Returns a 409 if the role does not has the permission.

    Returns a 403 if the PCeen do not have the
    :attr:`~.models.PermissionType.write` permission for this role.

    Returns:
        If something is not good, the message and HTTP code to return.
        If the permission was successfully removed, an empty dict with a 204.
    """
    # Check request refer to existing objects
    role: Role = Role.query.get(role_id)
    if not role:
        return f"Invalid role '{role_id}'", 404
    perm: Permission = Permission.query.get(perm_id)
    if not perm:
        return f"Invalid perm '{perm_id}'", 404
    # Check request is acceptable
    if not context.has_permission(
        type=PermissionType.write, scope=PermissionScope.role, elem=role
    ):
        return "Unauthorized (you nasty cheater)", 403
    if role not in perm.roles:
        return f"This permission does not exist", 409
    # Proceed
    try:
        role.permissions.remove(perm)
        db.session.commit()
        return {}, 204
    except Exception as exc:
        db.session.rollback()
        return f"Unexpected error: {exc}", 500


def get_perm_elements(scope_name: str) -> tuple[str | dict, int]:
    """Retrieve elements to put in select field when adding permission.

    Args:
        scope_name: The :class:`~.models.PermissionScope` of the permission
            to add (returns a 404 if not existing).

    Returns a 403 if the PCeen do not have the
    :attr:`~.models.PermissionType.read` permission for this scope.

    Returns:
        If something is not good, the message and HTTP code to return.
        If the scope has no elements, an empty list with a 200.
        If the scope has elements, a list containing dicts with ``"name"``
            (display name) and ``"value"`` informations of the permission
            with a 200.
    """
    # Check request refer to existing objects
    try:
        scope = PermissionScope[scope_name]
    except KeyError:
        return f"Invalid permission scope {scope_name}", 404
    # Check scope has objects
    if not scope.allow_elem:
        return {
            "allow_elem": False,
            "need_elem": False,
            "items": [],
        }, 200
    # Check request is acceptable
    if not context.has_permission(PermissionType.read, scope.parent or scope):
        return f"Missing authorization to read '{scope.name}' list!", 403
    # Proceed
    try:
        items = {item.id: str(item) for item in scope.query(models).all()}
        return {
            "allow_elem": scope.allow_elem,
            "need_elem": scope.need_elem,
            "items": sorted(items.items(), key=lambda kv: kv[1]),
        }, 200
    except Exception as exc:
        db.session.rollback()
        return f"Unexpected error: {exc}", 500


def compute_ban_end(
    start: datetime.datetime,
    infinite: bool,
    hours: int | None,
    days: int | None,
    months: int | None,
) -> datetime.datetime | None:
    """Compute the end datetime of the ban from form data.

    Args:
        start: The beginning of the ban.
        infinite: Whether the ban is infinite.
        hours: The number of hours of the ban, if applicable.
        days: The number of days of the ban, if applicable.
        months: The number of months of the ban, if applicable.

    Returns:
        The end of the ban, or ``None`` if infinite.
    """
    if infinite:
        return None
    else:
        return start + relativedelta.relativedelta(
            hours=int(hours or 0),
            days=int(days or 0),
            months=int(months or 0),
        )


def add_edit_ban(
    unban: str | None,
    pceen: str,
    ban_id: str | None,
    infinite: bool,
    hours: int | None,
    days: int | None,
    months: int | None,
    reason: str,
    message: str | None,
) -> None:
    """Process a ban add/update request, or return an error."""
    if ban_id:
        ban = Ban.query.get(int(ban_id))
        if unban:
            # Terminate existing ban
            ban.end = datetime.datetime.utcnow()
            helpers.log_action(f"Terminated {ban}")
            flask.flash(_("Le ban a été terminé."), "success")
        else:
            # Update existing ban
            ban.end = compute_ban_end(ban.start, infinite, hours, days, months)
            ban.reason = reason
            ban.message = message
            helpers.log_action(f"Modified {ban}: {ban.end} / {ban.reason}")
            flask.flash(_("Le ban a bien été modifié."), "success")
    else:
        # New ban
        pceen = PCeen.query.get(int(pceen))
        if pceen.is_banned:
            flask.flash(_("Ce PCéén est déjà banni !"), "danger")
        else:
            start = datetime.datetime.utcnow()
            end = compute_ban_end(start, infinite, hours, days, months)
            ban = Ban(
                pceen=pceen,
                start=start,
                end=end,
                reason=reason,
                message=message,
            )
            db.session.add(ban)
            helpers.log_action(f"Added {ban}: {ban.end} / {ban.reason}")
            flask.flash(_("Le mécréant a bien été banni."), "success")
    db.session.commit()
    helpers.run_script("gen_dhcp.py")  # Update DHCP rules
