"""PC est magique - Payments-related emails"""

import flask
import flask_babel
from flask_babel import _

from app.email import send_email
from app.models import PCeen, SubState


def send_state_change_email(pceen: PCeen, sub_state: SubState) -> None:
    """Send an email informing a PCéen of a subscription state change.

    Args:
        pceen: The PCéen in question.
        sub_state: The new PCéen subscription state.
    """
    with flask_babel.force_locale(pceen.locale or "en"):
        # Render mail content in pceen's language
        if sub_state == SubState.subscribed:
            subject = _("Paiement validé !")
            template_name = "new_subscription"
        elif sub_state == SubState.trial:
            subject = _("Paiement nécessaire")
            template_name = "subscription_expired"
        else:
            subject = _("Votre accès Internet a été coupé")
            template_name = "internet_cut"

        html_body = flask.render_template(
            f"payments/mails/{template_name}.html",
            pceen=pceen,
            sub=pceen.current_subscription,
        )

    send_email(
        f"payments/{template_name}",
        subject=f"[PC est magique] {subject}",
        recipients={pceen.email: pceen.full_name},
        html_body=html_body,
    )


def send_reminder_email(pceen: PCeen) -> None:
    """Send an email informing a PCéen its access will be cut soon.

    Args:
        pceen: The PCéen in question.
    """
    with flask_babel.force_locale(pceen.locale or "en"):
        # Render mail content in PCeen's language
        subject = _("IMPORTANT - Votre accès Internet va bientôt couper !")
        html_body = flask.render_template(
            "payments/mails/renew_reminder.html",
            pceen=pceen,
            sub=pceen.current_subscription,
        )

    send_email(
        "payments/renew_reminder",
        subject=f"[PC est magique] {subject}",
        recipients={pceen.email: pceen.full_name},
        html_body=html_body,
    )
