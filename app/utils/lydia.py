"""PC est magique - Lydia Integration"""

import datetime
import hashlib

import flask
from flask_babel import _
import requests

from app import db
from app.enums import PaymentStatus, PaymentType
from app.models import PCeen, Payment, Offer


def get_payment_url(pceen: PCeen, offer: Offer, phone: str | None) -> str:
    """Get URL to send the pceen to to make him pay for an offer.

    If a payment request is already waiting, it returns its URL, else
    it creates a new request and returns its URL.

    Args:
        pceen: The pceen that want to pay.
        offer, phone: Passed to :func:`.create_payment`.

    Returns:
        The Lydia pay page URL.
    """
    try:
        payment = next(
            payment
            for payment in pceen.payments
            if (payment.status == PaymentStatus.waiting and payment.amount == offer.price and payment.type == PaymentType.internet)
        )
    except StopIteration:
        # No payment waiting, create one
        return create_internet_payment(pceen, offer, phone)
    else:
        # Payment waiting, check still open
        update_payment(payment)
        if payment.status == PaymentStatus.waiting:
            # Still open: return pay URL
            return build_payment_url(payment.lydia_uuid)
        elif payment.status == PaymentStatus.accepted:
            # Payment made (but callback not called?): validate it
            return flask.url_for("payments.lydia_validate", payment_id=payment.id)
        else:
            # Payment closed, cancelled...: create a new one
            return create_internet_payment(pceen, offer, phone)


def create_internet_payment(pceen: PCeen, offer: Offer, phone: str | None) -> str:
    """Creates a new Lydia payment request for an Internet offer."""
    payment = Payment(
        pceen=pceen,
        amount=offer.price,
        created=datetime.datetime.now(),
        type=PaymentType.internet,
    )
    db.session.add(payment)
    db.session.commit()

    return create_payment(
        payment,
        message=_("Offre Internet à la Rez :") + f" {offer.name}",
        phone=phone,
        confirm_url=flask.url_for("payments.lydia_callback_confirm", _external=True),
        cancel_url=flask.url_for("payments.lydia_callback_cancel", _external=True),
        success_url=flask.url_for("payments.lydia_success", _external=True),
        fail_url=flask.url_for("payments.lydia_fail", _external=True),
    )


def create_payment(
    payment: Payment,
    message: str,
    phone: str | None = None,
    confirm_url: str | None = None,
    cancel_url: str | None = None,
    success_url: str | None = None,
    fail_url: str | None = None,
) -> str:
    """Creates a new Lydia payment request.

    Args:
        payment: The payment model instance.
        message: The message to display on the Lydia payment page.
        phone: The phone number used to send the Lydia request. If
            omitted, or if not associated with a Lydia account, it
            will send the user to a CB pay page.
        confirm_url, cancel_url, success_url, fail_url: Overrides for
            Lydia callback/redirect URLs.

    Returns:
        The Lydia pay page URL.
    """
    vendor_token = (
        flask.current_app.config["LYDIA_BAR_VENDOR_TOKEN"]
        if payment.type == PaymentType.bar
        else flask.current_app.config["LYDIA_VENDOR_TOKEN"]
    )
    if not vendor_token:
        raise RuntimeError(f"Lydia token missing for payment type {payment.type.name}")

    data = {
        "vendor_token": vendor_token,
        "amount": format(float(payment.amount), ".2f"),
        "currency": "EUR",
        "recipient": (phone or payment.pceen.email or f"{payment.pceen.username}@no-email.org"),
        "type": "phone" if phone else "email",
        "message": message,
        "order_ref": f"PEM-{payment.id}-{int(payment.created.timestamp())}",
        "notify_collector": "no",
        "display_confirmation": "no",
        "confirm_url": confirm_url or flask.url_for("payments.lydia_callback_confirm", _external=True),
        "cancel_url": cancel_url or flask.url_for("payments.lydia_callback_cancel", _external=True),
        "expire_url": cancel_url or flask.url_for("payments.lydia_callback_cancel", _external=True),
        "end_mobile_url": success_url or flask.url_for("payments.lydia_success", _external=True),
        "browser_success_url": success_url or flask.url_for("payments.lydia_success", _external=True),
        "browser_fail_url": fail_url or flask.url_for("payments.lydia_fail", _external=True),
        "payment_method": "lydia" if phone else "cb",
    }
    rep = requests.post(flask.current_app.config["LYDIA_BASE_URL"] + "/api/request/do.json", data=data)

    if rep and rep.json().get("error") == "0":
        # Payment request created
        payment.status = PaymentStatus.waiting
        payment.lydia_uuid = rep.json()["request_uuid"]
        db.session.commit()
        return build_payment_url(payment.lydia_uuid, method="lydia" if phone else "cb")
    else:
        raise RuntimeError(f"Lydia Request Do Failed: {rep.request.body} >>> {rep.text}")


