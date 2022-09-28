"""PC est magique Flask App - Bar Models"""

from __future__ import annotations

import datetime
import typing

import sqlalchemy as sa
from sqlalchemy.orm import Query

from app import db
from app.enums import BarTransactionType
from app.utils.columns import (
    column,
    many_to_one,
    one_to_many,
    Column,
    Relationship,
)


Model = typing.cast(type[type], db.Model)  # type checking hack


class BarItem(db.Model):
    """An item that can be bought at the Bar."""

    __tablename__ = "bar_item"

    id: Column[int] = column(sa.Integer(), primary_key=True)
    name: Column[str] = column(sa.String(64), unique=True, nullable=False)

    price: Column[float] = column(sa.Float(), nullable=False)

    is_alcohol: Column[bool] = column(sa.Boolean(), nullable=False)
    is_quantifiable: Column[bool] = column(sa.Boolean(), nullable=False)
    quantity: Column[int] = column(sa.Integer(), nullable=True)

    is_favorite: Column[bool] = column(sa.Boolean(), default=False)

    transactions: Relationship[Query[models.BarTransaction]] = one_to_many("BarTransaction.item", lazy="dynamic")

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<BarItem #{self.id}: {self.name}>"


class BarTransaction(db.Model):
    """A transaction that can be done at the Bar."""

    __tablename__ = "bar_transaction"

    id: Column[int] = column(sa.Integer(), primary_key=True)

    date: Column[datetime.datetime] = column(sa.DateTime, default=datetime.datetime.utcnow, nullable=False)

    # The barman who made the transaction
    _barman_id: Column[str] = column(sa.ForeignKey("pceen.id"), nullable=False)
    barman: Relationship[models.PCeen] = many_to_one("PCeen.bar_transactions_cashed", foreign_keys=[_barman_id])

    # Not NULL if type is 'Pay <BarItem>' or 'Top up'
    _client_id: Column[int] = column(sa.ForeignKey("pceen.id"), nullable=False)
    client: Relationship[models.PCeen] = many_to_one("PCeen.bar_transactions_made", foreign_keys=[_client_id])

    # Not NULL if type is 'Pay <BarItem>'
    _item_id: Column[int] = column(sa.ForeignKey("bar_item.id"), nullable=True)
    item: Relationship[BarItem] = many_to_one("BarItem.transactions")

    type: Column[BarTransactionType] = column(sa.Enum(BarTransactionType), nullable=False)
    balance_change: Column[float] = column(sa.Float(), nullable=False)

    # True if the transaction has been reverted. In this case, won't ever go back to False
    is_reverted: Column[bool] = column(sa.Boolean(), default=False)
    revert_date: Column[datetime.datetime] = column(sa.DateTime, default=datetime.datetime.utcnow, nullable=True)
    _reverter_id: Column[str] = column(sa.ForeignKey("pceen.id"), nullable=True)
    reverter: Relationship[models.PCeen] = many_to_one("PCeen.bar_transactions_reverted", foreign_keys=[_reverter_id])

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<BarTransaction #{self.id} ({self.client.username} / {self.item.name} / {self.date})>"


class GlobalSetting(db.Model):
    """App global settings model."""

    id: Column[int] = column(sa.Integer(), primary_key=True)

    name: Column[str] = column(sa.String(128), nullable=False)
    key: Column[str] = column(sa.String(64), nullable=False)
    value: Column[int] = column(sa.Integer(), default=0)

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<GlobalSetting #{self.id}: {self.key}>"


from app import models
