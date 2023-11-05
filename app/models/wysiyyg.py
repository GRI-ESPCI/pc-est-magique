"""PC est magique Flask App - Club Q Models"""

from __future__ import annotations
from app import models

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


class Files(db.Model):
    """WYSIWYG Files saving"""

    __tablename__ = "Files"
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
