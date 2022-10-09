"""PC est magique - Bar Routes"""

import datetime

import flask
from flask_babel import _, format_currency
from sqlalchemy import extract

from app import context, db
from app.models import PCeen, BarItem, BarTransaction, PermissionScope, PermissionType
from app.routes.bar.utils import can_buy, month_year_iter
from app.utils.global_settings import Settings

sbp = flask.Blueprint("bar", __name__)


@sbp.route("/deposit/<pceen_id>", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.bar)
def post_deposit(pceen_id: str):
    """Set a user deposit state."""
    if not pceen_id.isdigit():
        flask.abort(400, "Field 'pceen_id' missing or invalid integer")
    pceen: PCeen | None = PCeen.query.get(int(pceen_id))
    if not pceen or not pceen.has_permission(PermissionType.read, PermissionScope.bar):
        flask.abort(404, f"PCeen #{pceen_id} does not exist or has no access to the Bar module")

    if pceen.bar_deposit:
        flask.abort(422, f"PCeen '{pceen.full_name}' already gave a deposit")

    pceen.bar_deposit = True
    if not pceen.bar_balance:
        pceen.bar_balance = 0
    db.session.commit()

    flask.flash(_("La caution de %(name)s a bien été acceptée", name=pceen.full_name), "success")
    return {}, 204


@sbp.route("/revert_transaction/<transaction_id>", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.bar)
def revert_transaction(transaction_id: str):
    """Revert a transaction."""
    if not transaction_id.isdigit():
        flask.abort(400, "Field 'transaction_id' missing or invalid integer")

    transaction: BarTransaction | None = BarTransaction.query.get(int(transaction_id))
    if not transaction:
        flask.abort(404, f"Transaction #{transaction} does not exist")

    # Transactions that are already reverted can't be reverted again
    if transaction.is_reverted:
        flask.abort(422, f"Transaction #{transaction} has already been reverted.")

    # Check if user balance stays positive before reverting
    client: PCeen = transaction.client
    if client.bar_balance < transaction.balance_change:
        flask.abort(
            422,
            f"{client.full_name}'s balance would be negative if this transaction were reverted.",
        )

    transaction.revert(reverter=context.g.pceen)
    db.session.commit()

    flask.flash(_("La transaction #%(transaction_id)s a bien été annulée.", transaction_id=transaction.id), "primary")
    return {}, 204


@sbp.route("/quick_access_item/<item_id>", methods=["PATCH"])
@context.permission_only(PermissionType.write, PermissionScope.bar)
def set_quick_access_item(item_id: str):
    """Set the quick access item."""
    if not item_id.isdigit():
        flask.abort(400, "Field 'item_id' missing or invalid integer")
    item: BarItem | None = BarItem.query.get(int(item_id))
    if not item:
        flask.abort(404, f"Item #{item_id} does not exist")

    Settings.quick_access_item = item
    db.session.commit()

    flask.flash(_("Article %(item)s supprimé.", item=item.name), "success")
    return {}, 201


@sbp.route("/item/<item_id>", methods=["DELETE"])
@context.permission_only(PermissionType.write, PermissionScope.bar)
def delete_item(item_id: str):
    """Delete an item from the inventory."""
    if not item_id.isdigit():
        flask.abort(400, "Field 'item_id' missing or invalid integer")
    item: BarItem | None = BarItem.query.get(int(item_id))
    if not item:
        flask.abort(404, f"Item #{item_id} does not exist")

    item.archived = True
    db.session.commit()

    flask.flash(_("Article %(item)s supprimé.", item=item.name), "success")
    return {}, 201


@sbp.route("/top_up/<pceen_id>", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.bar)
def top_up(pceen_id: str):
    """Top up the user's balance"""
    if not pceen_id.isdigit():
        flask.abort(400, "Field 'pceen_id' missing or invalid integer")
    pceen: PCeen | None = PCeen.query.get(pceen_id)
    if not pceen or not pceen.has_permission(PermissionType.read, PermissionScope.bar):
        flask.abort(404, f"PCeen #{pceen_id} does not exist or has no access to the Bar module")

    try:
        amount = flask.request.form.get("amount", type=float)
        if amount <= 0:
            raise ValueError
    except ValueError:
        flask.abort(400, "Field 'amount' missing, invalid float or <= 0")

    transaction = BarTransaction.create_from_top_up(
        client=pceen, barman=context.g.pceen, amount=amount, date=datetime.datetime.utcnow()
    )
    db.session.add(transaction)
    db.session.commit()

    flask.flash(
        _("%(amount)s ajoutés au solde de %(name)s", amount=format_currency(amount, "EUR"), name=pceen.full_name),
        "success",
    )
    return {}, 204


@sbp.route("/pay/<pceen_id>/<item_id>", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.bar)
def pay(pceen_id: str, item_id: str):
    """Substract the item price to the user's balance."""
    if not pceen_id.isdigit():
        flask.abort(400, "Field 'pceen_id' missing or invalid integer")
    if not item_id.isdigit():
        flask.abort(400, "Field 'item_id' missing or invalid integer")

    pceen: PCeen | None = PCeen.query.get(pceen_id)
    if not pceen or not pceen.has_permission(PermissionType.read, PermissionScope.bar):
        flask.abort(404, f"PCeen #{pceen_id} does not exist or has no access to the Bar module")

    item: BarItem | None = BarItem.query.get(int(item_id))
    if not item:
        flask.abort(404, f"Item #{item} does not exist")

    if not can_buy(pceen, item, flash=True):
        flask.abort(422, "Cannot buy item")

    transaction = BarTransaction.create_from_item_bought(
        client=pceen, barman=context.g.pceen, item=item, date=datetime.datetime.utcnow()
    )
    db.session.add(transaction)
    db.session.commit()

    flask.flash(
        _("Achat validé : %(item)s (%(amount)s). Annuler :", item=item.name, amount=format_currency(item.price, "EUR"))
        + flask.Markup(flask.render_template("bar/_revert_button.html", transaction=transaction)),
        "success",
    )
    return {}, 204
