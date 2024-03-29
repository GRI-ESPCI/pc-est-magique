"""PC est magique - Payments-related Pages Routes"""

import datetime

import flask
from flask_babel import _

from app import context, db
from app.enums import PaymentStatus, SubState
from app.models import Offer, Payment, PermissionScope, PermissionType
from app.routes.payments import bp, forms
from app.routes.payments.utils import add_subscription
from app.utils import helpers, lydia, typing


@bp.before_app_first_request
def create_first_offer() -> None:
    """Create subscription welcome order if not already present."""
    if not Offer.query.first():
        offer = Offer.create_first_offer()
        db.session.add(offer)
        db.session.commit()
        helpers.log_action(f"Created first offer ({offer!r})")


@bp.route("")
@bp.route("/")
@context.intrarez_setup_only
@context.permission_only(PermissionType.read, PermissionScope.intrarez)
def main() -> typing.RouteReturn:
    """Subscriptions informations page."""
    subscriptions = sorted(context.g.pceen.subscriptions, key=lambda sub: sub.start, reverse=True)
    return flask.render_template(
        "payments/main.html",
        title=_("Mon abonnement Internet"),
        subscriptions=subscriptions,
    )


@bp.route("/pay")
@context.intrarez_setup_only
@context.permission_only(PermissionType.read, PermissionScope.intrarez)
def pay() -> typing.RouteReturn:
    """Payment page."""
    if context.g.pceen.sub_state == SubState.subscribed:
        flask.flash(_("Vous avez déjà un abonnement en cours !"), "warning")
        return helpers.redirect_to_next()

    offers = Offer.query.filter_by(visible=True).order_by(Offer.price).all()
    return flask.render_template("payments/pay.html", title=_("Paiement"), offers=offers)


@bp.route("/pay/<method>", methods=["GET", "POST"])
@bp.route("/pay/<method>/", methods=["GET", "POST"])
@bp.route("/pay/<method>/<offer>", methods=["GET", "POST"])
@context.intrarez_setup_only
@context.permission_only(PermissionType.read, PermissionScope.intrarez)
def pay_(method: str, offer: str | None = None) -> typing.RouteReturn:
    """Payment page."""
    if context.g.pceen.sub_state == SubState.subscribed:
        flask.flash(_("Vous avez déjà un abonnement en cours !"), "warning")
        return helpers.redirect_to_next()

    methods = {
        "lydia": _("Payer avec Lydia"),
        "transfer": _("Payer par virement"),
        "cash": _("Payer en main propre"),
        "magic": _("Ajouter un paiement"),
    }
    if method in methods:
        offer = Offer.query.get(offer)
        if offer and offer.visible and offer.active:
            if method == "magic" and not context.g.doas:
                flask.abort(403)
            if method == "lydia":
                form = forms.LydiaPaymentForm()
                if form.validate_on_submit():
                    if form.phone.data:
                        phone = form.phone.data.replace("+33", "0").replace(" ", "")
                    else:
                        phone = None
                    lydia_url = lydia.get_payment_url(context.g.pceen, offer, phone)
                    return flask.redirect(lydia_url)
            else:
                form = None
            return flask.render_template(
                f"payments/pay_{method}.html",
                title=methods[method],
                offer=offer,
                form=form,
            )

    # Bad arguments
    return helpers.ensure_safe_redirect("payments.pay", next=None)


@bp.route("/add_payment/<offer>")
@context.intrarez_setup_only
@context.permission_only(PermissionType.read, PermissionScope.intrarez)
def add_payment(offer: str = None) -> typing.RouteReturn:
    """Add an arbitrary payment by a GRI."""
    if not context.g.doas:
        flask.abort(403)

    pceen = context.g.pceen
    if pceen.sub_state == SubState.subscribed:
        flask.flash(_("Vous avez déjà un abonnement en cours !"), "warning")
        return helpers.redirect_to_next()

    offer = Offer.query.get(offer)
    if not (offer and offer.visible and offer.active):
        flask.flash("Offre incorrecte", "danger")
        return helpers.redirect_to_next()

    offer = typing.cast(Offer, offer)  # type check only

    # Add payment
    payment = Payment(
        pceen=pceen,
        amount=offer.price,
        created=datetime.datetime.now(),
        payed=datetime.datetime.now(),
        status=PaymentStatus.manual,
        gri=context.g.logged_in_user,
    )
    db.session.add(payment)

    # Add subscription
    subscription = add_subscription(pceen, offer, payment)
    helpers.log_action(f"Added {subscription!r} to {offer!r}, with {payment!r} added by GRI")

    flask.flash("Paiement et abonnement enregistrés !", "success")
    flask.flash("Mail d'information envoyé !", "success")
    return helpers.redirect_to_next()


