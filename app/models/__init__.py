"""PC est magique Flask App - Database Models"""

import typing

from app import db


Model = typing.cast(type[type], db.Model)  # type checking hack


from app.enums import PermissionScope, PermissionType

from app.models.auth import PCeen
from app.models.gris import Permission, Role
from app.models.photos import Album, Collection, Photo
