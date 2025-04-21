"""PC est magique Flask App - Theater Models"""

from __future__ import annotations

import datetime
import typing

import sqlalchemy as sa

from app import db
from app.utils.columns import (
    column,
    one_to_many,
    many_to_one,
    Column,
    Relationship,
)


Model = typing.cast(type[type], db.Model)  # type checking hack


class Saison(db.Model):
    """Store data about one season of theatre club"""
    id: Column[int] = column(sa.Integer(), primary_key=True)
    name: Column[str] = column(sa.String(120), nullable=False)
    description: Column[str | None] = column(sa.String(2000), nullable=True)
    image_name: Column[str | None] = column(sa.String(120), nullable=True)
    start_date: Column[date] = column(sa.Date(), nullable=False)

    spectacles: Relationship[list[Representation]] = one_to_many(
        "Spectacle.saison"
    )


class Spectacle(db.Model):
    """All information about ESPCI theatre spectacle information."""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    name: Column[str] = column(sa.String(120), nullable=False)
    year: Column[int] = column(sa.Integer(), nullable=False)
    description: Column[str | None] = column(sa.String(2000), nullable=True)
    ticket_link: Column[str | None] = column(sa.String(120), nullable=True)
    director: Column[str | None] = column(sa.String(64), nullable=True)
    author: Column[str | None] = column(sa.String(64), nullable=True)
    image_name: Column[str | None] = column(sa.String(120), nullable=True)
    places: Column[str | None] = column(sa.String(255), nullable=True)

    _saison_id: Column[int] = column(sa.ForeignKey("saison.id"), nullable=False)
    saison: Relationship[Saison] = many_to_one("Saison.spectacles")

    representations: Relationship[list[Representation]] = one_to_many(
        "Representation.spectacle", order_by="Representation.date"
    )


class Representation(db.Model):
    """Spectacles dates of representations"""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    date: Column[datetime.datetime] = column(sa.DateTime(), nullable=False)

    _spectacle_id: Column[int] = column(sa.ForeignKey("spectacle.id"), nullable=False)
    spectacle: Relationship[Spectacle] = many_to_one("Spectacle.representations")


from app import models
