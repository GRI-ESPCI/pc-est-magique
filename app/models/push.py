"""PC est magique Flask App - Push Notifications Models"""

from __future__ import annotations

import datetime
import typing
import sqlalchemy as sa
from sqlalchemy.orm import Mapped

from app import db
from app.utils.columns import column, Column, many_to_one, one_to_many

Model = typing.cast(type[type], db.Model)  # type checking hack

class PushSubscription(Model):
    """A push notification subscription."""
    
    __tablename__ = "push_subscription"
    
    id: Column[int] = column(sa.Integer, primary_key=True)
    _pceen_id: Column[int] = column(sa.ForeignKey("pceen.id"), nullable=False)
    endpoint: Column[str] = column(sa.String(1024), unique=True, nullable=False)
    p256dh: Column[str] = column(sa.String(255), nullable=False)
    auth: Column[str] = column(sa.String(255), nullable=False)

    pceen: Mapped["models.PCeen"] = many_to_one("PCeen.push_subscriptions")

class Notification(Model):
    """A sent notification stored in history."""
    
    __tablename__ = "notification"
    
    id: Column[int] = column(sa.Integer, primary_key=True)
    title: Column[str] = column(sa.String(128), nullable=False)
    body: Column[str] = column(sa.String(512), nullable=False)
    image: Column[str | None] = column(sa.String(256), nullable=True)
    url: Column[str | None] = column(sa.String(256), nullable=True)
    target_type: Column[str] = column(sa.String(32), nullable=False)  # 'all', 'eleves', 'rez', 'role'
    role_id: Column[int | None] = column(sa.ForeignKey("role.id", ondelete="SET NULL"), nullable=True)
    created_at: Column[datetime.datetime] = column(sa.DateTime(), nullable=False, default=datetime.datetime.utcnow)

    role: Mapped[typing.Optional["models.Role"]] = many_to_one("Role.notifications")
    reads: Mapped[list["NotificationRead"]] = one_to_many("NotificationRead.notification")

    @classmethod
    def get_visible_notifications_stmt(cls, pceen: "models.PCeen") -> sa.sql.Select:
        from app.models.auth import SubState
        
        target_types = ["all"]
        if pceen.promo:
            target_types.append("eleves")
        if pceen.sub_state in (SubState.subscribed, SubState.trial):
            target_types.append("rez")
            
        role_ids = [r.id for r in pceen.roles] if pceen.roles else []
        
        return db.select(cls).where(
            sa.or_(
                cls.target_type.in_(target_types),
                sa.and_(
                    cls.target_type == "role",
                    cls.role_id.in_(role_ids) if role_ids else sa.false()
                )
            )
        )

class NotificationRead(Model):
    """Association table to track which notifications are read by which user."""

    __tablename__ = "notification_read"

    pceen_id: Column[int] = column(sa.ForeignKey("pceen.id", ondelete="CASCADE"), primary_key=True)
    notification_id: Column[int] = column(sa.ForeignKey("notification.id", ondelete="CASCADE"), primary_key=True)

    pceen: Mapped["models.PCeen"] = many_to_one("PCeen.read_notifications")
    notification: Mapped["Notification"] = many_to_one("Notification.reads")

from app import models
