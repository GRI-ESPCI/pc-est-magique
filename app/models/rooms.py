"""PC est magique Flask App - Rooms Models"""

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


class Rental(Model):
    """A rental of a Rezidence room by a PCeen."""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    _pceen_id: Column[int] = column(sa.ForeignKey("pceen.id"), nullable=False)
    pceen: Relationship[models.PCeen] = many_to_one("PCeen.rentals")
    _room_num: Column[int] = column(sa.ForeignKey("room.num"), nullable=False)
    room: Relationship[Room] = many_to_one("Room.rentals")
    start: Column[datetime.date] = column(sa.Date(), nullable=False)
    end: Column[datetime.date | None] = column(sa.Date(), nullable=True)

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<Rental #{self.id} of {self.room} by {self.pceen}>"

    @property
    def is_current(self) -> bool:
        """Whether the rental is current."""
        return (self.end is None) or (self.end > datetime.date.today())


class Room(Model):
    """A Rezidence room."""

    num: Column[int] = column(sa.Integer(), primary_key=True)
    floor: Column[int] = column(sa.Integer())
    base_ip: Column[str] = column(sa.String(4))
    ips_allocated: Column[int] = column(sa.Integer(), nullable=False, default=0)

    rentals: Relationship[list[Rental]] = one_to_many("Rental.room")
    allocations: Relationship[list[models.Allocation]] = one_to_many("Allocation.room")

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<Room {self.num}>"

    @property
    def current_rental(self) -> Rental | None:
        """The room current rental, or ``None``."""
        try:
            return next(rent for rent in self.rentals if rent.is_current)
        except StopIteration:
            return None

    @classmethod
    def create_rez_rooms(cls):
        """Create the list of existing Rezidence rooms.

        Returns:
            list[Room]
        """
        doors_per_floor = {
            1: 16,
            2: 26,
            3: 26,
            4: 26,
            5: 26,
            6: 20,
            7: 20,
        }
        rooms = []
        for floor, max_door in doors_per_floor.items():
            for door in range(1, max_door + 1):
                rooms.append(cls(num=100 * floor + door, floor=floor, base_ip=f"{floor}.{door}"))
        return rooms


from app import models
