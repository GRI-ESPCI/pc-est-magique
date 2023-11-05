"""PC est magique - Bar Utils"""

from __future__ import annotations
import datetime
import io
import os
import subprocess

import typing

import flask
from flask_babel import _
import xlsxwriter

from app.models import BarItem, PCeen, BarTransaction, BarTransactionType
from app.utils.global_settings import Settings
from app.utils.nginx import get_nginx_access_token


def month_year_iter(start_month, start_year, end_month, end_year):
    """Return month iterator."""
    ym_start = 12 * start_year + start_month - 1
    ym_end = 12 * end_year + end_month - 1
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        yield y, m + 1


def _pceen_can_buy_anything(pceen: PCeen, flash: bool) -> bool:
    if not pceen.bar_deposit:
        if flash:
            flask.flash(_("%(pceen)s n'a pas fourni de caution.", pceen=pceen.full_name), "danger")
        return False

    return True


def _pceen_can_buy_alcohol(pceen: PCeen, flash: bool, item: BarItem) -> bool:
    if (
        pceen.current_bar_daily_data.alcohol_bought_count + float(item.alcohol_mass)
        > Settings.max_daily_alcoholic_drinks_per_user
    ):
        if flash:
            flask.flash(
                _(
                    "%(pceen)s a atteint la limite de %(limit)s boissons alcoolisées par jour.",
                    pceen=pceen.full_name,
                    limit=Settings.max_daily_alcoholic_drinks_per_user,
                ),
                "danger",
            )
        return False

    return True


def _item_can_be_bought(item: BarItem, flash: bool) -> bool:
    if item.is_quantifiable and item.quantity <= 0:
        if flash:
            flask.flash(_("Article %(item)s épuisé.", item=item.name), "danger")
        return False

    return True


def can_buy(pceen: PCeen, item: BarItem | None, flash: bool = False) -> str | bool:
    """Return the user's right to buy the item."""
    if not _pceen_can_buy_anything(pceen, flash):
        return False

    if not _item_can_be_bought(item, flash):
        return False
    if pceen.bar_balance < item.price:
        if flash:
            flask.flash(
                _("%(pceen)s n'a pas assez d'argent pour acheter %(item)s.", pceen=pceen.full_name, item=item.name),
                "danger",
            )
        return False

    if item.alcohol_mass > 0 and not _pceen_can_buy_alcohol(pceen, flash, item):
        return False

    return True


def get_items_descriptions(pceen: PCeen) -> typing.Iterator[tuple[BarItem, tuple[bool, str, bool]]]:
    balance = pceen.bar_balance
    can_buy_anything = _pceen_can_buy_anything(pceen, False)

    no_favorites_seen = True
    for item in (
        BarItem.query.filter(BarItem.archived == False)
        .order_by(BarItem.favorite_index.desc(), BarItem.name.asc())
        .all()
    ):
        item: BarItem
        can_be_bought = True
        limit_message = ""
        first_no_favorite = False
        if no_favorites_seen and not item.favorite_index:
            no_favorites_seen = False
            first_no_favorite = True

        if not can_buy_anything:
            can_be_bought = False
            limit_message = _("Caution non validée, consommation interdite")
        elif balance < item.price:
            can_be_bought = False
            limit_message = _("Fonds insuffisants")
        elif item.alcohol_mass > 0 and not _pceen_can_buy_alcohol(pceen, False, item):
            can_be_bought = False
            limit_message = _("Limite d'alcool quotidienne atteinte")
        elif not _item_can_be_bought(item, False):
            can_be_bought = False
            limit_message = _("Article épuisé (modifiable sur la page Articles)")

        yield item, (can_be_bought, limit_message, first_no_favorite)


def get_avatar_token_args():
    # Avatar access
    ip = flask.request.headers.get("X-Real-Ip") or flask.current_app.config["FORCE_IP"]
    if not ip:
        flask.flash(_("IP non détectable, impossible d'afficher les avatars"), "danger")
    # Access OK

    return get_nginx_access_token("/bar_avatars", ip) if ip else None


def get_export_data(start: datetime.date, end: datetime.date) -> str:
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    worksheet = workbook.add_worksheet()

    transactions: list[BarTransaction] = BarTransaction.query.filter(
        BarTransaction.date.between(start, end),
        BarTransaction.type == BarTransactionType.pay_item,
        BarTransaction.is_reverted == False,
    ).all()

    header = ["id", "date", "barman", "client", "item", "type", "balance"]

    for col, header in enumerate(header):
        worksheet.write(0, col, header)

    row = 1
    for transaction in transactions:
        worksheet.write(row, 0, transaction.id)
        worksheet.write(row, 1, str(transaction.date))
        worksheet.write(row, 2, transaction.barman.full_name)
        worksheet.write(row, 3, transaction.client.full_name)
        # Item may not be available
        try:
            worksheet.write(row, 4, transaction.item.name)
        except AttributeError:
            worksheet.write(row, 4, "Error")
        worksheet.write(row, 5, transaction.type.name)
        worksheet.write(row, 6, f"{transaction.balance_change}€")
        row += 1

    workbook.close()
    output.seek(0)
    return output.read()


def save_bar_avatar(pceen: PCeen, data: typing.BinaryIO) -> None:
    """Save and corp avatar to local data drive."""
    dir = os.path.join(flask.current_app.config["PHOTOS_BASE_PATH"], "bar_avatars", str(pceen.promo))
    if not os.path.isdir(dir):
        os.mkdir(dir)

    filepath = os.path.join(dir, pceen.username)
    with open(filepath, "wb") as fh:
        fh.write(data.read())

    subprocess.run(
        [
            "convert",
            filepath,  # Take the picture,
            "-resize",
            "160x200^",  # Fill a 160x200 box,
            "-gravity",
            "center",  # Refer to image center,
            "-extent",
            "160x200",  # Then crop overflow
            f"{filepath}.jpg",
        ],
        capture_output=True,
        check=True,
    )
