"""PC est magique - Calendar Routes"""

import datetime
import flask
from flask_babel import _

from app import context, db
from app.models import Club, Event, PermissionType, PermissionScope, ClubQSpectacle
from app.routes.calendar import bp
from app.routes.calendar.forms import EditClub

@bp.before_request
def check_access():
    if not context.g.logged_in:
        return
    if not context.has_permission(PermissionType.read, PermissionScope.calendar):
        if flask.request.path.startswith("/calendar/api/"):
            flask.abort(403)
        flask.flash(_("Vous n'avez pas accès au calendrier."), "danger")
        return flask.redirect(flask.url_for("main.index"))

@bp.route("/")
@context.logged_in_only
def index():
    """Main calendar page."""
    clubs = db.session.scalars(db.select(Club).order_by(Club.name)).all()
    can_admin = context.has_permission(PermissionType.write, PermissionScope.calendar)
    return flask.render_template("calendar/index.html", title=_("Calendrier"), clubs=clubs, can_admin=can_admin)

@bp.route("/api/events")
@context.logged_in_only
def get_events():
    """API route to get events in JSON format."""
    start_str = flask.request.args.get("start")
    end_str = flask.request.args.get("end")
    
    query = db.select(Event)
    spectacle_query = db.select(ClubQSpectacle)
    if start_str:
        start = datetime.datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        query = query.where(Event.end_time >= start)
        spectacle_query = spectacle_query.where(ClubQSpectacle.date >= start - datetime.timedelta(hours=2))
    if end_str:
        end = datetime.datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        query = query.where(Event.start_time <= end)
        spectacle_query = spectacle_query.where(ClubQSpectacle.date <= end)
        
    events = db.session.scalars(query).all()
    spectacles = db.session.scalars(spectacle_query).all()
    
    can_edit_calendar = context.has_permission(PermissionType.write, PermissionScope.calendar)
    
    events_list = [{
        **event.to_dict(),
        "can_edit": can_edit_calendar
    } for event in events]
    
    club_q = db.session.scalars(db.select(Club).filter_by(name="Club Q")).first()
    hex_color = club_q.color if club_q else "#dc8add"
    
    contrast_color = "#ffffff"
    if hex_color.startswith("#") and len(hex_color) == 7:
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            if luminance > 0.6:
                contrast_color = "#152f4e"
        except ValueError:
            pass

    for spec in spectacles:
        events_list.append({
            "id": f"clubq_{spec.id}",
            "title": spec.nom,
            "start": spec.date.isoformat(),
            "end": (spec.date + datetime.timedelta(hours=2)).isoformat(),
            "allDay": False,
            "color": hex_color,
            "extendedProps": {
                "description": spec.description,
                "location": spec.salle.nom if spec.salle else None,
                "club": "Club Q",
                "club_id": club_q.id if club_q else None,
                "contrast_color": contrast_color,
                "can_edit": False
            }
        })

    return flask.jsonify(events_list)

@bp.route("/api/events/edit/<int:event_id>", methods=["POST"])
@context.logged_in_only
def edit_event(event_id: str):
    """API route to edit an event."""
    event = db.session.get(Event, event_id)
    if not event:
        flask.abort(404, "Event not found")

    if not context.has_permission(PermissionType.write, PermissionScope.calendar):
        flask.abort(403, "You do not have permission to edit events in the calendar.")

    title = flask.request.form.get("title")
    club_id = flask.request.form.get("club_id", type=int)
    start_time_str = flask.request.form.get("start")
    end_time_str = flask.request.form.get("end")
    location = flask.request.form.get("location")
    description = flask.request.form.get("description")
    all_day = flask.request.form.get("all_day") == "true"

    if not title or not club_id or not start_time_str or not end_time_str:
        return flask.jsonify({"status": "error", "message": "Il manque des champs obligatoires."}), 400

    if len(title) > 128:
        return flask.jsonify({"status": "error", "message": "Le titre de l'évènement est trop long (128 caractères maximum)."}), 400
        
    if location and len(location) > 128:
        return flask.jsonify({"status": "error", "message": "Le lieu est trop long (128 caractères maximum)."}), 400

    new_club = db.session.get(Club, club_id)
    if not new_club:
        flask.abort(404, "New club not found")

    # Only allow calendar admins to add or edit clubs
    if new_club != event.club and not context.has_permission(PermissionType.write, PermissionScope.calendar):
        flask.abort(403, "You do not have permission to assign to the new club.")

    try:
        event.title = title
        event.club = new_club
        event.start_time = datetime.datetime.fromisoformat(start_time_str)
        event.end_time = datetime.datetime.fromisoformat(end_time_str)
        event.location = location
        event.description = description
        event.all_day = all_day
    except ValueError:
        flask.abort(400, "Invalid date format")

    db.session.commit()
    
    return flask.jsonify({
        "status": "success",
        "event": event.to_dict(),
        "message": str(_("Évènement '%(title)s' mis à jour !", title=title))
    })