def update_payment(payment: Payment) -> None:
    """Check the state of a Lydia payment request.

    Updates the associated PC est magique payment if the status changed.

    Checks the returned signature to check that it matches our private key
    and so that the payment is real.

    Args:
        payment: The payment to update status of. ``lydia_uuid`` must be set.
    """
    vendor_token = (
        flask.current_app.config["LYDIA_BAR_VENDOR_TOKEN"]
        if payment.type == PaymentType.bar
        else flask.current_app.config["LYDIA_VENDOR_TOKEN"]
    )
    if not vendor_token:
        raise RuntimeError(f"Lydia token missing for payment type {payment.type.name}")

    rep = requests.post(
        flask.current_app.config["LYDIA_BASE_URL"] + "/api/request/state.json",
        data={
            "request_uuid": payment.lydia_uuid,
            "vendor_token": vendor_token,
        },
    )
    if not rep or "error" in rep.json():
        raise RuntimeError(f"Lydia Request Check Failed: {rep.request.body} >>> {rep.text}")

    if not check_signature(
        rep.json().get("signature"),
        payment_type=payment.type,
        amount=format(float(payment.amount), ".2f"),
        request_uuid=payment.lydia_uuid,
    ):
        flask.flash(_("Signature invalide, impossible de valider le paiement"), "danger")
        return

    state = rep.json().get("state")
    new_status = {
        "0": PaymentStatus.waiting,
        "1": PaymentStatus.accepted,
        "5": PaymentStatus.refused,
        "6": PaymentStatus.cancelled,
    }.get(state, PaymentStatus.error)

    if new_status == PaymentStatus.accepted and payment.status != PaymentStatus.accepted:
        payment.payed = datetime.datetime.now()
        payment.lydia_transaction_id = rep.json().get("transaction_identifier")

    payment.status = new_status
    db.session.commit()


def build_payment_url(request_uuid: str, method: str = "auto") -> str:
    """Build Lydia payment URL from request UUID.

    Args:
        request_uuid: The UUID of the payment request.
        method: The method to use. One of ``lydia``, ``cb`` or
            ``auto`` (default). See
            https://homologation.lydia-app.com/doc/api/#api-Request-Do.

    Returns:
        The Lydia pay page URL.
    """
    base_url = flask.current_app.config["LYDIA_BASE_URL"]
    return f"{base_url}/collect/payment/{request_uuid}/{method}"


def check_signature(sig: str, payment_type: PaymentType = PaymentType.internet, **params: str) -> bool:
    """Check whether the signature passed by a Lydia call is correct.

    See https://homologation.lydia-app.com/doc/api/#signature.

    Args:
        sig: The signature to compare to (md5 hexdigest).
        payment_type: The type of payment (to use the correct private token).
        **params: The parameters in the signature (in any order).

    Returns:
        Whether the signature validates with the params and private token.
    """
    private_token = (
        flask.current_app.config["LYDIA_BAR_PRIVATE_TOKEN"]
        if payment_type == PaymentType.bar
        else flask.current_app.config["LYDIA_PRIVATE_TOKEN"]
    )
    sorted_params = sorted(params.items(), key=lambda kv: kv[0])
    query = "&".join(f"{key}={val}" for key, val in sorted_params)
    raw_sig = query + "&" + private_token
    return hashlib.md5(raw_sig.encode()).hexdigest() == sig
