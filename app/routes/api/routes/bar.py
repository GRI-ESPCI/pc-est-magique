"""PC est magique - Bar Routes"""

import datetime

import flask
from flask_babel import _, format_currency
from sqlalchemy import extract

from app import context, db
from app.enums import BarTransactionType
from app.models import PCeen, BarItem, BarTransaction, GlobalSetting, PermissionScope, PermissionType
from app.routes.bar.utils import can_buy, month_year_iter, BarSettings
from app.utils import helpers, typing

sbp = flask.Blueprint("bar", __name__)


@sbp.route("/yearly_transactions")
@context.permission_only(PermissionType.read, PermissionScope.bar_stats)
def get_yearly_transactions():
    """Return transaction from last 12 months."""
    # Get current day, month, year
    today = datetime.datetime.today()
    current_year = today.year
    current_month = today.month

    # Get last 12 months range
    if current_month == 12:
        previous_year = current_year
    else:
        previous_year = current_year - 1
    previous_month = (current_month - 12) % 12

    # Get money spent and topped up last 12 months
    paid_per_month = []
    topped_per_month = []
    for (y, m) in month_year_iter(previous_month + 1, previous_year, current_month + 1, current_year):
        transactions_paid_y = BarTransaction.query.filter(
            extract("month", BarTransaction.date) == m,
            extract("year", BarTransaction.date) == y,
            BarTransaction.type.like("Pay%"),
            BarTransaction.is_reverted == False,
        ).all()
        transactions_topped_y = BarTransaction.query.filter(
            extract("month", BarTransaction.date) == m,
            extract("year", BarTransaction.date) == y,
            BarTransaction.type.like("Top up"),
            BarTransaction.is_reverted == False,
        ).all()
        paid_per_month.append(0)
        for t in transactions_paid_y:
            paid_per_month[-1] -= t.balance_change
        topped_per_month.append(0)
        for t in transactions_topped_y:
            topped_per_month[-1] += t.balance_change

    # Generate months labels
    months_labels = [
        "%.2d" % m[1] + "/" + str(m[0])
        for m in list(month_year_iter(previous_month + 1, previous_year, current_month + 1, current_year))
    ]

    return flask.jsonify(
        {"paid_per_month": paid_per_month, "topped_per_month": topped_per_month, "months_labels": months_labels}
    )


@sbp.route("/daily_statistics")
@context.permission_only(PermissionType.read, PermissionScope.bar_stats)
def get_daily_statistics():
    """Return daily statistics."""
    # Get current day start
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=1)
    if today.hour < 6:
        current_day_start = datetime.datetime(year=yesterday.year, month=yesterday.month, day=yesterday.day, hour=6)
    else:
        current_day_start = datetime.datetime(year=today.year, month=today.month, day=today.day, hour=6)

    # Daily clients
    nb_daily_clients = PCeen.query.filter(
        PCeen.bar_transactions_made.any(BarTransaction.date > current_day_start)
    ).count()

    # Daily alcohol consumption
    alcohol_qty = (
        BarTransaction.query.filter(BarTransaction.date > current_day_start)
        .filter(BarTransaction.type.like("Pay%"))
        .filter(BarTransaction.item.has(is_alcohol=True))
        .filter_by(is_reverted=False)
        .count()
        * 0.25
    )

    # Daily revenue
    daily_transactions = (
        BarTransaction.query.filter(BarTransaction.date > current_day_start)
        .filter(BarTransaction.type.like("Pay%"))
        .filter_by(is_reverted=False)
        .all()
    )
    daily_revenue = sum([abs(t.balance_change) for t in daily_transactions])

    return flask.jsonify(
        {"nb_daily_clients": nb_daily_clients, "alcohol_qty": alcohol_qty, "daily_revenue": daily_revenue}
    )


@sbp.route("/user_products")
@context.permission_only(PermissionType.write, PermissionScope.bar)
def get_user_products():
    """Return the list of products that a user can buy."""
    # Get user
    pceen = PCeen.query.filter_by(username=flask.request.args["username"]).first()
    if not pceen:
        flask.abort(404)

    # Get inventory
    inventory = BarItem.query.order_by(BarItem.name.asc()).all()

    # Get favorite items
    favorite_inventory = BarItem.query.filter_by(is_favorite=True).order_by(BarItem.name.asc()).all()

    pay_template = flask.render_template(
        "bar/_user_products.html", pceen=pceen, inventory=inventory, favorite_inventory=favorite_inventory
    )

    return {"html": pay_template}, 200


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