@bp.route("/api/events/create", methods=["POST"])
@context.logged_in_only
def create_event():
    """API route to create an event."""
    title = flask.request.form.get("title")
    club_id = flask.request.form.get("club_id", type=int)
    start_time_str = flask.request.form.get("start")
    end_time_str = flask.request.form.get("end")
    location = flask.request.form.get("location")
    description = flask.request.form.get("description")
    all_day = flask.request.form.get("all_day") == "true"

    if not title or not club_id or not start_time_str or not end_time_str:
        return flask.jsonify({"status": "error", "message": "Il manque des champs obligatoires."}), 400

    if len(title) > 128:
        return flask.jsonify({"status": "error", "message": "Le titre de l'évènement est trop long (128 caractères maximum)."}), 400
        
    if location and len(location) > 128:
        return flask.jsonify({"status": "error", "message": "Le lieu est trop long (128 caractères maximum)."}), 400

    club = db.session.get(Club, club_id)
    if not club:
        flask.abort(404, "Club not found")

    # Check if the user has write permission for the calendar
    if not context.has_permission(PermissionType.write, PermissionScope.calendar):
        flask.abort(403, "You do not have permission to create events in the calendar.")

    try:
        start_time = datetime.datetime.fromisoformat(start_time_str)
        end_time = datetime.datetime.fromisoformat(end_time_str)
    except ValueError:
        flask.abort(400, "Invalid date format")

    event = Event(
        title=title,
        description=description,
        location=location,
        start_time=start_time,
        end_time=end_time,
        all_day=all_day,
        author=context.g.pceen,
        club=club
    )
    
    db.session.add(event)
    db.session.commit()
    
    return flask.jsonify({
        "status": "success",
        "event": event.to_dict(),
        "message": str(_("Évènement '%(title)s' créé avec succès !", title=title))
    }), 201

@bp.route("/admin")
@context.permission_only(PermissionType.write, PermissionScope.calendar)
def admin():
    """Calendar administration page (list of clubs)."""
    clubs = db.session.scalars(db.select(Club).order_by(Club.name)).all()
    return flask.render_template("calendar/admin.html", clubs=clubs)

@bp.route("/admin/club/new", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.calendar)
def admin_club_new():
    """Calendar route to create a new club."""
    form = EditClub()
    if form.validate_on_submit():
        club = Club(name=form.name.data, color=form.color.data)
        db.session.add(club)
        db.session.commit()
        flask.flash(_("Club '%(name)s' créé avec succès.", name=club.name), "success")
        return flask.redirect(flask.url_for("calendar.admin"))
    return flask.render_template("calendar/admin_club_new.html", form=form)

@bp.route("/admin/club/edit/<int:id>", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.calendar)
def admin_club_edit(id: int):
    """Calendar route to edit an existing club."""
    club = db.session.get(Club, id)
    if not club:
        flask.abort(404)
    form = EditClub(obj=club)
    if form.validate_on_submit():
        club.name = form.name.data
        club.color = form.color.data
        db.session.commit()
        flask.flash(_("Club '%(name)s' mis à jour.", name=club.name), "success")
        return flask.redirect(flask.url_for("calendar.admin"))
    return flask.render_template("calendar/admin_club_edit.html", form=form, club=club)

@bp.route("/admin/club/delete/<int:id>", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.calendar)
def admin_club_delete(id: int):
    """Calendar route to delete a club."""
    club = db.session.get(Club, id)
    if not club:
        flask.abort(404)
    db.session.delete(club)
    db.session.commit()
    flask.flash(_("Club supprimé."), "success")
    return flask.redirect(flask.url_for("calendar.admin"))


@bp.route("/static/fullcalendar.min.js")
@context.logged_in_only
def serve_fullcalendar():
    """Serve FullCalendar from node_modules."""
    import os
    from werkzeug.utils import safe_join
    proj_root = os.path.dirname(flask.current_app.root_path)
    return flask.send_from_directory(
        safe_join(proj_root, "node_modules", "fullcalendar"),
        "index.global.min.js"
    )

