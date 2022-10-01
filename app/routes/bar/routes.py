"""PC est magique - Bar Routes"""

from calendar import monthrange
import datetime

import flask
from flask_babel import _
from sqlalchemy import extract
import sqlalchemy
from unidecode import unidecode

from app import context, db
from app.models import PCeen, BarItem, BarTransaction, GlobalSetting, PermissionScope, PermissionType, Role, Permission
from app.routes.bar import bp
from app.routes.bar.forms import AddOrEditItemForm, GlobalSettingsForm
from app.routes.bar.utils import get_avatar_token_args, get_items_descriptions
from app.utils import helpers
from app.utils.global_settings import Settings


@bp.before_app_first_request
def retrieve_bar_settings():
    # Call getter for all settings to load cache
    Settings.max_daily_alcoholic_drinks_per_user
    Settings.quick_access_item


@bp.route("/stats")
@context.permission_only(PermissionType.read, PermissionScope.bar_stats)
def stats():
    # Get current day start
    today = datetime.datetime.today()
    current_year = today.year
    current_month = today.month
    current_day_start = datetime.datetime.combine(today, datetime.time(hour=6))
    if today.hour < 6:
        current_day_start -= datetime.timedelta(days=1)

    # Daily clients
    nb_daily_clients = PCeen.query.filter(
        PCeen.bar_transactions_made.any(BarTransaction.date > current_day_start)
    ).count()

    # Daily alcohol consumption
    alcohol_qty = (
        BarTransaction.query.filter(
            BarTransaction.date > current_day_start,
            BarTransaction.type.like("Pay%"),
            BarTransaction.item.has(is_alcohol=True),
            BarTransaction.is_reverted == False,
        ).count()
        * 0.25
    )

    # Daily revenue
    daily_transactions = BarTransaction.query.filter(
        BarTransaction.date > current_day_start,
        BarTransaction.type.like("Pay%"),
        BarTransaction.is_reverted == False,
    ).all()
    daily_revenue = sum([abs(t.balance_change) for t in daily_transactions])

    # Compute number of clients this month
    clients_this_month = [
        len(
            set(
                t.client_id
                for t in BarTransaction.query.filter(
                    extract("day", BarTransaction.date) == day,
                    extract("month", BarTransaction.date) == current_month,
                    extract("year", BarTransaction.date) == current_year,
                    BarTransaction.type.like("Pay%"),
                    BarTransaction.is_reverted == False,
                ).all()
            )
        )
        for day in range(1, 32)
    ]

    clients_alcohol_this_month = [
        len(
            set(
                t.client_id
                for t in BarTransaction.query.filter(
                    extract("day", BarTransaction.date) == day,
                    extract("month", BarTransaction.date) == current_month,
                    extract("year", BarTransaction.date) == current_year,
                    BarTransaction.type.like("Pay%"),
                    BarTransaction.item.has(is_alcohol=True),
                    BarTransaction.is_reverted == False,
                ).all()
            )
        )
        for day in range(1, 32)
    ]

    # Generate days labels
    days_labels = [
        "%.2d" % current_month + "/" + "%.2d" % day for day in range(1, monthrange(current_year, current_month)[1] + 1)
    ]

    return flask.render_template(
        "bar/dashboard.html",
        title="Dashboard",
        clients_this_month=clients_this_month,
        clients_alcohol_this_month=clients_alcohol_this_month,
        days_labels=days_labels,
        nb_daily_clients=nb_daily_clients,
        alcohol_qty=alcohol_qty,
        daily_revenue=daily_revenue,
    )


@bp.route("/search")
@context.permission_only(PermissionType.write, PermissionScope.bar)
def search():
    """Render search page."""
    # Get arguments
    page = flask.request.args.get("page", 1, type=int)
    sort = flask.request.args.get("sort", "name", type=str)
    way = flask.request.args.get("way", "asc", type=str)
    query = flask.request.args.get("q", type=str)

    if not query:
        return helpers.ensure_safe_redirect("bar.me")

    pceen = PCeen.query.filter_by(username=query).one_or_none()
    if pceen and pceen.has_permission(PermissionType.read, PermissionScope.bar):
        return helpers.ensure_safe_redirect("bar.user", username=pceen.username)

    paginator = (
        PCeen.query.join(PCeen.roles)
        .join(Role.permissions)
        .filter(
            Permission.type == PermissionType.read,
            Permission.scope == PermissionScope.bar,
            sqlalchemy.func.lower(sqlalchemy.func.unaccent(PCeen.full_name)).contains(unidecode(query).lower()),
        )
        .order_by(
            (PCeen.promo.desc() if way == "desc" else PCeen.promo.asc())
            if sort == "promo"
            else (PCeen.full_name.desc() if way == "desc" else PCeen.full_name.asc())
        )
        .paginate(page, flask.current_app.config["USERS_PER_PAGE"], True)
    )

    if paginator.total == 1:
        return helpers.ensure_safe_redirect("bar.user", username=paginator.items[0].username)

    return flask.render_template(
        "bar/search.html",
        title=_("Recherche – Bar"),
        paginator=paginator,
        query=query,
        sort=sort,
        way=way,
        avatar_token_args=get_avatar_token_args(),
    )


