"""PC est magique Flask App - Jeux Models"""

from __future__ import annotations

import datetime

import flask
from flask_babel import _
import sqlalchemy as sa
from sqlalchemy.orm import Mapped

from app import db
from app.utils.columns import column, many_to_one, one_to_many, Column


def _utcnow() -> datetime.datetime:
    """Return current UTC datetime as naive datetime (for DB storage)."""
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)


class JeuItem(db.Model):
    """An item in the Jeux club catalog (jeu de société, jeu de rôles, etc.)."""

    __tablename__ = "jeu_item"

    id: Column[int] = column(sa.Integer(), primary_key=True)
    nom: Column[str] = column(sa.String(500), nullable=False)
    categorie: Column[str] = column(sa.String(100), nullable=False, default="Autres")
    temps_de_jeu: Column[str | None] = column(sa.String(100), nullable=True)
    nb_joueurs: Column[str | None] = column(sa.String(100), nullable=True)
    popularite: Column[str | None] = column(sa.String(100), nullable=True)
    commentaires: Column[str | None] = column(sa.Text, nullable=True)
    resume: Column[str | None] = column(sa.Text, nullable=True)
    image_url: Column[str | None] = column(sa.String(500), nullable=True)
    image_filename: Column[str | None] = column(sa.String(255), nullable=True)
    nota_bene: Column[str | None] = column(sa.Text, nullable=True)

    reservations: Mapped[list["JeuReservation"]] = one_to_many(
        "JeuReservation.jeu",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<JeuItem #{self.id} ({self.nom!r})>"

    @property
    def cover_url(self) -> str | None:
        """Return the cover URL (uploaded image first, then external URL)."""
        if self.image_filename:
            return flask.url_for("jeux.serve_cover", filename=self.image_filename)
        if self.image_url:
            return self.image_url
        return None

    @property
    def active_reservation(self) -> JeuReservation | None:
        """Return the currently active reservation for this game, if any."""
        today = datetime.date.today()
        for res in self.reservations:
            if not res.cancelled and res.end_date >= today:
                return res
        return None


class JeuReservation(db.Model):
    """A reservation of a game by a PCeen."""

    __tablename__ = "jeu_reservation"

    id: Column[int] = column(sa.Integer(), primary_key=True)
    _jeu_id: Column[int] = column(
        sa.ForeignKey("jeu_item.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    jeu: Mapped[JeuItem] = many_to_one("JeuItem.reservations")

    _pceen_id: Column[int] = column(
        sa.ForeignKey("pceen.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pceen: Mapped["models.PCeen"] = many_to_one("PCeen.jeu_reservations")

    start_date: Column[datetime.date] = column(sa.Date(), nullable=False)
    end_date: Column[datetime.date] = column(sa.Date(), nullable=False)
    created_at: Column[datetime.datetime] = column(
        sa.DateTime(),
        nullable=False,
        default=_utcnow,
    )
    cancelled: Column[bool] = column(sa.Boolean(), nullable=False, default=False)

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<JeuReservation #{self.id} jeu={self._jeu_id} pceen={self._pceen_id} ({self.start_date} -> {self.end_date})>"

    @property
    def calendar_title(self) -> str:
        """Calendar event title for this reservation's end date."""
        nom = self.jeu.nom if self.jeu else ""
        return str(_("Fin de réservation : %(nom)s", nom=nom))

    @property
    def calendar_location(self) -> str:
        """Calendar event location for a game reservation."""
        return str(_("Armoire à jeux"))

    @property
    def calendar_description(self) -> str:
        """Calendar event description for this reservation's end date."""
        nom = self.jeu.nom if self.jeu else ""
        return str(
            _(
                "La réservation du jeu « %(nom)s » (du %(start)s au %(end)s) se termine ce jour.",
                nom=nom,
                start=self.start_date.strftime("%d/%m/%Y"),
                end=self.end_date.strftime("%d/%m/%Y"),
            )
        )

    @staticmethod
    def get_club_display_info() -> tuple[int | None, str, str, str]:
        """Return (club_id, name, color, contrast_color) for Club Jeux."""
        from app.models.calendar import Club

        club_jeux = db.session.scalars(
            db.select(Club).where(Club.name.in_(["Club Jeux", "Jeux"]))
        ).first()
        if club_jeux:
            return (
                club_jeux.id,
                club_jeux.name,
                club_jeux.color or "#e67e22",
                club_jeux.get_contrast_color(),
            )
        return None, "Club Jeux", "#e67e22", "#ffffff"


from app import models
