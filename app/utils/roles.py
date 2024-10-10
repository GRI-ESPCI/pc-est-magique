"""PC est magique roles granting / revoking utilities."""

import flask
from flask_babel import _

from app.models import PCeen, Role


def grant_student_role(pceen: PCeen) -> None:
    """Add the role allowing to access students services to a PCéen.

    Args:
        pceen: The PCéen to add the role to.
    """
    student_role = Role.query.filter_by(name="Élève").one()
    if student_role not in pceen.roles:
        pceen.roles.append(student_role)
        #flask.flash(_("Accès aux modules élèves débloqué !"), "success")


def grant_promotion_role(pceen: PCeen, promotion: int) -> None:
    """Add the role corresponding to an ESPCI promotion, creating it if necessary.

    Args:
        pceen: The PCéen to add the role to.
        promotion: The promotion number.
    """
    role = Role.query.filter_by(name=str(promotion)).one_or_none()
    if not role:
        role = Role(name=str(promotion), index=promotion)
    if role not in pceen.roles:
        pceen.roles.append(role)


def grant_rezident_role(pceen: PCeen) -> None:
    """Add the role allowing to access IntraRez services to a PCéen.

    Args:
        pceen: The PCéen to add the role to.
    """
    rezident_role = Role.query.filter_by(name="Rezident").one()
    if rezident_role not in pceen.roles:
        pceen.roles.append(rezident_role)
        flask.flash(_("Accès aux modules IntraRez débloqué !"), "success")


def grant_barman_role(pceen: PCeen) -> None:
    """Add the role allowing to manage Bar to a PCéen.

    Args:
        pceen: The PCéen to add the role to.
    """
    barman_role = Role.query.filter_by(name="Barman").one()
    if barman_role not in pceen.roles:
        pceen.roles.append(barman_role)


def revoke_barman_role(pceen: PCeen) -> None:
    """Remove the role allowing to manage Bar from a PCéen.

    Args:
        pceen: The PCéen to add the role to.
    """
    barman_role = Role.query.filter_by(name="Barman").one()
    if barman_role in pceen.roles:
        pceen.roles.remove(barman_role)
