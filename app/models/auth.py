"""PC est magique Flask App - Authentification Models"""

from __future__ import annotations

import datetime
import os
import re
import time
import typing

import jwt
import flask
from flask_babel import _
import flask_login
import sqlalchemy as sa
from sqlalchemy.ext.hybrid import hybrid_property
from unidecode import unidecode
from sqlalchemy.orm import Query
from werkzeug import security as wzs

from app import db
from app.enums import PermissionType, PermissionScope, SubState
from app.utils import helpers
from app.utils.columns import (
    column,
    one_to_many,
    many_to_many,
    my_enum,
    Column,
    Relationship,
)

app = flask.Flask(__name__)

Model = typing.cast(type[type], db.Model)  # type checking hack
Enum = my_enum  # type checking hack


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
    username: Column[str] = column(sa.String(64), unique=True, nullable=False)
    nom: Column[str] = column(sa.String(64), nullable=False)
    prenom: Column[str] = column(sa.String(64), nullable=False)
    promo: Column[int | None] = column(sa.Integer, nullable=True)
    email: Column[str] = column(sa.String(120), unique=True, nullable=False)
    locale: Column[str | None] = column(sa.String(8), nullable=True)
    is_gri: Column[bool] = column(sa.Boolean(), nullable=False, default=False)
    sub_state: Column[SubState] = column(Enum(SubState), nullable=True)
    espci_email: Column[str] = column(sa.String(120), unique=True, nullable=True)

    # Login info
    activated: Column[bool] = column(sa.Boolean(), nullable=False, default=True)
    _password_hash: Column[str] = column(sa.String(256), nullable=True)
    espci_sso_enabled: Column[bool] = column(sa.Boolean(), nullable=False, default=False)

    # Bar info
    bar_nickname: Column[str | None] = column(sa.String(128), nullable=True)
    bar_balance: Column[float | None] = column(
        sa.Numeric(precision=6, scale=2, asdecimal=False), default=0.0, nullable=True
    )
    bar_deposit: Column[bool | None] = column(sa.Boolean(), default=False, nullable=True)

    # Club Q info
    discontent: Column[float] = column(sa.Numeric(precision=2, asdecimal=False), nullable=True)

    photos = one_to_many("Photo.author", uselist=True)
    roles = many_to_many(
        "Role.pceens",
        secondary="_pceen_role_at",
        order_by="Role.index",
        uselist=True,
    )
    bans = one_to_many("Ban.pceen", uselist=True)
    devices = one_to_many("Device.pceen", uselist=True)
    rentals = one_to_many("Rental.pceen", uselist=True)
    subscriptions = one_to_many("Subscription.pceen", uselist=True)
    payments = one_to_many("Payment.pceen", foreign_keys="Payment._pceen_id", uselist=True)
    payments_created = one_to_many("Payment.gri", foreign_keys="Payment._gri_id", uselist=True)

    bar_transactions_made = one_to_many(
        "BarTransaction.client",
        foreign_keys="BarTransaction._client_id",
        lazy="select",
        uselist=True,
    )
    bar_transactions_cashed = one_to_many(
        "BarTransaction.barman",
        foreign_keys="BarTransaction._barman_id",
        lazy="select",
        uselist=True,
    )
    bar_transactions_reverted = one_to_many(
        "BarTransaction.reverter",
        foreign_keys="BarTransaction._reverter_id",
        lazy="select",
        uselist=True,
    )
    bar_daily_data = one_to_many("BarDailyData.pceen", uselist=True)

    clubq_voeux = one_to_many("ClubQVoeu.pceen", uselist=True)

    order_panier_bio = one_to_many("OrderPanierBio.pceen", uselist=True)

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<PCeen #{self.id} ('{self.username}')>"

    def __str__(self) -> str:
        """Human-readible description of the PCeen."""
        return f"{self.full_name} {self.promo or '(no promo)'}"

    @hybrid_property
    def full_name(self) -> str:
        """The pceens's first + last names."""
        return self.prenom + " " + self.nom

    def _get_list(self, attr_name: str) -> list:
        """Helper to make SQLAlchemy relationships into a list."""
        val = getattr(self, attr_name)
        if not val:
            return []
        if not isinstance(val, (list, set, tuple)):
            return [val]
        return val

    @property
    def all_roles(self) -> list:
        """Gets roles from templates"""
        return self._get_list("roles")

    @property
    def all_devices(self) -> list:
        """Gets devices from templates."""
        return self._get_list("devices")

    @property
    def permissions(self) -> set[models.Permission]:
        """The set of all permissions this PCeen has."""
        roles_list = self._get_list("roles")

        all_perms = set()
        for role in roles_list:
            perms = role.permissions
            if not perms:
                continue
            if not isinstance(perms, (list, set, tuple)):
                perms = [perms]
            all_perms.update(perms)
            
        return all_perms

    @classmethod
    def _has_permission(
        cls,
        permissions,
        type: PermissionType,
        scope: PermissionScope,
        elem: Model = None,
    ) -> bool:
        # Check validity
        if not scope.allow_elem and elem:
            raise ValueError(f"Specifying elem is not allowed for {scope}")
        if scope.need_elem and not elem:
            raise ValueError(f"Specifying elem is mandatory for {scope}")
            
        # Make sure that permissions is a list
        if not permissions:
            permissions = []
        elif not isinstance(permissions, (list, set, tuple)):
            permissions = [permissions]

        # Check all permissions
        for permission in permissions:
            if permission.grants_for(type, scope, elem):
                return True
                
        # Check all permissions for the parent permission
        if scope.parent and elem:
            parent_elem = getattr(elem, scope.parent_attr)
            if cls._has_permission(permissions, type, scope.parent, parent_elem):
                return True
                
        # No permission granted
        return False

    def has_permission(self, type: PermissionType, scope: PermissionScope, elem: Model = None) -> bool:
        """Check whether this PCeen has a given permission.

        Args:
            type: The permission type (.read, .write...).
            scope: The permission scope (.pceen, .album...).
            elem: The database entry to check the permission for, if applicable.

        Returns:
            If the permission is granted.
        """
        return self._has_permission(self.permissions, type, scope, elem) or self.has_public_permission(
            type, scope, elem
        )

    @classmethod
    def has_public_permission(cls, type: PermissionType, scope: PermissionScope, elem: Model = None) -> bool:
        """Check whether an anonymous user has a given permission.

        Args:
            type: The permission type (.read, .write...).
            scope: The permission scope (.pceen, .album...).
            elem: The database entry to check the permission for, if applicable.

        Returns:
            If the permission is granted.
        """
        public_role: models.Role = models.db.session.get(models.Role, 0)
        if not public_role:
            return False
        return cls._has_permission(public_role.permissions, type, scope, elem)

    @classmethod
    def find_by_fuzzy_name(cls, nom: str, prenom: str, promo: int | None) -> PCeen | None:
        """Find a PCeen by a fuzzy name (unaccented + lowercased) and promo.
        
        Args:
            nom: The user's last name.
            prenom: The user's first name.
            promo: The user's promotion number.
            
        Returns:
            The matching PCeen, if one exists.
        """
        if not nom or not prenom or promo is None:
            return None
            
        nom_clean = re.sub(r'\W+', ' ', unidecode(nom)).strip()
        prenom_clean = re.sub(r'\W+', ' ', unidecode(prenom)).strip()
        
        return cls.query.filter(
            sa.func.trim(sa.func.regexp_replace(sa.func.unaccent(cls.nom), r'\W+', ' ', 'g')).ilike(nom_clean),
            sa.func.trim(sa.func.regexp_replace(sa.func.unaccent(cls.prenom), r'\W+', ' ', 'g')).ilike(prenom_clean),
            cls.promo == promo
        ).first()

    @property
    def first_seen(self) -> datetime.datetime:
        """The first time the pceen registered a device, or now."""
        devices = self._get_list("devices")
        if not devices:
            return datetime.datetime.now(datetime.UTC)
        return min(device.registered for device in devices)

    @property
    def current_device(self) -> models.Device | None:
        """The PCeen's last seen device, or ``None``."""
        devices = self._get_list("devices")
        if not devices:
            return None
        return max(devices, key=lambda device: device.last_seen_time)

    @property
    def last_seen(self) -> datetime.datetime | None:
        """The last time the PCeen logged in, or ``None``."""
        if not self.current_device:
            return None
        return self.current_device.last_seen

    @property
    def other_devices(self) -> list[models.Device]:
        """The PCeen's non-current* devices.

        Sorted from most recently seen to latest seen.

        *If the PCeen's "current_device" is not the device currently making the request
        (connection from outside/GRIs list), it is included in this list.
        """
        devices = self._get_list("devices")
        if not devices:
            return []
        all_devices = sorted(devices, key=lambda device: device.last_seen_time, reverse=True)
        if flask.g.internal and self == flask.g.pceen:
            # Really connected from current device: exclude it from other
            return all_devices[1:]
        else:
            # Connected from outside/an other device: include it
            return all_devices

    @property
    def current_rental(self) -> models.Rental | None:
        """The PCeen's current rental, or ``None``."""
        rentals = self._get_list("rentals")
        return next((rent for rent in rentals if rent.is_current), None)

    @property
    def old_rentals(self) -> list[models.Rental]:
        """The PCeen's non-current rentals."""
        rentals = self._get_list("rentals")
        return [rental for rental in rentals if not rental.is_current]

    @property
    def current_room(self) -> models.Room | None:
        """The PCeen's current room, or ``None``."""
        current_rental = self.current_rental
        return current_rental.room if current_rental else None

    @property
    def has_a_room(self) -> bool:
        """Whether the PCeen has currently a room rented."""
        return self.current_rental is not None

    @property
    def current_subscription(self) -> models.Subscription | None:
        """:class:`Subscription`: The PCeen's current subscription, or ``None``.

        Sorted from most recent to last recent subscription."""
        subscriptions = self._get_list("subscriptions")
        if not subscriptions:
            return None
        return max(subscriptions, key=lambda sub: sub.start)

    @property
    def old_subscriptions(self) -> list[models.Subscription] | None:
        """:class:`list[Subscription]`: The PCeen's non-current subscriptions."""
        subscriptions = self._get_list("subscriptions")
        if not subscriptions:
            return None
        return sorted(
            (sub for sub in subscriptions if not sub.is_active),
            key=lambda sub: sub.end,
            reverse=True,
        )

    def compute_sub_state(self) -> SubState:
        """Compute the PCeen's subscription state.

        Theoretically returns :attr:`~PCeen.sub_state`, but computed
        from :attr:`~PCeen.subscriptions`: it will differ the first
        minutes of the day of state change, before the daily scheduled
        script ``update_sub_states`` changes it.

        Returns:
            :class:.SubState`:
        """
        sub = self.current_subscription
        if not sub:
            # Default: trial
            return SubState.trial
        elif not sub.is_active:
            return SubState.outlaw
        elif sub.is_trial:
            return SubState.trial
        else:
            return SubState.subscribed

    def add_first_subscription(self) -> None:
        """Add subscription to first offer (free month).

        The subscription starts the day the PCeen registered its first
        device (usually today), and ends today.
        """
        if not self._get_list("devices"):
            return
        offer = models.Offer.first_offer()
        start = self.first_seen.date()
        sub = models.Subscription(
            pceen=self,
            offer=offer,
            payment=None,
            start=start,
            end=datetime.date.today(),
        )
        db.session.add(sub)
        self.sub_state = SubState.trial
        db.session.commit()
        helpers.log_action(
            f"Added {sub!r} to {offer!r}, with no payment, "
            f"granting Internet access for {start} – {start + offer.delay}"
        )

    @property
    def current_ban(self) -> models.Ban | None:
        """The PCeen's current ban, or ``None``."""
        bans = self._get_list("bans")
        return next((ban for ban in bans if ban.is_active), None)

    @property
    def is_banned(self) -> bool:
        """Whether the PCeen is currently under a ban."""
        return self.current_ban is not None

    @property
    def current_bar_daily_data(self) -> models.BarDailyData:
        """Current readonly Bar daily data of the PCeen."""
        return models.BarDailyData.from_pceen_and_timestamp(
            pceen=self, timestamp=datetime.datetime.utcnow(), create=False
        )

    @property
    def has_bar_avatar(self) -> bool:
        """Check if the PCeen has a bar avatar on the filesystem."""
        path = os.path.join(flask.current_app.config["PHOTOS_BASE_PATH"], "bar_avatars", str(self.promo), f"{self.username}.jpg")
        return os.path.exists(path)

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
            algorithm="HS256",
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
            id = jwt.decode(token, flask.current_app.config["SECRET_KEY"], algorithms=["HS256"])["reset_password"]
        except Exception:
            return
        return db.session.get(cls, id)


from app import models