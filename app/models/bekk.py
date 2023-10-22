"""PC est magique Flask App - Bekk Models"""

from __future__ import annotations
from app import models

import datetime
import typing

import sqlalchemy as sa

from app import db
from app.utils.columns import (
    column,
    Column,
)
from app.utils.nginx import get_nginx_access_token
import flask


Model = typing.cast(type[type], db.Model)  # type checking hack


class Bekk(db.Model):
    """Bekk registration information"""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    name: Column[str] = column(sa.String(120), nullable=False)
    promo: Column[int] = column(sa.Integer(), nullable=False)
    date: Column[datetime.date] = column(sa.Date(), nullable=False)

    @property
    def src(self) -> str:
        """The online path to the pdf."""
        return f"/bekks/{self.id}.pdf"

    @property
    def pdf_src_with_token(self) -> str:
        """The online query to the pdf with md5 args."""
        ip = flask.request.headers.get("X-Real-Ip") or flask.current_app.config["FORCE_IP"]
        token_args = get_nginx_access_token(self.src, ip)
        return f"/bekks?{token_args}"
