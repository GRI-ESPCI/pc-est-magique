"""PC est magique Flask App - Club Q Models"""

from __future__ import annotations
from app import models

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


class ClubQSeason(db.Model):
    """Informations about Club Q Seasons"""

    __tablename__ = "club_q_season"
    id: Column[int] = column(sa.Integer(), primary_key=True)
    nom: Column[str] = column(sa.String(64), nullable=False)
    promo_orga: Column[int] = column(sa.Integer(), nullable=False)
    debut: Column[datetime.datetime | None] = column(sa.DateTime(), nullable=True)
    fin: Column[datetime.datetime | None] = column(sa.DateTime(), nullable=True)
    fin_inscription: Column[datetime.datetime | None] = column(sa.DateTime(), nullable=True)
    spectacles: Relationship[list[ClubQSpectacle]] = one_to_many(
        "ClubQSpectacle.season", order_by="ClubQSpectacle.date"
    )
    voeu: Relationship[list[ClubQVoeu]] = one_to_many("ClubQVoeu.season", order_by="ClubQVoeu.id")


class ClubQSalle(db.Model):
    """Informations about Club Q spectacle places"""

    __tablename__ = "club_q_salle"
    id: Column[int] = column(sa.Integer(), primary_key=True)
    nom: Column[str] = column(sa.String(64), nullable=False)
    description: Column[str | None] = column(sa.String(500), nullable=True)
    url: Column[str | None] = column(sa.String(64), nullable=True)
    adresse: Column[str | None] = column(sa.String(64), nullable=True)
    latitude: Column[float | None] = column(sa.Float(), nullable=True)
    longitude: Column[float | None] = column(sa.Float(), nullable=True)
    spectacles: Relationship[list[ClubQSpectacle]] = one_to_many("ClubQSpectacle.salle", order_by="ClubQSpectacle.date")


class ClubQSpectacle(db.Model):
    """Spectacles dates of representations"""

    __tablename__ = "club_q_spectacle"
    id: Column[int] = column(sa.Integer(), primary_key=True)
    nom: Column[str] = column(sa.String(64), nullable=False)
    categorie: Column[str | None] = column(sa.String(64), nullable=True)
    image_name: Column[str | None] = column(sa.String(64), nullable=True)
    description: Column[str | None] = column(sa.String(2500), nullable=True)
    date: Column[datetime.datetime] = column(sa.DateTime(), nullable=False)
    nb_tickets: Column[int] = column(sa.Integer(), nullable=False)
    unit_price: Column[float] = column(sa.Float(), nullable=False)

    voeu: Relationship[list[ClubQVoeu]] = one_to_many("ClubQVoeu.spectacle", order_by="ClubQVoeu.id", lazy="dynamic")

    _season_id: Column[int] = column(sa.ForeignKey("club_q_season.id"), nullable=False)
    season: Relationship[ClubQSeason] = many_to_one("ClubQSeason.spectacles")

    _salle_id: Column[int] = column(sa.ForeignKey("club_q_salle.id"), nullable=False)
    salle: Relationship[ClubQSalle] = many_to_one("ClubQSalle.spectacles")

    @property
    def sum_places_demandees(self) -> int:
        """The number of tickets asked for a spectacle"""
        return sum(v.places_demandees for v in self.voeu.filter_by(_season_id = models.GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value))
    
    @property
    def sum_places_attribuees(self) -> int:
        """The number of tickets asked for a spectacle"""
        return sum(v.places_attribuees for v in self.voeu.filter_by(_season_id = models.GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value).all())

    
class ClubQVoeu(db.Model):
    """Client wish for a spectacle"""

    __tablename__ = "club_q_voeu"
    id: Column[int] = column(sa.Integer(), primary_key=True)
    places_demandees: Column[int] = column(sa.Integer(), nullable=False)
    priorite: Column[int] = column(sa.Integer(), nullable=False)
    places_minimum: Column[int | None] = column(sa.Integer(), nullable=True)
    places_attribuees: Column[int | None] = column(sa.Integer(), nullable=True)

    _pceen_id: Column[int] = column(sa.ForeignKey("pceen.id"), nullable=False)
    pceen: Relationship[models.PCeen] = many_to_one("PCeen.clubq_voeux", foreign_keys=[_pceen_id])

    _spectacle_id: Column[int] = column(sa.ForeignKey("club_q_spectacle.id"), nullable=False)
    spectacle: Relationship[ClubQSeason] = many_to_one("ClubQSpectacle.voeu")

    _season_id: Column[int] = column(sa.ForeignKey("club_q_season.id"), nullable=False)
    season: Relationship[ClubQSeason] = many_to_one("ClubQSeason.voeu")
