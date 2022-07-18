"""PC est magique - Payments-related Pages Utils"""

import datetime

from app import db
from app.enums import SubState
from app.models import Offer, Payment, PCeen, Subscription
from app.routes.payments import email
from app.utils import helpers


def add_subscription(pceen: PCeen, offer: Offer, payment: Payment) -> Subscription:
    """Add a new subscription to a PCéen.

    Update sub state and send informative email.
    Remove user's current ban if necessary.

    Args:
        pceen: The PCéen to add a subscription to.
        offer: The offer just subscripted to.
        payment: The payment made by the PCéen to subscribe to the Offer.

    Returns:
        The subscription created.
    """
    # Determine new subscription dates
    start = pceen.current_subscription.renew_day
    end = start + offer.delay

    # Add new subscription
    subscription = Subscription(
        pceen=pceen,
        offer=offer,
        payment=payment,
        start=start,
        end=end,
    )
    db.session.add(subscription)

    pceen.sub_state = pceen.compute_sub_state()
    db.session.commit()

    if pceen.sub_state != SubState.subscribed:
        raise RuntimeError(
            f"payments.add_payment : Paiement {payment} ajouté, création "
            f"de l'abonnement {subscription}, mais le PCéen {pceen} "
            f"a toujours l'état {pceen.sub_state}..."
        )

    # Remove ban and update DHCP
    if pceen.is_banned:
        helpers.log_action(f"{pceen!r} subscribed, terminated {pceen.current_ban!r}")
        pceen.current_ban.end = datetime.datetime.utcnow()
        db.session.commit()
        helpers.run_script("gen_dhcp.py")  # Update DHCP rules

    # Send mail
    email.send_state_change_email(pceen, pceen.sub_state)
    return subscription
