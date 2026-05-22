"""PC est magique Flask App - Information Banner Models"""

from __future__ import annotations
import datetime
import typing
import sqlalchemy as sa
from sqlalchemy.orm import Mapped
from app import db
from app.utils.columns import (
    column,
    many_to_one,
    one_to_many,
    Column,
)

class BannerStyleMixin:
    """Mixin for styling columns shared by preset and banner."""
    background_color: Mapped[str] = column(sa.String(7), nullable=False, default="#152f4e")
    text_color: Mapped[str] = column(sa.String(7), nullable=False, default="#ffffff")
    icon: Mapped[str | None] = column(sa.String(64), nullable=True)
    text_alignment: Mapped[str] = column(sa.String(16), nullable=False, default="center")
    layout_style: Mapped[str] = column(sa.String(16), nullable=False, default="vertical")
    overlay_opacity: Mapped[int] = column(sa.Integer(), nullable=False, default=70)
    image_filename: Mapped[str | None] = column(sa.String(128), nullable=True)


class InfoBannerPreset(BannerStyleMixin, db.Model):
    """Presets of style and icons for info banners."""

    __tablename__ = "info_banner_preset"

    id: Column[int] = column(sa.Integer(), primary_key=True)
    name: Column[str] = column(sa.String(64), nullable=False, unique=True)
    banners: Mapped[list[InfoBanner]] = one_to_many("InfoBanner.preset")

    def __repr__(self) -> str:
        return f"<InfoBannerPreset #{self.id} ('{self.name}')>"


class InfoBanner(BannerStyleMixin, db.Model):
    """Banners and text alerts shown on the homepage."""

    __tablename__ = "info_banner"

    id: Column[int] = column(sa.Integer(), primary_key=True)
    title: Column[str] = column(sa.String(128), nullable=False)
    is_text: Column[bool] = column(sa.Boolean(), default=False, nullable=False)
    text_content: Column[str | None] = column(sa.Text(), nullable=True)
    
    _preset_id: Column[int | None] = column(sa.ForeignKey("info_banner_preset.id", ondelete="SET NULL"), nullable=True)
    preset: Mapped[InfoBannerPreset | None] = many_to_one("InfoBannerPreset.banners", foreign_keys=[_preset_id])
    
    link_url: Column[str | None] = column(sa.String(512), nullable=True)
    file_filename: Column[str | None] = column(sa.String(128), nullable=True)
    file_original_name: Column[str | None] = column(sa.String(128), nullable=True)
    order_index: Column[int] = column(sa.Integer(), default=0, nullable=False)
    created_at: Column[datetime.datetime] = column(sa.DateTime(), default=datetime.datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<InfoBanner #{self.id} ('{self.title}')>"

