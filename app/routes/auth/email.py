"""PC est magique - Authentication-related Emails"""

import flask
import flask_babel
from flask_babel import _

from app.email import send_email
from app.models import PCeen


def send_account_registered_email(pceen: PCeen) -> None:
    """Send an email confirming account registration.

    Args:
        pceen: The pceen that just registered.
    """
    subject = _("Compte créé avec succès !")
    html_body = flask.render_template(
        "auth/mails/account_registered.html",
        pceen=pceen,
    )
    send_email(
        "auth/account_registered",
        subject=f"[PC est magique] {subject}",
        recipients={pceen.email: pceen.full_name},
        html_body=html_body,
    )


def send_password_reset_email(pceen: PCeen) -> None:
    """Send a password reset email.

    Args:
        pceen: The pceen to reset password of.
    """
    with flask_babel.force_locale(pceen.locale or "fr"):
        # Render mail content in pceen's language (if doas, ...)
        subject = _("Réinitialisation du mot de passe")
        html_body = flask.render_template(
            "auth/mails/reset_password.html",
            pceen=pceen,
            token=pceen.get_reset_password_token(),
        )

    send_email(
        "auth/reset_password",
        subject=f"[PC est magique] {subject}",
        recipients={pceen.email: pceen.full_name},
        html_body=html_body,
    )
