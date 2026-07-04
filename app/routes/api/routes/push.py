"""PC est magique - API Push routes"""

import flask
from flask_babel import _
import flask_login

from app import db, models
from app.utils import helpers

sbp = flask.Blueprint("push", __name__)

@sbp.route("/subscribe", methods=["POST"])
@flask_login.login_required
def subscribe():
    """Subscribe to push notifications."""
    sub_data = flask.request.get_json()
    if not isinstance(sub_data, dict):
        return flask.jsonify(status="error", message="Invalid subscription data format"), 400

    if "endpoint" not in sub_data or "keys" not in sub_data or not isinstance(sub_data["keys"], dict):
        return flask.jsonify(status="error", message="Invalid subscription data fields"), 400

    endpoint = sub_data.get("endpoint")
    p256dh = sub_data["keys"].get("p256dh")
    auth = sub_data["keys"].get("auth")

    if not endpoint or not p256dh or not auth:
        return flask.jsonify(status="error", message="Missing keys"), 400

    # Check if exists
    sub = models.PushSubscription.query.filter_by(endpoint=endpoint).first()
    if sub:
        if sub.pceen == flask.g.pceen:
            return flask.jsonify(status="success", message="Already subscribed")
        else:
            # Transfer subscription to new user
            sub.pceen = flask.g.pceen
            db.session.commit()
            return flask.jsonify(status="success", message="Subscription transferred")

    # Create new
    sub = models.PushSubscription(
        pceen=flask.g.pceen,
        endpoint=endpoint,
        p256dh=p256dh,
        auth=auth,
    )
    db.session.add(sub)
    db.session.commit()

    return flask.jsonify(status="success", message="Subscribed")

@sbp.route("/unsubscribe", methods=["POST"])
@flask_login.login_required
def unsubscribe():
    """Unsubscribe from push notifications."""
    sub_data = flask.request.get_json()
    if not isinstance(sub_data, dict) or "endpoint" not in sub_data:
        return flask.jsonify(status="error", message="Invalid subscription data"), 400

    endpoint = sub_data["endpoint"]
    sub = models.PushSubscription.query.filter_by(endpoint=endpoint).first()
    if sub and sub.pceen == flask.g.pceen:
        db.session.delete(sub)
        db.session.commit()

    return flask.jsonify(status="success", message="Unsubscribed")

@sbp.route("/vapid_public_key", methods=["GET"])
@flask_login.login_required
def vapid_public_key():
    """Get the VAPID public key."""
    return flask.jsonify(
        status="success",
        public_key=flask.current_app.config["VAPID_PUBLIC_KEY"]
    )

@sbp.route("/notifications/<int:notif_id>/read", methods=["POST"])
@flask_login.login_required
def read_notification(notif_id):
    """Mark a specific notification as read."""
    notif = db.session.get(models.Notification, notif_id)
    if not notif:
        flask.abort(404)
        
    read_record = models.NotificationRead.query.filter_by(
        pceen_id=flask.g.pceen.id,
        notification_id=notif_id
    ).first()
    
    if not read_record:
        read_record = models.NotificationRead(
            pceen_id=flask.g.pceen.id,
            notification_id=notif_id
        )
        db.session.add(read_record)
        db.session.commit()
        
    return flask.jsonify(status="success")

@sbp.route("/notifications/read_all", methods=["POST"])
@flask_login.login_required
def read_all_notifications():
    """Mark all visible notifications as read."""
    from app.models.push import Notification
    
    stmt = Notification.get_visible_notifications_stmt(flask.g.pceen).with_only_columns(Notification.id).order_by(Notification.created_at.desc()).limit(20)
    
    visible_notif_ids = db.session.scalars(stmt).all()
    
    # Query what is already read
    already_read_stmt = db.select(models.NotificationRead.notification_id).where(
        models.NotificationRead.pceen_id == flask.g.pceen.id
    )
    already_read_ids = set(db.session.scalars(already_read_stmt).all())
    
    # Mark unread ones as read
    to_add = []
    for nid in visible_notif_ids:
        if nid not in already_read_ids:
            to_add.append(models.NotificationRead(
                pceen_id=flask.g.pceen.id,
                notification_id=nid
            ))
            
    if to_add:
        db.session.add_all(to_add)
        db.session.commit()
        
    return flask.jsonify(status="success")

@sbp.route("/notifications/navbar", methods=["GET"])
@flask_login.login_required
def navbar_notifications():
    """Get the navbar notifications HTML and unread count."""
    from app.models.push import Notification, NotificationRead
    
    stmt = Notification.get_visible_notifications_stmt(flask.g.pceen).order_by(Notification.created_at.desc()).limit(20)
    recent_notifications = db.session.scalars(stmt).all()
    
    read_stmt = db.select(NotificationRead.notification_id).where(
        NotificationRead.pceen_id == flask.g.pceen.id
    )
    read_notification_ids = set(db.session.scalars(read_stmt).all())
    
    unread_count = sum(1 for n in recent_notifications if n.id not in read_notification_ids)
    
    html = flask.render_template(
        "_navbar_notifications.html",
        recent_notifications=recent_notifications,
        read_notification_ids=read_notification_ids,
        unread_count=unread_count
    )
    
    return flask.jsonify(status="success", html=html, unread_count=unread_count)
