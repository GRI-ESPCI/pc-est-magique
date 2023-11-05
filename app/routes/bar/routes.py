"""PC est magique - Bar Routes"""

from calendar import monthrange
import datetime
import os
from typing import NamedTuple

import flask
from flask_babel import _, format_date
import sqlalchemy
from unidecode import unidecode
import werkzeug.datastructures

from app import context, db
from app.models import (
    PCeen,
    BarItem,
    BarTransaction,
    GlobalSetting,
    PermissionScope,
    PermissionType,
    Role,
    Permission,
    BarDailyData,
)
from app.routes.bar import bp
from app.routes.bar.forms import AddOrEditItemForm, GlobalSettingsForm, DataExport, EditBarUserForm
from app.routes.bar.utils import get_avatar_token_args, get_export_data, get_items_descriptions, save_bar_avatar
from app.utils import helpers, roles
from app.utils.global_settings import Settings


@bp.before_app_first_request
def retrieve_bar_settings():
    # Call getter for all settings to load cache
    Settings.max_daily_alcoholic_drinks_per_user
    Settings.quick_access_item


@bp.route("/stats")
@context.permission_only(PermissionType.read, PermissionScope.bar_stats)
def stats():
    # Get arguments
    date = flask.request.args.get("date", type=datetime.date.fromisoformat)
    is_today = False
    if not date:
        is_today = True
        timestamp = datetime.datetime.utcnow()
        date = timestamp.date()
        if timestamp.hour < 4:  # 4h UTC = 5-6h Paris
            date -= datetime.timedelta(days=1)

    # Daily clients
    daily_data: list[BarDailyData] = BarDailyData.query.filter(
        BarDailyData.date == date, BarDailyData.total_spent != 0
    ).all()

    # Daily alcohol consumption
    alcohol_qty = sum(data.alcohol_bought_count for data in daily_data)

    # Daily revenue
    daily_revenue = sum(data.total_spent for data in daily_data)

    days_range = range(1, monthrange(date.year, date.month)[1] + 1)

    # Compute number of clients this month
    clients_this_month = [
        BarDailyData.query.filter(
            BarDailyData.date == date.replace(day=day), BarDailyData.items_bought_count > 0
        ).count()
        for day in days_range
        if day <= date.day
    ]

    clients_alcohol_this_month = [
        BarDailyData.query.filter(
            BarDailyData.date == date.replace(day=day), BarDailyData.alcohol_bought_count > 0
        ).count()
        for day in days_range
        if day <= date.day
    ]

    revenues_this_month = [
        db.session.query(sqlalchemy.func.sum(BarDailyData.total_spent))
        .filter(BarDailyData.date == date.replace(day=day))
        .scalar()
        for day in days_range
        if day <= date.day
    ]

    # Client total moula
    (total_balances_sum,) = db.session.query(sqlalchemy.func.sum(PCeen.bar_balance)).first()

    # Best customer
    customers_consumption_this_month = (
        db.session.query(BarDailyData._pceen_id, sqlalchemy.func.sum(BarDailyData.total_spent))
        .filter(
            sqlalchemy.extract("year", BarDailyData.date) == date.year,
            sqlalchemy.extract("month", BarDailyData.date) == date.month,
        )
        .group_by(BarDailyData._pceen_id)
        .all()
    )

    best_customer_name = "Sylvain Gilat"
    if customers_consumption_this_month:
        best_customer_id, _sum = max(customers_consumption_this_month, key=lambda tup: tup[1])
        best_customer_name = PCeen.query.get(best_customer_id).full_name

    return flask.render_template(
        "bar/stats.html",
        title=_("Stats – Bar"),
        date=date,
        is_today=is_today,
        clients_this_month=",".join(str(nb) for nb in clients_this_month),
        clients_alcohol_this_month=",".join(str(nb) for nb in clients_alcohol_this_month),
        revenues_this_month=",".join(str(nb) for nb in revenues_this_month),
        days_labels=",".join(format_date(date.replace(day=day), "medium") for day in days_range),
        nb_daily_clients=len(daily_data),
        alcohol_qty=alcohol_qty,
        daily_revenue=daily_revenue,
        best_customer_name=best_customer_name,
        total_balances_sum=total_balances_sum,
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
        .paginate(page, flask.current_app.config["BAR_USERS_PER_PAGE"], True)
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
@context.any_permission_only(
    (PermissionType.read, PermissionScope.bar),
    (PermissionType.read, PermissionScope.bar_stats),
)
def main():
    return helpers.ensure_safe_redirect(
        "bar.stats" if context.has_permission(PermissionType.read, PermissionScope.bar_stats) else "bar.me"
    )


@bp.route("/me")
@context.permission_only(PermissionType.read, PermissionScope.bar)
def me():
    page = flask.request.args.get("page", 1, type=int)
    if context.has_permission(PermissionType.write, PermissionScope.bar):
        return helpers.ensure_safe_redirect("bar.user", username=context.g.pceen.username, page=page, next=None)
    return _user(context.g.pceen, page=page)


@bp.route("/user/<username>", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.bar)
def user(username: str, page: int | None = None):
    # Get user
    pceen: PCeen | None = PCeen.query.filter_by(username=username).one_or_none()
    if not pceen or not pceen.has_permission(PermissionType.read, PermissionScope.bar):
        flask.abort(404)

    form = EditBarUserForm()
    if form.validate_on_submit():
        if form.nickname.data != pceen.bar_nickname:
            pceen.bar_nickname = form.nickname.data
            db.session.commit()
            flask.flash(_("Le surnom de %(name)s a bien été modifié", name=pceen.full_name), "success")

        if pceen.has_permission(PermissionType.write, PermissionScope.bar):
            if not form.is_barman.data:
                roles.revoke_barman_role(pceen)
                db.session.commit()
                helpers.log_action(f"Removed Barman role from {pceen}")
                flask.flash(_("%(name)s n'est maintenant plus barman / barmaid", name=pceen.full_name), "warning")
        elif form.is_barman.data:
            roles.grant_barman_role(pceen)
            db.session.commit()
            helpers.log_action(f"Added Barman role to {pceen}")
            flask.flash(_("%(name)s est maintenant barmaid / barmaid", name=pceen.full_name), "warning")

        if form.avatar.data:
            try:
                save_bar_avatar(pceen, form.avatar.data)
            except Exception as exc:
                flask.flash(_("Erreur lors de la transformation de la photo : %(exc)s", exc=exc))
            else:
                flask.flash(_("L'avatar de %(name)s a bien été modifié", name=pceen.full_name), "success")

    return _user(pceen, form=form, page=page)


def _user(pceen: PCeen, form: EditBarUserForm | None = None, page: int | None = None):
    """Render the user profile page."""
    # Get pceen transactions
    if page == None:
        page = flask.request.args.get("page", 1, type=int)
    transactions_paginator = pceen.bar_transactions_made.order_by(BarTransaction.date.desc()).paginate(page, 5, True)

    # Get inventory
    item_descriptions = dict(get_items_descriptions(pceen))

    # Get quick access item
    quick_access_item = Settings.quick_access_item

    # Is it the bar page of the connected pceen?
    personal_page = False
    if context.g.pceen == pceen:
        personal_page = True

    return flask.render_template(
        "bar/user.html",
        title=_("%(name)s – Profil Bar", name=pceen.full_name),
        pceen=pceen,
        item_descriptions=item_descriptions,
        quick_access_item=quick_access_item,
        paginator=transactions_paginator,
        avatar_token_args=get_avatar_token_args(),
        form=form,
        personal_page=personal_page,
    )


@bp.route("/transactions")
@context.permission_only(PermissionType.write, PermissionScope.bar)
def transactions():
    """Render the transactions page."""
    # Get arguments
    page = flask.request.args.get("page", 1, type=int)
    sort = flask.request.args.get("sort", "date", type=str)
    way = flask.request.args.get("way", "desc", type=str)

    # Sort transactions alphabetically
    paginator = BarTransaction.query.order_by(
        BarTransaction.date.desc() if way == "desc" else BarTransaction.date.asc()
    ).paginate(page, flask.current_app.config["BAR_ITEMS_PER_PAGE"], True)

    return flask.render_template(
        "bar/transactions.html", title=_("Transactions – Bar"), paginator=paginator, sort=sort, way=way
    )


@bp.route("/items", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.bar)
def items():
    """Render the items page."""
    form = AddOrEditItemForm()
    if form.is_submitted():
        if form.validate():
            favorite_index = form.favorite_index.data if form.is_favorite.data else 0
            quantity = (form.quantity.data or 0) if form.is_quantifiable.data else None
            alcohol_mass = form.alcohol_mass.data or 0
            if form.id.data:
                # Edit existing item
                item: BarItem = BarItem.query.get(form.id.data)
                item.name = form.name.data
                item.is_quantifiable = form.is_quantifiable.data
                item.quantity = quantity
                item.price = form.price.data
                item.alcohol_mass = alcohol_mass
                item.favorite_index = favorite_index
                flask.flash(_("Article %(item)s modifié.", item=item.name), "success")
            else:
                # Create item
                item = BarItem(
                    name=form.name.data,
                    is_quantifiable=form.is_quantifiable.data,
                    quantity=quantity,
                    price=form.price.data,
                    alcohol_mass=alcohol_mass,
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
            else (
                sqlalchemy.func.lower(BarItem.name).desc()
                if way == "desc"
                else sqlalchemy.func.lower(BarItem.name).asc()
            )
        )
        .paginate(page, flask.current_app.config["BAR_ITEMS_PER_PAGE"], True)
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


class ExportWeek(NamedTuple):
    start: datetime.date
    end: datetime.date
    filename: str
    url: str


@bp.route("/export", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.bar)
def export():
    """Render the data export page."""
    form = DataExport()
    if form.validate_on_submit():
        response = flask.Response()
        response.status_code = 200
        response.data = get_export_data(form.start.data, form.end.data)
        filename = form.filename.data or f"export_{form.start.data.isoformat()}_{form.end.data.isoformat()}.xlsx"
        response.headers = werkzeug.datastructures.Headers(
            {
                "Pragma": "public",  # required,
                "Expires": "0",
                "Cache-Control": "must-revalidate, post-check=0, pre-check=0",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "Content-Disposition": f'attachment; filename="{filename}";',
                "Content-Transfer-Encoding": "binary",
                "Content-Length": len(response.data),
            }
        )
        return response

    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=today.weekday())

    weeks = [ExportWeek(start=week_start, end=today, filename="current_week.xlsx", url="")]
    for i in range(4):
        week_start -= datetime.timedelta(days=7)
        week_start_iso = week_start.isocalendar()
        weeks.append(
            ExportWeek(
                start=week_start,
                end=week_start + datetime.timedelta(days=6),
                filename=f"week{week_start_iso.week}-{week_start_iso.year}.xlsx",
                url="",
            )
        )

    return flask.render_template("bar/export.html", title=_("Export de données – Bar"), form=form, weeks=weeks)


