"""PC est magique Flask App - Database Models"""

from __future__ import annotations

import typing

import sqlalchemy as sa

from app import db
from app.enums import PermissionType, PermissionScope
from app.utils.columns import (
    column,
    many_to_many,
    my_enum,
    Column,
    Relationship,
)


Model = typing.cast(type[type], db.Model)  # type checking hack
Enum = my_enum  # type checking hack


# Association tables


class _PCeen_Role_AT(Model):
    __tablename__ = "_pceen_role_at"
    _pceen_id: Column[int] = column(sa.ForeignKey("pceen.id"), primary_key=True)
    _role_id: Column[int] = column(sa.ForeignKey("role.id"), primary_key=True)


class _Role_Permission_AT(Model):
    __tablename__ = "_role_permission_at"
    _role_id: Column[int] = column(sa.ForeignKey("role.id"), primary_key=True)
    _permission_id: Column[int] = column(
        sa.ForeignKey("permission.id"), primary_key=True
    )


class Role(Model):
    """A role a PCeen can have."""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    name: Column[str] = column(sa.String(64), nullable=False)
    index: Column[int] = column(sa.Integer(), nullable=False, default=1000)
    color: Column[str] = column(sa.String(6), nullable=True)

    pceens: Relationship[list[models.PCeen]] = many_to_many(
        "PCeen.roles", secondary=_PCeen_Role_AT
    )
    permissions: Relationship[list[Permission]] = many_to_many(
        "Permission.roles", secondary=_Role_Permission_AT
    )

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<Role #{self.id} ({self.name})>"

    def __str__(self) -> str:
        """Human-readible description of the role."""
        return self.name

    @property
    def is_dark_colored(self) -> bool:
        """Whether the role color is dark-themed.

        Adapted from https://stackoverflow.com/a/58270890.
        """
        if not self.color:
            return False
        try:
            red = int(self.color[:2], 16)
            green = int(self.color[2:4], 16)
            blue = int(self.color[4:], 16)
        except ValueError:
            return False
        hsp_2 = (0.299 * red**2) + (0.587 * green**2) + (0.114 * blue**2)
        return hsp_2 < 19500


class Permission(Model):
    """A permission a role can have."""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    type: Column[PermissionType] = column(my_enum(PermissionType), nullable=False)
    scope: Column[PermissionScope] = column(my_enum(PermissionScope), nullable=False)
    ref_id: Column[int] = column(sa.Integer(), nullable=True)

    roles: Relationship[list[Role]] = many_to_many(
        "Role.permissions", secondary=_Role_Permission_AT
    )

    def __repr__(self) -> str:
        """Returns repr(self)."""
        try:
            ref = self.ref or "<all>"
        except ValueError:
            ref = f"[#{self.ref_id}]"
        return (
            f"<Permission #{self.id} ({self.type.name} / " f"{self.scope.name}:{ref})>"
        )

    @property
    def ref(self) -> Model | None:
        """Database entry this permission refer to, or ``None`` if global.

        Raises :exc:`ValueError` if this permission refer to non-existing
        item.
        """
        if not self.scope.allow_item or not self.ref_id:
            return None
        item = self.scope.query(models).get(self.ref_id)
        if not item:
            raise ValueError(f"Permission {self} refer to non-existing {self.scope}")
        return item

    def __str__(self) -> str:
        """A human-readible description of this permission."""
        if not self.scope.allow_elem:
            return f"{self.type.name} / {self.scope.name}"
        if self.ref_id is None:
            return f"{self.type.name} / every {self.scope.name}"
        try:
            return f'{self.type.name} / {self.scope.name} "{self.ref}"'
        except ValueError:
            return f"{self.type.name} / [OLD {self.scope.name} #{self.ref_id}]"

    def grants_for(
        self, type: PermissionType, scope: PermissionScope, elem: Model = None
    ) -> bool:
        """Check whether this permission grants given type and scope.

        Args:
            type: The permission type (.read, .write...).
            scope: The permission scope (.pceen, .album...).
            elem: The database entry to check the permission for, if
                applicable.

        Returns:
            If the permission is granted.
        """
        return (
            self.scope == scope
            and ((self.type == type) or (self.type == PermissionType.all))
            and ((self.ref_id is None) or (self.ref == elem))
        )

    @classmethod
    def get_or_create(
        cls, type_: PermissionType, scope: PermissionScope, ref_id: int | None = None
    ) -> Permission:
        perm = cls.query.filter_by(scope=scope, type=type_, ref_id=ref_id).first()
        if not perm:
            perm = cls(scope=scope, type=type_, ref_id=ref_id)
            db.session.add(perm)
            db.session.commit
        return perm


from app import models
