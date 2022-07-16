"""PC est magique - Authentication Utils"""

import re

import flask
from flask_babel import _
import unidecode

from app.models import PCeen, Role


def new_username(prenom: str, nom: str) -> str:
    """Create a new pceen unique username from its names.

    Args:
        prenom: The pceen's first name.
        nom: The pceen's last name.

    Returns:
        The first non-existing corresponding username.
    """
    pnom = prenom.lower()[0] + nom.lower()[:7]
    # Exclude non-alphanumerics characters
    base_username = re.sub(r"\W", "", unidecode.unidecode(pnom), re.A)
    # Construct first non-existing username
    username = base_username
    discr = 1
    while PCeen.query.filter_by(username=username).first():
        username = f"{base_username}{discr}"
        discr += 1
    return username


def grant_student_role(pceen: PCeen) -> None:
    """Add the role allowing to access students services to a PCéen.

    Args:
        pceen: The PCéen to add the role to.
    """
    student_role = Role.query.filter_by(name="Élève").one()
    if student_role not in pceen.roles:
        pceen.roles.append(student_role)
        flask.flash(_("Accès aux modules élèves débloqué !"), "success")


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
