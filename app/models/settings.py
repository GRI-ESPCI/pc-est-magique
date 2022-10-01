"""PC est magique Flask App - Bar Models"""

from __future__ import annotations

import typing

import sqlalchemy as sa

from app import db
from app.utils.columns import column, Column


Model = typing.cast(type[type], db.Model)  # type checking hack


class GlobalSetting(db.Model):
    """App global settings model."""

    id: Column[int] = column(sa.Integer(), primary_key=True)

    name_fr: Column[str] = column(sa.String(128), nullable=False)
    name_en: Column[str] = column(sa.String(128), nullable=False)

    key: Column[str] = column(sa.String(64), nullable=False)
    value: Column[int] = column(sa.Integer(), default=0)

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<GlobalSetting #{self.id}: {self.key}>"


from app import models
