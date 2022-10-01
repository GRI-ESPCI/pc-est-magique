"""PC est magique - Bar Utils"""

from __future__ import annotations

import datetime
import typing

import flask
from flask_babel import _
from app.enums import BarTransactionType

from app.models import BarItem, BarTransaction, PCeen


class BarSettings:
    max_daily_alcoholic_drinks_per_user: int
    _quick_access_item_id: BarItem

    class _QuickAccessItemDescriptor:
        def __get__(self, obj: None, objtype=None):
            return BarItem.query.get(BarSettings._quick_access_item_id)

    quick_access_item = _QuickAccessItemDescriptor()


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
            flask.flash(_("%(pceen)s hasn't given a deposit.", pceen=pceen.full_name), "danger")
        return False

    return True


def _pceen_can_buy_alcohol(pceen: PCeen, flash: bool) -> bool:
    if pceen.current_bar_daily_data.alcohol_bought_count >= BarSettings.max_daily_alcoholic_drinks_per_user:
        if flash:
            flask.flash(
                _("%(pceen)s has reached the limit of %(limit)s drinks per night.", pceen=pceen.full_name, limit=limit),
                "danger",
            )
        return False

    return True


def _item_can_be_bought(item: BarItem, flash: bool) -> bool:
    if item.is_quantifiable and item.quantity <= 0:
        if flash:
            flask.flash(_("No %(item)s left.", item=item.name), "danger")
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
                _("%(pceen)s doesn't have enough funds to buy %(item)s.", pceen=pceen.full_name, item=item.name),
                "danger",
            )
        return False

    if item.is_alcohol and not _pceen_can_buy_alcohol(pceen, flash):
        return False

    return True


def get_items_descriptions(pceen: PCeen) -> typing.Iterator[tuple[BarItem, tuple[bool, str, bool]]]:
    balance = pceen.bar_balance
    can_buy_anything = _pceen_can_buy_anything(pceen, False)
    can_buy_alcohol = can_buy_anything and _pceen_can_buy_alcohol(pceen, False)

    no_favorites_seen = True
    for item in BarItem.query.order_by(BarItem.favorite_index.desc(), BarItem.name.asc()).all():
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
        elif not can_buy_alcohol and item.is_alcohol:
            can_be_bought = False
            limit_message = _("Limite d'alcool quotidienne atteinte")
        elif not _item_can_be_bought(item, False):
            can_be_bought = False
            limit_message = _("Article épuisé (voir onglet Inventaire)")

        yield item, (can_be_bought, limit_message, first_no_favorite)