@sbp.route("/nickname/<pceen_id>", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.bar)
def post_nickname(pceen_id: str):
    """Set a user nickname."""
    if not pceen_id.isdigit():
        flask.abort(400, "Field 'pceen_id' missing or invalid integer")
    pceen: PCeen | None = PCeen.query.get(int(pceen_id))
    if not pceen or not pceen.has_permission(PermissionType.read, PermissionScope.bar):
        flask.abort(404, f"PCeen #{pceen_id} does not exist or has no access to the Bar module")

    nickname = flask.request.form.get("nickname")
    if nickname is None:
        flask.abort(400, "Field 'nickname' missing")

    pceen.bar_nickname = nickname
    db.session.commit()

    flask.flash(_("Le surnom de %(name)s a bien été modifié", name=pceen.full_name), "success")
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
    transaction = BarTransaction.query.filter_by(id=transaction_id).first_or_404()
    if transaction.is_reverted:
        flask.abort(422, f"Transaction #{transaction} has already been reverted.")

    # Check if user balance stays positive before reverting
    client: PCeen = transaction.client
    if client.bar_balance < transaction.balance_change:
        flask.abort(
            422,
            _("%(pceen)s's balance would be negative if this transaction were reverted.", pceen=client.full_name),
        )

    # Revert client balance
    client.bar_balance -= transaction.balance_change

    # Revert item quantity
    if transaction.item and transaction.item.is_quantifiable:
        transaction.item.quantity += 1

    # BarTransaction is now reverted: it won't ever be 'unreverted'
    transaction.is_reverted = True
    transaction.revert_date = datetime.datetime.utcnow()
    transaction.reverter = context.g.pceen

    db.session.commit()

    flask.flash(_("La transaction #%(transaction_id)s a bien été annulée.", transaction_id=transaction.id), "primary")
    return {}, 204


@sbp.route("/quick_access_item", methods=["PATCH"])
@context.permission_only(PermissionType.write, PermissionScope.bar)
def set_quick_access_item():
    """Set the quick access item."""
    # Get arguments
    item_name = flask.request.args.get("item_name", None, type=str)

    # Get item
    item = BarItem.query.filter_by(name=item_name).first_or_404()

    # Get quick access item id
    BarSettings.quick_access_item = item

    # Update the quick access item id
    quick_access_item_id = GlobalSetting.query.filter_by(key="QUICK_ACCESS_ITEM_ID").first()
    quick_access_item_id.value = item.id
    db.session.commit()

    return flask.redirect(flask.request.referrer)


@sbp.route("/item", methods=["DELETE"])
@context.permission_only(PermissionType.write, PermissionScope.bar)
def delete_item():
    """Delete an item from the inventory."""
    item_name = flask.request.args.get("item_name", None, type=str)

    item = BarItem.query.filter_by(name=item_name).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flask.flash("The item " + item_name + " has been deleted.", "primary")
    return flask.redirect(flask.request.referrer)


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

    pceen.bar_balance += amount

    transaction = BarTransaction(
        _client_id=pceen.id, _barman_id=context.g.pceen.id, type=BarTransactionType.top_up, balance_change=amount
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

    pceen.bar_balance -= item.price
    if item.is_quantifiable:
        item.quantity -= 1

    transaction = BarTransaction(
        _client_id=pceen.id,
        _item_id=item.id,
        _barman_id=context.g.pceen.id,
        date=datetime.datetime.utcnow(),
        type=BarTransactionType.pay_item,
        balance_change=-item.price,
    )
    db.session.add(transaction)
    db.session.commit()

    flask.flash(
        _("Achat validé : %(item)s (%(amount)s). Annuler :", item=item.name, amount=format_currency(item.price, "EUR"))
        + flask.Markup(flask.render_template("bar/_revert_button.html", transaction=transaction)),
        "success",
    )
    return {}, 204