@bp.route("/settings", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.bar)
def settings():
    """Render the global settings page."""
    max_daily_alcoholic_drink_per_user = GlobalSetting.query.filter_by(key="MAX_DAILY_ALCOHOLIC_DRINKS_PER_USER").one()
    form = GlobalSettingsForm()
    if form.validate_on_submit():
        Settings.max_daily_alcoholic_drinks_per_user = form.max_daily_alcoholic_drinks_per_user.data
        if form.delete_background_image.data:
            try:
                os.remove(os.path.join("app", "static", "img", "bar_background.png"))
            except FileNotFoundError:
                pass

        if form.background_image.data:
            with open(os.path.join("app", "static", "img", "bar_background.png"), "wb") as fh:
                fh.write(form.background_image.data.read())

        flask.flash(_("Paramètres mis à jour."), "success")

    return flask.render_template(
        "bar/settings.html",
        title=_("Paramètres – Bar"),
        form=form,
        max_daily_alcoholic_drink_per_user=max_daily_alcoholic_drink_per_user,
    )


@bp.route("/welcome")
def welcome():
    """Render the (one-shot) welcome page."""
    if context.g.logged_in:
        if context.has_permission(PermissionType.read, PermissionScope.bar):
            flask.flash(
                _("Bonjour, camarade ! Ton compte du Bar a été migré dans ton compte PC est magique. Profite bien !"),
                "success",
            )
            return helpers.ensure_safe_redirect("bar.main")

        flask.flash(
            _(
                "Les comptes du Bar ont été migrés dans PC est magique. En revanche, pas de trace du tien... "
                "Pas de panique, il n'est pas perdu ! Contacte simplement un GRI."
            ),
            "danger",
        )
        return helpers.ensure_safe_redirect("main.index")

    return flask.render_template("bar/welcome.html", title=_("Migration du site du Bar"))