@bp.route("/")
@bp.route("/me")
@context.permission_only(PermissionType.read, PermissionScope.bar)
def me():
    return _user(context.g.pceen)


@bp.route("/user/<username>")
@context.permission_only(PermissionType.write, PermissionScope.bar)
def user(username: str):
    # Get user
    pceen: PCeen | None = PCeen.query.filter_by(username=username).one_or_none()
    if not pceen or not pceen.has_permission(PermissionType.read, PermissionScope.bar):
        flask.abort(404)

    return _user(pceen)


def _user(pceen: PCeen):
    """Render the user profile page."""
    # Get pceen transactions
    page = flask.request.args.get("page", 1, type=int)
    transactions = pceen.bar_transactions_made.order_by(BarTransaction.date.desc()).paginate(page, 5, True)

    # Get inventory
    item_descriptions = dict(get_items_descriptions(pceen))

    # Get quick access item
    quick_access_item = Settings.quick_access_item

    return flask.render_template(
        "bar/user.html",
        title=_("%(name)s – Profil Bar", name=pceen.full_name),
        pceen=pceen,
        item_descriptions=item_descriptions,
        quick_access_item=quick_access_item,
        transactions=transactions,
        avatar_token_args=get_avatar_token_args(),
        max_daily_alcoholic_drinks_per_user=Settings.max_daily_alcoholic_drinks_per_user,
    )


@bp.route("/transactions")
@context.permission_only(PermissionType.write, PermissionScope.bar)
def transactions():
    """Render the transactions page."""
    # Get arguments
    page = flask.request.args.get("page", 1, type=int)
    sort = flask.request.args.get("sort", "desc", type=str)

    # Sort transactions alphabetically
    order_clause = BarTransaction.id.asc() if sort == "asc" else BarTransaction.id.desc()
    transactions = BarTransaction.query.order_by(order_clause).paginate(
        page, flask.current_app.config["ITEMS_PER_PAGE"], True
    )

    return flask.render_template("bar/transactions.html", title="Transactions", transactions=transactions, sort=sort)


@bp.route("/items", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.bar)
def items():
    """Render the items page."""
    form = AddOrEditItemForm()
    if form.is_submitted():
        if form.validate():
            favorite_index = form.favorite_index.data if form.is_favorite.data else 0
            quantity = (form.quantity.data or 0) if form.is_quantifiable.data else None
            if form.id.data:
                # Edit existing item
                item: BarItem = BarItem.query.get(form.id.data)
                item.name = form.name.data
                item.is_quantifiable = form.is_quantifiable.data
                item.quantity = quantity
                item.price = form.price.data
                item.is_alcohol = form.is_alcohol.data
                item.favorite_index = favorite_index
                flask.flash(_("Article %(item)s modifié.", item=item.name), "success")
            else:
                # Create item
                item = BarItem(
                    name=form.name.data,
                    is_quantifiable=form.is_quantifiable.data,
                    quantity=quantity,
                    price=form.price.data,
                    is_alcohol=form.is_alcohol.data,
                    favorite_index=favorite_index,
                )
                db.session.add(item)
                flask.flash(_("Article %(item)s créé.", item=item.name), "success")
            db.session.commit()

        else:
            for field, messages in form.errors.items():
                flask.flash(f"{form._fields[field].label.text} : {messages[0]}", "danger")

    # Get arguments
    page = flask.request.args.get("page", 1, type=int)
    sort = flask.request.args.get("sort", "name", type=str)
    way = flask.request.args.get("way", "asc", type=str)

    # Sort items alphabetically
    paginator = (
        BarItem.query.filter(~BarItem.archived)
        .order_by(
            (BarItem.quantity.desc() if way == "desc" else BarItem.quantity.asc())
            if sort == "quantity"
            else (BarItem.name.desc() if way == "desc" else BarItem.name.asc())
        )
        .paginate(page, flask.current_app.config["ITEMS_PER_PAGE"], True)
    )

    return flask.render_template(
        "bar/items.html",
        title=_("Articles – Bar"),
        paginator=paginator,
        sort=sort,
        way=way,
        quick_access_item=Settings.quick_access_item,
        form=form,
    )


@bp.route("/global_settings", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.bar)
def global_settings():
    """Render the global settings page."""
    form = GlobalSettingsForm()
    if form.validate_on_submit():
        settings = GlobalSetting.query.all()
        for index, s in enumerate(settings):
            s.value = form.value.data[index]
        db.session.commit()
        flask.flash("Global settings successfully updated.", "primary")
        return helpers.ensure_safe_redirect("bar.global_settings")
    else:
        settings = GlobalSetting.query.all()
        for index, s in enumerate(settings):
            form.value.append_entry(s.value)
            form.value.entries[index].label.text = s.name
    return flask.render_template("bar/global_settings.html", title="Global settings", form=form)
