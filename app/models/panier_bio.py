"""PC est magique Flask App - Bekk Models"""

from __future__ import annotations
from app import models

import datetime
import typing

import sqlalchemy as sa
from sqlalchemy.orm import Query

from app import db
from app.utils.columns import (
    column,
    many_to_one,
    one_to_many,
    Column,
    Relationship,
)


Model = typing.cast(type[type], db.Model)  # type checking hack


class OrderPanierBio(db.Model):
    """Bio basket registration information"""

    # Registration informations
    id: Column[int] = column(sa.Integer(), primary_key=True)
    date: Column[datetime.date] = column(sa.Date(), nullable=False)
    payment_method: Column[str] = column(sa.String(120), nullable=False)
    phone_number: Column[str] = column(sa.String(20), nullable=True)
    comment: Column[str] = column(sa.String(500), nullable=True)

    # Administration informations
    payment_made: Column[bool] = column(sa.Boolean(), nullable=False, default=False)
    treasurer_validate: Column[bool] = column(sa.Boolean(), nullable=False, default=False)
    taken: Column[bool] = column(sa.Boolean(), nullable=False, default=False)

    name: Column[str] = column(sa.String(50), nullable=False)  # For non-connected uses
    service: Column[str] = column(sa.String(50), nullable=False)  # For non-connected uses

    _period_id: Column[int] = column(sa.ForeignKey("period_panier_bio.id"), nullable=False)
    period: Relationship[models.PeriodPanierBio] = many_to_one("PeriodPanierBio.order", foreign_keys=[_period_id])

    _pceen_id: Column[int] = column(sa.ForeignKey("pceen.id"), nullable=True)
    pceen: Relationship[models.PCeen] = many_to_one("PCeen.order_panier_bio", foreign_keys=[_pceen_id])


class PeriodPanierBio(db.Model):
    """Periods to order panier bio"""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    start_date: Column[datetime.date] = column(sa.Date(), nullable=False)
    end_date: Column[datetime.date] = column(sa.Date(), nullable=False)
    disabled_days: Column[str] = column(sa.String(500), nullable=True)
    active: Column[bool] = column(sa.Boolean(), nullable=False)

    order: Relationship[Query[models.OrderPanierBio]] = one_to_many("OrderPanierBio.period", lazy="dynamic")
