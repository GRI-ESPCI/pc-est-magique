"""PC est magique - SAML Authentication Utils"""

import datetime
import typing

import flask
from flask_babel import _

from app import db
from app.models import PCeen
from app.routes.auth.utils import new_username
from app.utils import helpers
from app.utils.roles import grant_student_role, grant_promotion_role


#: Promotion that is entered / will enter to ESPCI the current year.
ENTER_THIS_YEAR_PROMO: int = datetime.date.today().year - 1882 + 1
#: Mapping of ESPCI LDAP services names to promotions currently in school.
PROMOTIONS_SERVICES: dict[str, int] = {
    f"promo{promo}": promo for promo in range(ENTER_THIS_YEAR_PROMO - 4, ENTER_THIS_YEAR_PROMO + 1)
}


class SAMLAttributes(typing.TypedDict):
    """Attributes dict provided by the IdP when authentication succeeded."""

    givenName: list[str]
    sn: list[str]
    mail: list[str]
    authorizedService: list[str]


def process_attributes(attributes: SAMLAttributes) -> tuple[str, str, str, int | None]:
    """Extract authenticated user information from SAML attributes.

    Args:
        attributes: SAML attributes provided by the IdP.

    Returns:
        The first name, last name, email address and promotion of the authenticated user.
    """
    prenom = attributes["givenName"][0].title()
    nom = attributes["sn"][0].title()
    email = next(
        (mail for mail in attributes["mail"] if mail.endswith("psl.eu")),
        attributes["mail"][0],
    )
    promos = [
        PROMOTIONS_SERVICES[service] for service in attributes["authorizedService"] if service in PROMOTIONS_SERVICES
    ]
    promo = max(promos) if promos else None
    return prenom, nom, email, promo


def reconciliate_account(pceen: PCeen, attributes: SAMLAttributes) -> None:
    """Updates an existing PCéen account with SAML authentication info.

    Turns on "SSO enabled" flag, and add "Student" role if appropriate.

    Args:
        pceen: The PCéen matching the authenticated user.
        attributes: SAML attributes of the authenticated user.
    """
    prenom, nom, _email, promo = process_attributes(attributes)
    pceen.prenom = prenom
    pceen.nom = nom
    pceen.promo = promo
    flask.flash(
        _(
            "Compte mis à jour depuis les infos ESPCI (prénom : %(prenom)s, nom : %(nom)s, promotion : %(promo)s)",
            prenom=prenom,
            nom=nom,
            promo=promo,
        ),
        "info",
    )
    if promo:
        grant_student_role(pceen)
        grant_promotion_role(pceen, promo)
    pceen.espci_sso_enabled = True
    pceen.activated = True
    db.session.commit()
    helpers.log_action(
        f"ESPCI SSO -> Matched account {pceen!r} with ESPCI account, updated it ({pceen.prenom} {pceen.nom} "
        f"{pceen.promo}, {pceen.email})"
    )


def create_new_account(attributes: SAMLAttributes) -> PCeen:
    """Creates a new PCéen account from SAML authentication info.

    Add "Student" role if appropriate.

    Args:
        attributes: SAML attributes of the authenticated user.
    """
    prenom, nom, email, promo = process_attributes(attributes)
    pceen = PCeen(
        username=new_username(prenom, nom),
        nom=nom,
        prenom=prenom,
        promo=promo,
        email=email,
        espci_sso_enabled=True,
    )
    if promo:
        grant_student_role(pceen)
        grant_promotion_role(pceen, promo)
    db.session.add(pceen)
    db.session.commit()
    helpers.log_action(
        f"ESPCI SSO -> Registered account {pceen!r} ({pceen.prenom} {pceen.nom} {pceen.promo}, {pceen.email})"
    )
    return pceen
