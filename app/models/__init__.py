"""PC est magique Flask App - Database Models"""

import typing

from app import db


Model = typing.cast(type[type], db.Model)  # type checking hack


from app.enums import PaymentStatus, PermissionScope, PermissionType, SubState

from app.models.auth import PCeen
from app.models.bar import GlobalSetting, BarItem, BarTransaction, BarDailyData
from app.models.devices import Allocation, Device
from app.models.gris import Ban, Permission, Role
from app.models.payments import Offer, Payment, Subscription
from app.models.photos import Album, Collection, Photo
from app.models.rooms import Rental, Room
