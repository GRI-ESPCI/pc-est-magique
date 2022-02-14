"""PC est magique Flask App - Database Models"""

from __future__ import annotations

import time

import jwt
import flask
import flask_login
import sqlalchemy as sa
from werkzeug import security as wzs

from app import db
from app.tools import typing
from app.tools.columns import (column, one_to_many, many_to_one, my_enum,
                               Column, Relationship)


Model = typing.cast(type[type], db.Model)   # type checking hack
Enum = my_enum                              # type checking hack


class PCeen(flask_login.UserMixin, Model):
    """A PCeen.

    :class:`flask_login.UserMixin` adds the following properties and methods:
        * is_authenticated: a property that is True if the pceen has
            valid credentials or False otherwise.
        * is_active: a property that is True if the pceen's account is
            active or False otherwise.
        * is_anonymous: a property that is False for regular pceens, and
            True for a special, anonymous pceen.
        * get_id(): a method that returns a unique identifier for the
            pceen as a string.
    """
    __tablename__ = "pceen"

    id: Column[int] = column(sa.Integer(), primary_key=True)
    username: Column[str | None] = column(sa.String(64), unique=True)
    nom: Column[str | None] = column(sa.String(64))
    prenom: Column[str | None] = column(sa.String(64))
    promo: Column[int | None] = column(sa.Integer)
    email: Column[str | None] = column(sa.String(120), unique=True)
    locale: Column[str | None] = column(sa.String(8))
    is_gri: Column[bool] = column(sa.Boolean(), nullable=False, default=False)
    _password_hash: Column[str | None] = column(sa.String(128))

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<PCeen #{self.id} ('{self.username}')>"

    @property
    def full_name(self) -> str:
        """The pceens's first + last names."""
        return f"{self.prenom} {self.nom}"

    def set_password(self, password: str) -> None:
        """Save or modify pceen password.

        Relies on :func:`werkzeug.security.generate_password_hash` to
        store a password hash only.

        Args:
            password: The password to store. Not stored.
        """
        self._password_hash = wzs.generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check that a given password matches stored pceen password.

        Relies on :func:`werkzeug.security.check_password_hash` to
        compare tested password with stored password hash.

        Args:
            password: The password to check. Not stored.

        Returns:
            Whether the password is correct.
        """
        return wzs.check_password_hash(self._password_hash or "", password)

    def get_reset_password_token(self, expires_in: int = 600) -> str:
        """Forge a JWT reset password token for the pceen.

        Relies on :func:`jwt.encode`.

        Args:
            expires_in: The time before the token expires, in seconds.

        Returns:
            The created JWT token.
        """
        return jwt.encode(
            {"reset_password": self.id, "exp": time.time() + expires_in},
            flask.current_app.config["SECRET_KEY"],
            algorithm="HS256"
        )

    @classmethod
    def verify_reset_password_token(cls, token: str) -> PCeen | None:
        """Verify a pceen password reset token (class method).

        Relies on :func:`jwt.decode`.

        Args:
            token: The JWT token to decode.

        Returns:
            The pceen to reset password of if the token is valid and the
            pceen exists, else ``None``.
        """
        try:
            id = jwt.decode(
                token,
                flask.current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )["reset_password"]
        except Exception:
            return
        return cls.query.get(id)
