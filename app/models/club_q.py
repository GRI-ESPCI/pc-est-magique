"""PC est magique Flask App - Club Q Models"""

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


class ClubQClient(db.Model):
    """Clients of the Club Q"""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    mecontentement: Column[float] = column(sa.Float(), nullable=False)
    mecontentement_precedent: Column[float | None] = column(sa.Float(), nullable=False)
    saison_actuelle_mec: Column[int] = column(sa.Integer(), nullable=False)
    a_payer: Column[float] = column(sa.Float(), nullable=False)

#    voeux: Relationship[list[ClubQVoeux]] = one_to_many("ClubQVoeux.client", order_by="ClubQVoeux.id")


class ClubQSeason(db.Model):
    """Informations about Club Q Seasons"""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    nom: Column[str] = column(sa.String(64), nullable=False)
    promo_orga: Column[int] = column(sa.Integer(), nullable=False)
    debut: Column[datetime.datetime | None] = column(sa.DateTime(), nullable=True)
    fin: Column[datetime.datetime | None] = column(sa.DateTime(), nullable=True)
    fin_inscription: Column[datetime.datetime | None] = column(sa.DateTime(), nullable=True)

#    spectacles: Relationship[list[ClubQSpectacle]] = one_to_many("ClubQSpectacle.season", order_by="ClubQSpectacle.date")


class ClubQSalle(db.Model):
    """Informations about Club Q spectacle places"""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    nom: Column[str] = column(sa.String(64), nullable=False)
    description: Column[str | None] = column(sa.String(500), nullable=True)
    url: Column[str | None] = column(sa.String(64), nullable=True)
    adresse: Column[str | None] = column(sa.String(64), nullable=True)
    latitude: Column[float | None] = column(sa.Float(), nullable=True)
    lontitude: Column[float | None] = column(sa.Float(), nullable=True)

#    spectacles: Relationship[list[ClubQSpectacle]] = one_to_many("ClubQSpectacle.salle", order_by="ClubQSpectacle.date")


class ClubQSpectacle(db.Model):
    """Spectacles dates of representations"""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    nom: Column[str] = column(sa.String(64), nullable=False)
    categorie: Column[str | None] = column(sa.String(64), nullable=True)
    description: Column[str | None] = column(sa.String(500), nullable=True)
    date: Column[datetime.datetime] = column(sa.DateTime(), nullable=False)
    nb_tickets: Column[int] = column(sa.Integer(), nullable=False)
    unit_price: Column[float] = column(sa.Float(), nullable=False)

#    _season_id: Column[int] = column(sa.ForeignKey("season.id"), nullable=False)
#    season: Relationship[ClubQSeason] = many_to_one("ClubQSeason.spectacles")

#    _salle_id: Column[int] = column(sa.ForeignKey("salle.id"), nullable=False)
#    salle: Relationship[ClubQSalle] = many_to_one("ClubQSalle.spectacles")
    
#    voeux: Relationship[list[ClubQVoeux]] = one_to_many("ClubQVoeux.spectacle", order_by="ClubQVoeux.id")



class ClubQVoeux(db.Model):
    """List of spectacle wishes"""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    places_demandees: Column[int] = column(sa.Integer(), nullable=False)
    priorite: Column[int] = column(sa.Integer(), nullable=False)
    places_minimum: Column[int | None] = column(sa.Integer(), nullable=True)
    places_attribuees: Column[int | None] = column(sa.Integer(), nullable=True)

#    _client_id: Column[int] = column(sa.ForeignKey("client.id"), nullable=False)
#    client: Relationship[ClubQClient] = many_to_one("ClubQClient.voeux")

#    _spectacle_id: Column[int] = column(sa.ForeignKey("spectacle.id"), nullable=False)
#    spectacle: Relationship[ClubQSeason] = many_to_one("ClubQSpectacle.voeux")


from app import models