"""PC est magique Flask App - Database Enums"""

from __future__ import annotations

import enum


__all__ = ["PermissionType", "PermissionScope"]


class PermissionType(enum.Enum):
    """"The type of a permission."""
    def __repr__(self) -> str:
        return f"<{type(self).__name__}.{self.name}>"

    all = enum.auto()
    read = enum.auto()
    write = enum.auto()
    delete = enum.auto()


class PermissionScope(enum.Enum):
    """"The scope of a permission.

    Attrs:
        allow_elem (bool): If this scope allows specific permissions.
        need_elem (bool): If this scope allows for a global permission.
        parent (PermissionScope | None): The scope this scope is enclosed
            in, if applicable: if the parent element has a given permission
            granted, it is granted for all its children (recursively).
            Should be set only if ``need_elem`` is ``True``.
        parent_attr (str | None): The attribute of the underlying element
            used to retrieve its parent. Should be set if and only if
            ``parent`` is set.
    """
    def __new__(cls, allow_elem: bool, need_elem: bool, _parent: str | None,
                parent_attr: str | None):
        obj = object.__new__(cls)
        obj._value_ = enum.auto()
        obj.allow_elem = allow_elem
        obj.need_elem = need_elem
        obj.parent = getattr(cls, _parent) if _parent else None
        obj.parent_attr = parent_attr
        return obj

    def __repr__(self) -> str:
        return f"<{type(self).__name__}.{self.name}>"

    pceen = (True, False, None, None)
    photos = (False, False, None, None)
    collection = (True, False, None, None)
    album = (True, True, "collection", "collection")
    role = (True, False, None, None)
