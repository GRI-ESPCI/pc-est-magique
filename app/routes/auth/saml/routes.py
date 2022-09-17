"""PC est magique - SAML Authentication Routes"""

import flask
import flask_login
from flask_babel import _
import requests
import saml2
import saml2.client
import saml2.config
import saml2.entity
import saml2.metadata

from app.models import PCeen
from app.routes.auth import email
from app.routes.auth.saml import bp
from app.routes.auth.saml.utils import (
    reconciliate_account,
    create_new_account,
    PROMOTIONS_SERVICES,
    SAMLAttributes,
)

from app.utils import helpers, typing

_idp_metadata = typing.cast(str, None)
_saml_client = typing.cast(saml2.client.Saml2Client, None)


#: Attributes we require from the IdP (SAML identity provider).
REQUESTED_ATTRIBUTES: list[str] = [
    "givenName",
    "sn",
    "mail",
    "authorizedService",
]
#: ESPCI LDAP services the users need to have one of to sign up.
ACCEPTED_SERVICES: list[str] = list(PROMOTIONS_SERVICES)


@bp.before_app_first_request
def setup_saml_authentication() -> None:
    """Prepare objects needed to provide ESPCI SAML authentication."""
    global _idp_metadata, _saml_client
    app_config = flask.current_app.config

    # Get IdP (identity provider) metadata
    idp_response = requests.get(app_config["SAML_IDP_METADATA_URL"])
    if not idp_response and app_config["SAML_IDP_METADATA_FALLBACK_URL"]:
        idp_response = requests.get(app_config["SAML_IDP_METADATA_FALLBACK_URL"])
    if not idp_response:
        raise RuntimeError(f"Could not retrieve IdP metadata ({idp_response.status_code}): {idp_response.text}")
    _idp_metadata = idp_response.text

    # Create and configure SAML client
    scheme = app_config["PREFERRED_URL_SCHEME"]
    acs_url = flask.url_for("auth_saml.acs", _external=True, _scheme=scheme)
    metadata_url = "https://pc-est-magique.fr/saml/metadata"
    # Adresse écrite en dur dans la config de vip.espci.fr. Contactez le SI si il faut la changer.
    settings = {
        "entityid": metadata_url,
        "key_file": app_config["SAML_CERTIFICATE_PRIVATE_KEY_FILE"],
        "cert_file": app_config["SAML_CERTIFICATE_PUBLIC_KEY_FILE"],
        "encryption_keypairs": [
            {
                "key_file": app_config["SAML_CERTIFICATE_PRIVATE_KEY_FILE"],
                "cert_file": app_config["SAML_CERTIFICATE_PUBLIC_KEY_FILE"],
            }
        ],
        "generate_cert_info": True,
        "metadata": {"inline": [_idp_metadata]},
        "service": {
            "sp": {
                "endpoints": {
                    "assertion_consumer_service": [(acs_url, saml2.BINDING_HTTP_POST)],
                },
                "required_attributes": REQUESTED_ATTRIBUTES,
                "allow_unsolicited": True,
            },
        },
        "organization": {
            "name": [
                ("PC est magique (site BDE)", "fr"),
                ("PC est magique (Students site)", "en"),
            ],
            "display_name": [
                ("PC est magique (site BDE)", "fr"),
                ("PC est magique (Students site)", "en"),
            ],
            "url": "https://pc-est-magique.fr",
        },
        "contact_person": [
            {
                "given_name": "GRI Team -- BDE ESPCI Paris - PSL",
                "email_address": app_config["ADMINS"],
                "type": "technical",
            },
        ],
    }
    config = saml2.config.Config()
    config.load(settings)
    config.allow_unknown_attributes = True
    _saml_client = saml2.client.Saml2Client(config=config)


@bp.route("/metadata")
def metadata() -> typing.RouteReturn:
    """SAML public metadata of our SP (service provider), to be read by the IdP (identity provider)."""
    metadata_str = saml2.metadata.create_metadata_string(configfile=None, config=_saml_client.config)
    return metadata_str, {"Content-Type": "text/xml"}


@bp.route("/login")
def login() -> typing.RouteReturn:
    """Route starting SAML authentication request, by redirecting the user to the IdP."""
    _, info = _saml_client.prepare_for_authenticate()
    headers = dict(info["headers"])
    response = flask.redirect(headers.pop("Location"), code=302)
    response.headers.extend(headers)
    response.headers["Cache-Control"] = "no-cache, no-store"
    response.headers["Pragma"] = "no-cache"
    return response


@bp.route("/acs", methods=["POST"])
def acs() -> typing.RouteReturn:
    """Route the user is redirected to by the IdP after successful authentication."""
    if "SAMLResponse" not in flask.request.form:
        return "Missing SAMLResponse POST data", 400

    try:
        authn_response = _saml_client.parse_authn_request_response(
            flask.request.form["SAMLResponse"],
            saml2.entity.BINDING_HTTP_POST,
        )
        if authn_response is None:
            raise RuntimeError("Unhandled SAML error, please check logs")

        attributes: SAMLAttributes = authn_response.get_identity()
        for key in REQUESTED_ATTRIBUTES:
            if not attributes.get(key):
                raise ValueError(f"Missing SAML attribute: '{key}")

    except Exception as exc:
        flask.flash(
            _(
                f"L'authentification SSO a échoué (%(exc)s). Merci de réessayer ultérieurement.",
                exc=exc,
            ),
            "danger",
        )
        return helpers.ensure_safe_redirect("auth.auth_needed", next=None)

    # Authentication OK, process attributes
    for mail in attributes["mail"]:
        if pceen := PCeen.query.filter_by(email=mail).first():
            if not pceen.espci_sso_enabled:
                reconciliate_account(pceen, attributes)

            flask_login.login_user(pceen, remember=False)
            flask.flash(_("Connecté !"), "success")
            return helpers.redirect_to_next()

    # No known address, check if allowed to access
    if any(service in ACCEPTED_SERVICES for service in attributes["authorizedService"]):
        pceen = create_new_account(attributes)
        email.send_account_registered_email(pceen)
        flask_login.login_user(pceen, remember=False)
        flask.flash(_("Compte créé avec succès !"), "success")
        return helpers.redirect_to_next()

    # Not allowed
    flask.flash(
        _(
            "Le compte %(mail)s n'a pas les droits requis pour accéder à "
            "ce site. L'inscription est pour le moment réservée aux élèves.",
            mail=attributes["mail"][0],
        ),
        "warning",
    )
    return helpers.ensure_safe_redirect("auth.register", next=None)
