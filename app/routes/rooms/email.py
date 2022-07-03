"""PC est magique - Rooms-related Emails"""

import flask
import flask_babel
from flask_babel import _

from app.email import send_email
from app.models import PCeen


def send_room_transferred_email(pceen: PCeen) -> None:
    """Send an email informing a PCéen someone else took its room.

    Args:
        pceen (models.pceen): the PCéen that lost its room.
    """
    with flask_babel.force_locale(pceen.locale or "en"):
        # Render mail content in PCéen's language
        subject = _("Attention : Chambre transférée, Internet coupé")
        html_body = flask.render_template(
            "rooms/mails/room_transferred.html",
            pceen=pceen,
        )

    send_email(
        "rooms/room_transferred",
        subject=f"[PC est magique] {subject}",
        recipients={pceen.email: pceen.full_name},
        html_body=html_body,
    )
