"""PC est magique Flask App - V4A Models"""

from __future__ import annotations

import datetime
import typing

import sqlalchemy as sa

from app import db
from flask_babel import lazy_gettext as _l
from app.utils.columns import (
    column,
    Column,
    many_to_one,
    one_to_many,
    Relationship
)

Model = typing.cast(type[type], db.Model) # type checking hack


class V4A(Model):
    """A collection of tools for V4A"""

    __tablename__ = "v4a"
    id: Column[int] = column(sa.Integer(), primary_key=True)
    visible: Column[bool] = column(
        sa.Boolean(),
        nullable=False,
        default=False)
    name: Column[str] = column(sa.String(120), nullable=False)
    description: Column[str] = column(sa.String(500), nullable=True)
    ticketing_open: Column[bool] = column(sa.Boolean(), nullable=False, default=False)
    image_name: Column[str | None] = column(sa.String(120), nullable=True)
    full_description: Column[str] = column(sa.Text(), nullable=True)

    representations: Relationship[list[V4ARepresentation]] = one_to_many(
        "V4ARepresentation.v4a", order_by="V4ARepresentation.date"
    )
    pricings: Relationship[list[V4ARepresentation]] = one_to_many(
        "V4APricing.v4a", order_by="V4APricing.price"
    )

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<V4A #{self.id} ('{self.name}')>"

    def __str__(self) -> str:
        """Human-readible description of the V4A."""
        return self.name

class V4ARepresentation(Model):
    """V4A dates of representation"""

    __tablename__ = "v4a_representation"
    id: Column[int] = column(sa.Integer(), primary_key=True)
    date: Column[datetime.datetime] = column(sa.DateTime(), nullable=False)
    sits: Column[int] = column(sa.Integer(), nullable=False)

    _v4a_id: Column[int] = column(sa.ForeignKey("v4a.id"), nullable=False)
    v4a: Relationship[V4A] = many_to_one("V4A.representations")

    tickets: Relationship[list[V4ATicket]] = one_to_many("V4ATicket.representation")

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<V4A Representation #{self.id} ('{self.date}')>"

    def __str__(self) -> str:
        """Human-readible description of the V4A."""
        return self.date


class V4APricing(Model):
    """Pricing for V4A"""

    __tablename__ = "v4a_pricing"
    id: Column[int] = column(sa.Integer(), primary_key=True)
    name: Column[str] = column(sa.String(50), nullable=False)
    description: Column[str] = column(sa.String(250), nullable=True)
    price: Column[int] = column(sa.Integer(), nullable=False)

    _v4a_id: Column[int] = column(sa.ForeignKey("v4a.id"), nullable=False)
    v4a: Relationship[V4A] = many_to_one("V4A.pricings")

    tickets: Relationship[list[V4ATicket]] = one_to_many("V4ATicket.pricing")

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<V4A Pricing #{self.id} ('{self.name}')>"

    def __str__(self) -> str:
        """Human-readible description of the V4A."""
        return self.name

class V4ATicket(Model):
    """Tickets for V4A"""

    __tablename__ = "v4a_ticket"
    id: Column[int] = column(sa.Integer(), primary_key=True)
    first_name: Column[str] = column(sa.String(100), nullable=False)
    last_name: Column[str] = column(sa.String(100), nullable=False)
    email: Column[str] = column(sa.String(250), nullable=False)
    phone_number: Column[str] = column(sa.String(20), nullable=False)
    date: Column[datetime.datetime] = column(sa.DateTime(), nullable=False)

    _representation_id: Column[int] = column(sa.ForeignKey("v4a_representation.id"), nullable=False)
    representation: Relationship[V4ARepresentation] = many_to_one("V4ARepresentation.tickets")

    _pricing_id: Column[int] = column(sa.ForeignKey("v4a_pricing.id"), nullable=False)
    pricing: Relationship[V4APricing] = many_to_one("V4APricing.tickets")

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<V4A Ticket #{self.id} ('{self.first_name}')>"

    def __str__(self) -> str:
        """Human-readible description of the V4A."""
        return self.name


from app import models