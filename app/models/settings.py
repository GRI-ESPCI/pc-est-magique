"""PC est magique Flask App - Bar Models"""

from __future__ import annotations

import flask_babel
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
        return f"<GlobalSetting #{self.id}: {self.key}={self.value}>"

    @property
    def name(self) -> str:
        """Context-localized setting name.

        One of :attr:`.name_fr` or :attr:`.name_en`, depending on the
        request context (user preferred language). Read-only property.

        Raises:
            RuntimeError: If acceded outside of a request context.
        """
        locale = flask_babel.get_locale()
        if locale is None:
            raise RuntimeError("Outside of request context")
        return self.name_fr if locale.language[:2] == "fr" else self.name_en


from app import models
