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


class Client(db.Model):
    """Clients of the Club Q"""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    mecontentement: Column[float] = column(sa.Float(), nullable=False)
    mecontentement_precedent: Column[float | None] = column(sa.Float(), nullable=False)
    saison_actuelle_mec: Column[int] = column(sa.Integer(), nullable=False)
    a_payer: Column[float] = column(sa.Float(), nullable=False)

    voeux: Relationship[list[Voeux]] = one_to_many("Voeux.client", order_by="Voeux.id")


class Season(db.Model):
    """Informations about Club Q Seasons"""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    nom: Column[str] = column(sa.String(64), nullable=False)
    promo_orga: Column[int] = column(sa.Integer(), nullable=False)
    debut: Column[datetime.datetime | None] = column(sa.DateTime(), nullable=True)
    fin: Column[datetime.datetime | None] = column(sa.DateTime(), nullable=True)
    fin_inscription: Column[datetime.datetime | None] = column(sa.DateTime(), nullable=True)

    spectacles: Relationship[list[Spectacle]] = one_to_many("Spectacle.season", order_by="Spectacle.date")


class Salle(db.Model):
    """Informations about Club Q spectacle places"""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    nom: Column[str] = column(sa.String(64), nullable=False)
    description: Column[str | None] = column(sa.String(500), nullable=True)
    url: Column[str | None] = column(sa.String(64), nullable=True)
    adresse: Column[str | None] = column(sa.String(64), nullable=True)
    latitude: Column[float | None] = column(sa.Float(), nullable=True)
    lontitude: Column[float | None] = column(sa.Float(), nullable=True)

    spectacles: Relationship[list[Spectacle]] = one_to_many("Spectacle.salle", order_by="Spectacle.date")


class Spectacle(db.Model):
    """Spectacles dates of representations"""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    nom: Column[str] = column(sa.String(64), nullable=False)
    categorie: Column[str | None] = column(sa.String(64), nullable=True)
    description: Column[str | None] = column(sa.String(500), nullable=True)
    date: Column[datetime.datetime] = column(sa.DateTime(), nullable=False)
    nb_tickets: Column[int] = column(sa.Integer(), nullable=False)
    unit_price: Column[float] = column(sa.Float(), nullable=False)

    _season_id: Column[int] = column(sa.ForeignKey("season.id"), nullable=False)
    season: Relationship[Season] = many_to_one("Season.spectacles")

    _salle_id: Column[int] = column(sa.ForeignKey("salle.id"), nullable=False)
    salle: Relationship[Salle] = many_to_one("Salle.spectacles")
    
    voeux: Relationship[list[Voeux]] = one_to_many("Voeux.spectacle", order_by="Voeux.id")



class Voeux(db.Model):
    """Spectacles dates of representations"""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    places_demandees: Column[int] = column(sa.Integer(), nullable=False)
    priorite: Column[int] = column(sa.Integer(), nullable=False)
    places_minimum: Column[int | None] = column(sa.Integer(), nullable=True)
    places_attribuees: Column[int | None] = column(sa.Integer(), nullable=True)

    _client_id: Column[int] = column(sa.ForeignKey("client.id"), nullable=False)
    client: Relationship[Season] = many_to_one("Client.voeux")

    _spectacle_id: Column[int] = column(sa.ForeignKey("spectacle.id"), nullable=False)
    spectacle: Relationship[Season] = many_to_one("Spectacle.voeux")


from app import models
