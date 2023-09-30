"""PC est magique Flask App - Bekk Models"""

from __future__ import annotations
from app import models

import datetime
import typing

import sqlalchemy as sa

from app import db
from app.utils.columns import (
    column,
    Column,
)


Model = typing.cast(type[type], db.Model)  # type checking hack


class Bekk(db.Model):
    """Bekk registration information"""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    name: Column[str] = column(sa.String(120), nullable=False)
    promo: Column[int] = column(sa.Integer(), nullable=False)
    date: Column[datetime.date] = column(sa.Date(), nullable=False)
