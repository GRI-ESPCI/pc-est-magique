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
