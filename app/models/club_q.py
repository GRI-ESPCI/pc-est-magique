"""PC est magique Flask App - Club Q Models"""

from __future__ import annotations
from app import models

import datetime
import typing

import sqlalchemy as sa
import flask
from app.utils.nginx import get_nginx_access_token
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
    debut: Column[datetime.date | None] = column(sa.Date(), nullable=True)
    fin: Column[datetime.date | None] = column(sa.Date(), nullable=True)
    fin_inscription: Column[datetime.date | None] = column(sa.Date(), nullable=True)
    spectacles: Relationship[list[ClubQSpectacle]] = one_to_many(
        "ClubQSpectacle.season", order_by="ClubQSpectacle.date"
    )
    voeu: Relationship[list[ClubQVoeu]] = one_to_many("ClubQVoeu.season", order_by="ClubQVoeu.id")
    brochure: Relationship[list[ClubQBrochure]] = one_to_many("ClubQBrochure.season", order_by="ClubQBrochure.id")

    @property
    def sum_places_demandees(self) -> int:
        """The sum of all the places asked in a season"""
        return sum(spect.sum_places_demandees for spect in ClubQSpectacle.query.filter_by(_season_id=self.id))

    @property
    def sum_places_attribuees(self) -> int:
        """The sum of all the places asked in a season"""
        return sum(spect.sum_places_attribuees for spect in ClubQSpectacle.query.filter_by(_season_id=self.id))


class ClubQSalle(db.Model):
    """Informations about Club Q spectacle places"""

    __tablename__ = "club_q_salle"
    id: Column[int] = column(sa.Integer(), primary_key=True)
    nom: Column[str] = column(sa.String(64), nullable=False)
    description: Column[str | None] = column(sa.String(500), nullable=True)
    url: Column[str | None] = column(sa.String(64), nullable=True)
    adresse: Column[str | None] = column(sa.String(64), nullable=True)
    latitude: Column[float] = column(sa.Float(), default=0, nullable=False)
    longitude: Column[float] = column(sa.Float(), default=0, nullable=False)
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
        return sum(v.places_demandees for v in self.voeu.filter_by(_season_id=self._season_id))

    @property
    def sum_places_attribuees(self) -> int:
        """The number of tickets asked for a spectacle"""
        return sum(v.places_attribuees for v in self.voeu.filter_by(_season_id=self._season_id))

    @property
    def src(self) -> int:
        """Image path for club q images"""
        return f"/club_q_images/{self.season.id}/{self.id}.jpg"


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


class ClubQBrochure(db.Model):
    """Bekk registration information"""

    id: Column[int] = column(sa.Integer(), primary_key=True)

    _season_id: Column[int] = column(sa.ForeignKey("club_q_season.id"), nullable=False)
    season: Relationship[ClubQSeason] = many_to_one("ClubQSeason.brochure")

    @property
    def src(self) -> str:
        """The online path to the pdf."""
        return f"/club_q_plaquettes/{self.id}.pdf"

    @property
    def pdf_src_with_token(self) -> str:
        """The online query to the pdf with md5 args."""
        ip = flask.request.headers.get("X-Real-Ip") or flask.current_app.config["FORCE_IP"]
        token_args = get_nginx_access_token("/club_q_plaquettes", ip)
        return f"{self.src}?{token_args}"
