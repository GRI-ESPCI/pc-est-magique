"""PC est magique Flask App - Bar Models"""

from __future__ import annotations

import datetime
import typing

import sqlalchemy as sa
from sqlalchemy.orm import Query

from app import db
from app.enums import BarTransactionType
from app.utils.columns import column, many_to_one, one_to_many, Column, Relationship


Model = typing.cast(type[type], db.Model)  # type checking hack


class BarItem(db.Model):
    """An item that can be bought at the Bar."""

    __tablename__ = "bar_item"

    id: Column[int] = column(sa.Integer(), primary_key=True)
    name: Column[str] = column(sa.String(64), nullable=False)

    price: Column[float] = column(sa.Numeric(6, 2, asdecimal=False), nullable=False)

    is_alcohol: Column[bool] = column(sa.Boolean(), nullable=False)
    alcohol_degree: Column[bool] = column(sa.Numeric(4, 2), nullable=True)
    is_quantifiable: Column[bool] = column(sa.Boolean(), nullable=False)
    quantity: Column[int] = column(sa.Integer(), nullable=True)

    favorite_index: Column[int] = column(sa.Integer(), nullable=False, default=0)
    archived: Column[bool] = column(sa.Boolean(), nullable=False, default=False)

    transactions: Relationship[Query[models.BarTransaction]] = one_to_many("BarTransaction.item", lazy="dynamic")

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<BarItem #{self.id}: {self.name}>"


class BarTransaction(db.Model):
    """A transaction that can be done at the Bar."""

    __tablename__ = "bar_transaction"

    id: Column[int] = column(sa.Integer(), primary_key=True)

    _client_id: Column[int] = column(sa.ForeignKey("pceen.id"), nullable=False)
    client: Relationship[models.PCeen] = many_to_one("PCeen.bar_transactions_made", foreign_keys=[_client_id])

    _barman_id: Column[str] = column(sa.ForeignKey("pceen.id"), nullable=False)
    barman: Relationship[models.PCeen] = many_to_one("PCeen.bar_transactions_cashed", foreign_keys=[_barman_id])

    date: Column[datetime.datetime] = column(sa.DateTime(), default=datetime.datetime.utcnow, nullable=False)
    type: Column[BarTransactionType] = column(sa.Enum(BarTransactionType), nullable=False)

    _item_id: Column[int] = column(sa.ForeignKey("bar_item.id"), nullable=True)
    item: Relationship[BarItem] = many_to_one("BarItem.transactions")

    balance_change: Column[float] = column(sa.Numeric(6, 2, asdecimal=False), nullable=False)

    # True if the transaction has been reverted. In this case, won't ever go back to False
    is_reverted: Column[bool] = column(sa.Boolean(), default=False)
    revert_date: Column[datetime.datetime] = column(sa.DateTime(), nullable=True)
    _reverter_id: Column[str] = column(sa.ForeignKey("pceen.id"), nullable=True)
    reverter: Relationship[models.PCeen] = many_to_one("PCeen.bar_transactions_reverted", foreign_keys=[_reverter_id])

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<BarTransaction #{self.id} ({self.client.username} / {self.item.name if self.item else '<no item>'} / {self.date})>"

    def _update_linked_objects(self, revert: bool):
        factor = -1 if revert else 1
        # Client
        self.client.bar_balance += factor * self.balance_change
        # Item
        if self.item and self.item.is_quantifiable:
            self.item.quantity -= factor * 1
        # Daily data
        daily_data = BarDailyData.from_pceen_and_timestamp(self.client, self.date, create=True)
        daily_data.balance_change += factor * self.balance_change
        if self.item:
            daily_data.items_bought_count += factor * 1
            daily_data.total_spent -= factor * self.balance_change
            if self.item.is_alcohol:
                degree = 5 if self.item.alcohol_degree is None else self.item.alcohol_degree
                daily_data.alcohol_bought_count += factor * degree

    @classmethod
    def create_from_item_bought(
        cls, client: models.PCeen, barman: models.PCeen, item: models.PCeen, date: datetime.datetime
    ) -> BarTransaction:
        transaction = cls(
            client=client,
            barman=barman,
            date=date,
            type=BarTransactionType.pay_item,
            item=item,
            balance_change=-item.price,
        )
        transaction._update_linked_objects(revert=False)
        return transaction

    @classmethod
    def create_from_top_up(
        cls, client: models.PCeen, barman: models.PCeen, amount: float, date: datetime.datetime
    ) -> BarTransaction:
        transaction = cls(
            client=client, barman=barman, date=date, type=BarTransactionType.top_up, balance_change=amount
        )
        transaction._update_linked_objects(revert=False)
        return transaction

    def revert(self, reverter: models.PCeen | None = None) -> None:
        if self.is_reverted:
            raise ValueError(f"Transaction {self} is already reverted!")
        # BarTransaction is now reverted: it won't ever be 'unreverted'
        self.is_reverted = True
        self.revert_date = datetime.datetime.utcnow()
        self.reverter = reverter
        self._update_linked_objects(revert=True)


class BarDailyData(db.Model):
    """The daily Bar transactions of a PCeen."""

    __tablename__ = "bar_daily_data"

    id: Column[int] = column(sa.Integer(), primary_key=True)

    _pceen_id: Column[int] = column(sa.ForeignKey("pceen.id"), nullable=False)
    pceen: Relationship[models.PCeen] = many_to_one("PCeen.bar_daily_data")

    date: Column[datetime.date] = column(sa.Date(), nullable=False)

    balance_change: Column[float] = column(sa.Numeric(6, 2, asdecimal=False), nullable=False, default=0.0)
    items_bought_count: Column[int] = column(sa.Integer(), nullable=False, default=0)
    alcohol_bought_count: Column[int] = column(sa.Numeric(4, 2, asdecimal=False), nullable=False, default=0.0)
    total_spent: Column[float] = column(sa.Numeric(6, 2, asdecimal=False), nullable=False, default=0.0)

    pceen_date_unique = sa.UniqueConstraint(_pceen_id, date)

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<BarDailyData #{self.id} ({self.pceen.username} / {self.date})>"

    class _FakeBarDailyData(typing.NamedTuple):
        pceen: models.PCeen
        date: datetime.date
        balance_change: float = 0.0
        items_bought_count: int = 0
        alcohol_bought_count: int = 0
        total_spent: float = 0.0

    @classmethod
    def from_pceen_and_timestamp(
        cls, pceen: models.PCeen, timestamp: datetime.datetime, create: bool = False
    ) -> BarDailyData:
        date = timestamp.date()
        if timestamp.hour < 4:  # 4h UTC = 5-6h Paris
            date -= datetime.timedelta(days=1)

        if data := cls.query.filter_by(pceen=pceen, date=date).one_or_none():
            return data
        if create:
            data = cls(pceen=pceen, date=date)
            db.session.add(data)
            db.session.flush()
            return data
        return cls._FakeBarDailyData(pceen=pceen, date=date)


from app import models