@bp.route("/lydia_callback/confirm", methods=["POST"])
def lydia_callback_confirm() -> typing.RouteReturn:
    """Route called by Lydia server on payment success.

    See https://homologation.lydia-app.com/doc/api/#api-Request-Do.
    """
    try:
        currency = flask.request.form["currency"]
        request_id = flask.request.form["request_id"]
        amount = flask.request.form["amount"]
        signed = flask.request.form["signed"]
        transaction_identifier = flask.request.form["transaction_identifier"]
        vendor_token = flask.request.form["vendor_token"]
        order_ref = flask.request.form["order_ref"]
        sig = flask.request.form["sig"]
    except LookupError as exc:
        return "Wrong parameters", 400

    if not lydia.check_signature(
        sig,
        currency=currency,
        request_id=request_id,
        amount=amount,
        signed=signed,
        transaction_identifier=transaction_identifier,
        vendor_token=vendor_token,
        order_ref=order_ref,
    ):
        return "Invalid signature", 403

    if not order_ref.isdigit():
        return "order_ref invalid", 400

    # Retrieve payment
    payment = Payment.query.get(int(order_ref))
    if not payment:
        return f"Payment not existing: {order_ref}", 404
    if payment.status != PaymentStatus.waiting:
        return f"Bad payment state: {payment.status.name}", 400
    if payment.amount != float(amount):
        return f"Bad amount {amount}: expected {payment.amount}", 400

    payment.status = PaymentStatus.accepted
    payment.payed = datetime.datetime.now()
    payment.lydia_transaction_id = transaction_identifier
    pceen = payment.pceen
    offer = Offer.query.filter_by(price=payment.amount).one_or_none()
    if not offer:
        return f"No offer for price {payment.amount}", 404

    subscription = add_subscription(pceen, offer, payment)
    helpers.log_action(f"Added {subscription!r} to {offer!r}, with {payment!r} via Lydia CONFIRM")
    return "", 204


@bp.route("/lydia_callback/cancel", methods=["POST"])
def lydia_callback_cancel() -> typing.RouteReturn:
    """Route called by Lydia server on payment cancel / expiration.

    See https://homologation.lydia-app.com/doc/api/#api-Request-Do.
    """
    try:
        currency = flask.request.form["currency"]
        request_id = flask.request.form["request_id"]
        amount = flask.request.form["amount"]
        signed = flask.request.form["signed"]
        vendor_token = flask.request.form["vendor_token"]
        order_ref = flask.request.form["order_ref"]
        sig = flask.request.form["sig"]
    except LookupError as exc:
        return "Wrong parameters", 400

    if not lydia.check_signature(
        sig,
        currency=currency,
        request_id=request_id,
        amount=amount,
        signed=signed,
        vendor_token=vendor_token,
        order_ref=order_ref,
    ):
        return "Invalid signature", 403

    if not order_ref.isdigit():
        return "order_ref invalid", 400

    # Retrieve payment
    payment = Payment.query.get(int(order_ref))
    if not payment:
        return f"Payment not existing: {order_ref}", 404
    if payment.status != PaymentStatus.waiting:
        return f"Bad payment state: {payment.status.name}", 400
    if payment.amount != float(amount):
        return f"Bad amount {amount}: expected {payment.amount}", 400

    payment.status = PaymentStatus.refused
    db.session.commit()
    return "", 204


@bp.route("/lydia/success")
@context.intrarez_setup_only
@context.permission_only(PermissionType.read, PermissionScope.intrarez)
def lydia_success() -> typing.RouteReturn:
    """Route the user is sent back by Lydia after paying."""
    if context.g.pceen.sub_state == SubState.subscribed:
        flask.flash(_("Paiement validé !"), "success")
        return helpers.redirect_to_next(next=None)

    try:
        payment = next(payment for payment in context.g.pceen.payments if payment.status == PaymentStatus.waiting)
    except StopIteration:
        flask.flash(_("Pas de paiement détecté"), "warning")
        return helpers.redirect_to_next(next=None)
    else:
        lydia.update_payment(payment)
        transaction = flask.request.args.get("transaction", "<unknown>")
        return helpers.ensure_safe_redirect(
            "payments.lydia_validate",
            payment_id=payment.id,
            transaction=transaction,
            next=None,
        )


@bp.route("/lydia/fail")
@context.intrarez_setup_only
@context.permission_only(PermissionType.read, PermissionScope.intrarez)
def lydia_fail() -> typing.RouteReturn:
    """Route the user is sent back by Lydia after cancelling payment."""
    flask.flash(_("Paiement annulé"), "danger")
    return helpers.ensure_safe_redirect("payments.pay", next=None)


@bp.route("/lydia/validate/<payment_id>")
@context.intrarez_setup_only
@context.permission_only(PermissionType.read, PermissionScope.intrarez)
def lydia_validate(payment_id: int) -> typing.RouteReturn:
    """Route to register a payment done but not validated (callback error)."""
    if not payment_id.isdigit():
        flask.flash(_("Numéro de paiement invalide"), "warning")
        return helpers.ensure_safe_redirect("payments.pay", next=None)

    # Retrieve payment
    payment = Payment.query.get(int(payment_id))
    if not payment:
        flask.flash(_("Numéro de paiement invalide"), "warning")
        return helpers.ensure_safe_redirect("payments.pay", next=None)
    if payment.status == PaymentStatus.waiting:
        flask.flash(_("Paiement en attente, réessayer"), "warning")
        return helpers.ensure_safe_redirect("payments.pay", next=None)
    elif payment.status != PaymentStatus.accepted:
        flask.flash(_("Paiement invalide, réessayer"), "warning")
        return helpers.ensure_safe_redirect("payments.pay", next=None)

    payment.payed = datetime.datetime.now()
    payment.lydia_transaction_id = flask.request.args.get("transaction")
    db.session.commit()

    offer = Offer.query.filter_by(price=payment.amount).one_or_none()
    if not offer:
        return f"No offer for price {payment.amount}", 404

    subscription = add_subscription(payment.pceen, offer, payment)
    helpers.log_action(f"Added {subscription!r} to {offer!r}, with {payment!r} via Lydia VALIDATE")
    flask.flash(_("Paiement validé !"), "success")
    return helpers.redirect_to_next()
