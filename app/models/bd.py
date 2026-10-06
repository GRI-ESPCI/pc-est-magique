"""PC est magique Flask App - BD (Bandes Dessinées) Models"""

from __future__ import annotations

import typing

import sqlalchemy as sa

from app import db
from app.utils.columns import column, Column


Model = typing.cast(type[type], db.Model)  # type checking hack


class BDItem(db.Model):
    """An item in the BD club catalog (livre ou bande dessinée)."""

    __tablename__ = "bd_item"

    id: Column[int] = column(sa.Integer(), primary_key=True)
    auteurs: Column[str] = column(sa.String(500), nullable=False)
    titre: Column[str] = column(sa.String(500), nullable=False)
    date_publication: Column[str | None] = column(sa.String(50), nullable=True)
    editeur: Column[str | None] = column(sa.String(200), nullable=True)
    pages: Column[int | None] = column(sa.Integer(), nullable=True)
    isbn: Column[str | None] = column(sa.String(20), nullable=True, index=True)
    # "livre" or "bd"
    categorie: Column[str] = column(sa.String(20), nullable=False, default="bd")
    resume: Column[str | None] = column(sa.Text, nullable=True)
    image_url: Column[str | None] = column(sa.String(500), nullable=True)

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<BDItem #{self.id} ({self.titre!r})>"

    @property
    def cover_url(self) -> str | None:
        """Open Library cover URL based on ISBN, or None if no ISBN."""
        if self.image_url:
            return self.image_url
        if self.isbn:
            clean = self.isbn.replace("-", "").replace(" ", "")
            if clean:
                return f"https://covers.openlibrary.org/b/isbn/{clean}-M.jpg?default=false"
        return None


from app import models  # noqa: E402, F401
