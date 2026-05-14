"""PC est magique Flask App - Calendar Models"""

from __future__ import annotations

import datetime
import typing

import sqlalchemy as sa
from sqlalchemy.orm import Mapped

from app import db, models
from app.utils.columns import (
    column,
    one_to_many,
    many_to_one,
    Column,
)

Model = typing.cast(type[type], db.Model)  # type checking hack

class Club(db.Model):
    """A club that calendar events can be attributed to."""

    __tablename__ = "club"
    id: Column[int] = column(sa.Integer(), primary_key=True)
    name: Column[str] = column(sa.String(64), nullable=False, unique=True)
    color: Column[str] = column(sa.String(7), nullable=False, default="#000000")
    
    events: Mapped[list[Event]] = one_to_many("Event.club", order_by="Event.start_time", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Club #{self.id} ({self.name})>"

    def __str__(self) -> str:
        return self.name


class Event(db.Model):
    """An event in the calendar."""

    __tablename__ = "event"
    id: Column[int] = column(sa.Integer(), primary_key=True)
    title: Column[str] = column(sa.String(128), nullable=False)
    description: Column[str | None] = column(sa.Text(), nullable=True)
    location: Column[str | None] = column(sa.String(128), nullable=True)
    start_time: Column[datetime.datetime] = column(sa.DateTime(), nullable=False)
    end_time: Column[datetime.datetime] = column(sa.DateTime(), nullable=False)
    all_day: Column[bool] = column(sa.Boolean(), default=False, nullable=False)

    _author_id: Column[int] = column(sa.ForeignKey("pceen.id"), nullable=False)
    author: Mapped[models.PCeen] = many_to_one("PCeen.events_created")

    _club_id: Column[int] = column(sa.ForeignKey("club.id"), nullable=False)
    club: Mapped[Club] = many_to_one("Club.events")

    def __repr__(self) -> str:
        return f"<Event #{self.id} ({self.title})>"

    def to_dict(self) -> dict[str, typing.Any]:
        """Convert to dict for FullCalendar compatibility."""
        hex_color = self.club.color
        
        # Check if background colour is too bright to use white text
        contrast_color = "#ffffff"
        if hex_color.startswith("#") and len(hex_color) == 7:
            try:
                r = int(hex_color[1:3], 16)
                g = int(hex_color[3:5], 16)
                b = int(hex_color[5:7], 16)
                luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                if luminance > 0.6:  # Prefer using dark text with light backgrounds
                    contrast_color = "#152f4e" 
            except ValueError:
                pass

        return {
            "id": self.id,
            "title": self.title,
            "start": self.start_time.isoformat(),
            "end": self.end_time.isoformat(),
            "allDay": self.all_day,
            "color": hex_color,
            "extendedProps": {
                "description": self.description,
                "location": self.location,
                "club": self.club.name,
                "club_id": self._club_id,
                "contrast_color": contrast_color,
            }
        }
