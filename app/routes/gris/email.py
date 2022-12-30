"""PC est magique - Admin-related emails"""

import flask
import flask_babel
from flask_babel import _

from app.email import send_email
from app.models import PCeen


def send_role_switch_email(pceen: PCeen) -> None:
    """Send an email informing a PCéen its student role has been replaced by Alumni role.

    Args:
        pceen: The PCéen in question.
    """
    with flask_babel.force_locale(pceen.locale or "en"):
        # Render mail content in PCeen's language
        subject = _("Perte de l'accès Élève... contre l'accès Alumni !")
        html_body = flask.render_template(
            "gris/mails/role_switch.html",
            pceen=pceen,
            sub=pceen.current_subscription,
        )

    send_email(
        "gris/role_switch",
        subject=f"[PC est magique] {subject}",
        recipients={pceen.email: pceen.full_name},
        html_body=html_body,
    )
