"""PC est magique Flask App - Club Q Models"""

from __future__ import annotations
from app import models

import datetime
import typing

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Mapped, WriteOnlyMapped
import flask
from app.utils.nginx import get_nginx_access_token
from app import db
from app.utils.columns import (
    column,
    one_to_many,
    many_to_one,
    Column,
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
    attributions_visible: Column[bool] = column(sa.Boolean(), default=False, nullable=False)

    spectacles: Mapped[list["models.ClubQSpectacle"]] = one_to_many("ClubQSpectacle.season", order_by="ClubQSpectacle.date")
    voeu: WriteOnlyMapped["models.ClubQVoeu"] = one_to_many("ClubQVoeu.season", lazy="write_only")
    brochure: Mapped[list["models.ClubQBrochure"]] = one_to_many("ClubQBrochure.season", order_by="ClubQBrochure.id")
    payments: Mapped[list["models.ClubQPayment"]] = one_to_many("ClubQPayment.season", cascade="all, delete-orphan")
    salle_respos: Mapped[list["models.ClubQSalleRespo"]] = one_to_many("ClubQSalleRespo.season", cascade="all, delete-orphan")

    @classmethod
    def default_order(cls) -> tuple:
        """Consistent ordering for Club Q seasons (most recent promo/date first, NULL dates last)."""
        return (
            cls.promo_orga.desc(),
            sa.func.coalesce(cls.debut, cls.fin).desc().nullslast(),
            cls.id.desc(),
        )

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
    spectacles: Mapped[list["models.ClubQSpectacle"]] = one_to_many("ClubQSpectacle.salle", order_by="ClubQSpectacle.date")
    respos: Mapped[list["models.ClubQSalleRespo"]] = one_to_many("ClubQSalleRespo.salle", cascade="all, delete-orphan")


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

    voeu: WriteOnlyMapped["models.ClubQVoeu"] = one_to_many("ClubQVoeu.spectacle", lazy="write_only")

    _season_id: Column[int] = column(sa.ForeignKey("club_q_season.id"), nullable=False)
    season: Mapped[ClubQSeason] = many_to_one("ClubQSeason.spectacles")

    _salle_id: Column[int] = column(sa.ForeignKey("club_q_salle.id"), nullable=False)
    salle: Mapped[ClubQSalle] = many_to_one("ClubQSalle.spectacles")

    @property
    def sum_places_demandees(self) -> int:
        """The number of tickets asked for a spectacle"""
        stmt = sa.select(sa.func.sum(ClubQVoeu.places_demandees)).where(
            ClubQVoeu._spectacle_id == self.id,
            ClubQVoeu._season_id == self._season_id
        )
        return db.session.scalar(stmt) or 0

    @property
    def sum_places_attribuees(self) -> int:
        """The number of tickets asked for a spectacle"""
        stmt = sa.select(sa.func.sum(ClubQVoeu.places_attribuees)).where(
            ClubQVoeu._spectacle_id == self.id,
            ClubQVoeu._season_id == self._season_id
        )
        return db.session.scalar(stmt) or 0


class ClubQVoeu(db.Model):
    """Client wish for a spectacle"""

    __tablename__ = "club_q_voeu"
    __table_args__ = (sa.UniqueConstraint("_pceen_id", "_spectacle_id", name="uq_club_q_voeu_pceen_spectacle"),)

    id: Column[int] = column(sa.Integer(), primary_key=True)
    places_demandees: Column[int] = column(sa.Integer(), nullable=False)
    priorite: Column[int] = column(sa.Integer(), nullable=False)
    places_minimum: Column[int | None] = column(sa.Integer(), nullable=True)
    places_attribuees: Column[int | None] = column(sa.Integer(), nullable=True)

    _pceen_id: Column[int] = column(sa.ForeignKey("pceen.id"), nullable=False)
    pceen: Mapped[models.PCeen] = many_to_one("PCeen.clubq_voeux", foreign_keys=[_pceen_id])

    _spectacle_id: Column[int] = column(sa.ForeignKey("club_q_spectacle.id"), nullable=False)
    spectacle: Mapped[ClubQSeason] = many_to_one("ClubQSpectacle.voeu")

    _season_id: Column[int] = column(sa.ForeignKey("club_q_season.id"), nullable=False)
    season: Mapped[ClubQSeason] = many_to_one("ClubQSeason.voeu")


class ClubQBrochure(db.Model):
    """Bekk registration information"""

    id: Column[int] = column(sa.Integer(), primary_key=True)

    _season_id: Column[int] = column(sa.ForeignKey("club_q_season.id"), nullable=False)
    season: Mapped[ClubQSeason] = many_to_one("ClubQSeason.brochure")

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


class ClubQPayment(db.Model):
    """Tracks whether a PCeen has paid for a given Club Q season"""

    __tablename__ = "club_q_payment"
    __table_args__ = (
        sa.UniqueConstraint("_pceen_id", "_season_id", name="uq_club_q_payment_pceen_season"),
        sa.Index("ix_club_q_payment_season_id", "_season_id"),
    )

    id: Column[int] = column(sa.Integer(), primary_key=True)
    paid: Column[bool] = column(sa.Boolean(), default=False, server_default=sa.false(), nullable=False)

    _pceen_id: Column[int] = column(sa.ForeignKey("pceen.id", ondelete="CASCADE"), nullable=False)
    _season_id: Column[int] = column(sa.ForeignKey("club_q_season.id", ondelete="CASCADE"), nullable=False)

    pceen: Mapped[models.PCeen] = many_to_one("PCeen.clubq_payments")
    season: Mapped[ClubQSeason] = many_to_one("ClubQSeason.payments")

    @classmethod
    def paid_pceen_ids(cls, season_id: int) -> set[int]:
        """Return the set of PCeen IDs marked as paid for a given season."""
        return set(
            db.session.scalars(
                db.select(cls._pceen_id).filter_by(_season_id=season_id, paid=True)
            ).all()
        )

    @classmethod
    def is_paid(cls, pceen_id: int, season_id: int) -> bool:
        """Return whether a specific PCeen is marked as paid for a given season."""
        return bool(
            db.session.scalar(
                db.select(cls.paid).filter_by(_pceen_id=pceen_id, _season_id=season_id)
            )
        )

    @classmethod
    def set_paid(cls, pceen_id: int, season_id: int, paid: bool) -> None:
        """Upsert the payment status for a (pceen, season) pair."""
        stmt = pg_insert(cls).values(_pceen_id=pceen_id, _season_id=season_id, paid=paid)
        db.session.execute(
            stmt.on_conflict_do_update(constraint="uq_club_q_payment_pceen_season", set_={"paid": stmt.excluded.paid})
        )


class ClubQSalleRespo(db.Model):
    """Respo salle assigned to a Club Q venue for a specific season"""

    __tablename__ = "club_q_salle_respo"
    __table_args__ = (
        sa.UniqueConstraint("_salle_id", "_season_id", name="uq_club_q_salle_respo_salle_season"),
        sa.Index("ix_club_q_salle_respo_pceen_season", "_pceen_id", "_season_id"),
        sa.Index("ix_club_q_salle_respo_season_id", "_season_id"),
    )

    id: Column[int] = column(sa.Integer(), primary_key=True)
    _salle_id: Column[int] = column(sa.ForeignKey("club_q_salle.id", ondelete="CASCADE"), nullable=False)
    _season_id: Column[int] = column(sa.ForeignKey("club_q_season.id", ondelete="CASCADE"), nullable=False)
    _pceen_id: Column[int] = column(sa.ForeignKey("pceen.id", ondelete="CASCADE"), nullable=False)

    salle: Mapped[ClubQSalle] = many_to_one("ClubQSalle.respos")
    season: Mapped[ClubQSeason] = many_to_one("ClubQSeason.salle_respos")
    pceen: Mapped[models.PCeen] = many_to_one("PCeen.clubq_salle_respos")

    @classmethod
    def respos_by_salle(cls, season_id: int) -> dict[int, "ClubQSalleRespo"]:
        rows = db.session.scalars(
            db.select(cls).options(sa.orm.selectinload(cls.pceen)).filter_by(_season_id=season_id)
        ).all()
        return {row._salle_id: row for row in rows}

    @classmethod
    def salle_ids_for(cls, pceen_id: int, season_id: int) -> set[int]:
        return set(
            db.session.scalars(
                db.select(cls._salle_id).filter_by(_pceen_id=pceen_id, _season_id=season_id)
            ).all()
        )

    @classmethod
    def season_ids_for(cls, pceen_id: int, *, visible_only: bool = False) -> set[int]:
        stmt = db.select(cls._season_id).filter_by(_pceen_id=pceen_id)
        if visible_only:
            stmt = stmt.join(ClubQSeason, cls._season_id == ClubQSeason.id).filter(
                ClubQSeason.attributions_visible.is_(True)
            )
        return set(db.session.scalars(stmt).all())

    @classmethod
    def is_respo_for(cls, pceen_id: int, salle_id: int, season_id: int) -> bool:
        return (
            db.session.scalar(
                db.select(cls.id).filter_by(_pceen_id=pceen_id, _salle_id=salle_id, _season_id=season_id)
            )
            is not None
        )

    @classmethod
    def get(cls, salle_id: int, season_id: int) -> "ClubQSalleRespo | None":
        """Return the Respo salle (with its PCeen loaded) for a (salle, season) pair."""
        return db.session.scalars(
            db.select(cls).options(sa.orm.selectinload(cls.pceen)).filter_by(_salle_id=salle_id, _season_id=season_id)
        ).one_or_none()

    @classmethod
    def set_respo(cls, salle_id: int, season_id: int, pceen_id: int) -> None:
        """Assign or update the Respo salle for a (salle, season) pair."""
        stmt = pg_insert(cls).values(_salle_id=salle_id, _season_id=season_id, _pceen_id=pceen_id)
        db.session.execute(
            stmt.on_conflict_do_update(
                constraint="uq_club_q_salle_respo_salle_season", set_={"_pceen_id": stmt.excluded._pceen_id}
            )
        )

    @classmethod
    def clear_respo(cls, salle_id: int, season_id: int) -> bool:
        """Remove the Respo salle for a (salle, season) pair. Return True if one existed."""
        result = db.session.execute(db.delete(cls).filter_by(_salle_id=salle_id, _season_id=season_id))
        return bool(result.rowcount)
