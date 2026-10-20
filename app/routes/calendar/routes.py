"""PC est magique - Calendar Routes"""

import datetime
import os
import zoneinfo

import flask
from flask_babel import _
import ics
from ics.grammar.parse import ContentLine
from werkzeug.utils import safe_join

from app import context, db
from app.models import Club, Event, PermissionType, PermissionScope, ClubQSpectacle, PCeen, ClubQVoeu, JeuReservation
from app.routes.calendar import bp
from app.routes.calendar.forms import EditClub
from app.utils.holidays import get_espci_vacations
from sqlalchemy.orm import selectinload

CLUB_Q_NAME = "Club Q"

@bp.before_request
def check_access():
    # Skip for unauthenticated users; individual routes handle auth
    # via @logged_in_only or token verification (e.g. export_feed)
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
    calendar_token = context.g.pceen.get_calendar_token() if context.g.pceen else None
    return flask.render_template("calendar/index.html", title=_("Calendrier"), clubs=clubs, can_admin=can_admin, calendar_token=calendar_token)

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
    
    club_q = db.session.scalars(db.select(Club).filter_by(name=CLUB_Q_NAME)).first()
    hex_color = club_q.color if club_q else "#dc8add"
    contrast_color = club_q.get_contrast_color() if club_q else "#ffffff"

    for spec in spectacles:
        events_list.append({
            "id": f"clubq_{spec.id}",
            "title": spec.nom,
            "start": spec.date.isoformat(),
            "end": (spec.date + datetime.timedelta(hours=2)).isoformat(),
            "allDay": False,
            "color": hex_color,
            "can_edit": False,
            "extendedProps": {
                "description": spec.description,
                "location": spec.salle.nom if spec.salle else None,
                "club": CLUB_Q_NAME,
                "club_id": club_q.id if club_q else None,
                "contrast_color": contrast_color,
            }
        })

    if context.g.pceen:
        jeu_res_query = (
            db.select(JeuReservation)
            .options(selectinload(JeuReservation.jeu))
            .where(
                JeuReservation._pceen_id == context.g.pceen.id,
                JeuReservation.cancelled.is_(False),
            )
        )
        if start_str:
            jeu_res_query = jeu_res_query.where(JeuReservation.end_date >= start.date())
        if end_str:
            jeu_res_query = jeu_res_query.where(JeuReservation.end_date <= end.date())

        jeu_reservations = db.session.scalars(jeu_res_query).all()
        cj_id, cj_name, jeux_color, jeux_contrast = JeuReservation.get_club_display_info()

        for res in jeu_reservations:
            if not res.jeu:
                continue
            end_dt = datetime.datetime.combine(res.end_date, datetime.time.min)
            events_list.append({
                "id": f"jeu_res_{res.id}",
                "title": res.calendar_title,
                "start": end_dt.isoformat(),
                "end": (end_dt + datetime.timedelta(days=1)).isoformat(),
                "allDay": True,
                "color": jeux_color,
                "can_edit": False,
                "extendedProps": {
                    "description": res.calendar_description,
                    "location": res.calendar_location,
                    "club": cj_name,
                    "club_id": cj_id,
                    "contrast_color": jeux_contrast,
                }
            })

    min_vac_year = start.year if start_str else datetime.date.today().year - 1
    for idx, vac in enumerate(get_espci_vacations(min_year=min_vac_year)):
        if start_str and vac.end_date < start.date():
            continue
        if end_str and vac.start_date > end.date():
            continue
        vac_start_dt = datetime.datetime.combine(vac.start_date, datetime.time.min)
        vac_end_dt = datetime.datetime.combine(vac.end_date, datetime.time.min)
        events_list.append({
            "id": f"vac_{vac.start_date.isoformat()}_{idx}",
            "title": vac.title,
            "start": vac_start_dt.isoformat(),
            "end": vac_end_dt.isoformat(),
            "allDay": True,
            "color": "#198754",
            "can_edit": False,
            "extendedProps": {
                "description": _(
                    "%(title)s (du %(start)s au %(end)s).",
                    title=vac.title,
                    start=vac.start_date.strftime("%d/%m/%Y"),
                    end=vac.end_date.strftime("%d/%m/%Y"),
                ),
                "location": None,
                "club": _("Vacances scolaires"),
                "club_id": None,
                "contrast_color": "#ffffff",
            },
        })

    return flask.jsonify(events_list)

@bp.route("/api/events/edit/<int:event_id>", methods=["POST"])
@context.logged_in_only
def edit_event(event_id: int):
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

    try:
        start_time = datetime.datetime.fromisoformat(start_time_str)
        end_time = datetime.datetime.fromisoformat(end_time_str)
    except ValueError:
        flask.abort(400, "Invalid date format")

    if (all_day and end_time < start_time) or (not all_day and end_time <= start_time):
        return flask.jsonify({"status": "error", "message": "La fin de l'évènement doit être après le début."}), 400

    event.title = title
    event.club = new_club
    event.start_time = start_time
    event.end_time = end_time
    event.location = location
    event.description = description
    event.all_day = all_day

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

    if (all_day and end_time < start_time) or (not all_day and end_time <= start_time):
        return flask.jsonify({"status": "error", "message": "La fin de l'évènement doit être après le début."}), 400

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

@bp.route("/api/events/delete/<int:event_id>", methods=["POST", "DELETE"])
@context.logged_in_only
def delete_event(event_id: int):
    """API route to delete an event."""
    event = db.session.get(Event, event_id)
    if not event:
        flask.abort(404, "Event not found")

    if not context.has_permission(PermissionType.write, PermissionScope.calendar):
        flask.abort(403, "You do not have permission to delete events in the calendar.")

    db.session.delete(event)
    db.session.commit()
    
    return flask.jsonify({
        "status": "success",
        "message": str(_("Évènement supprimé avec succès."))
    })

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
    proj_root = os.path.dirname(flask.current_app.root_path)
    return flask.send_from_directory(
        safe_join(proj_root, "node_modules", "fullcalendar"),
        "index.global.min.js"
    )

def _finalize_ics_event(
    e: ics.Event,
    club_name: str | None,
    club_color: str | None,
    now_utc_str: str,
) -> None:
    """Attach club metadata and standard iCalendar headers to an ics.Event."""
    if club_name:
        e.categories = {club_name}
        e.description = f"[{club_name}]\n{e.description}" if e.description else f"[{club_name}]"
    if club_color:
        e.extra.append(ContentLine(name="COLOR", value=club_color))
    for name, value in (
        ("DTSTAMP", now_utc_str),
        ("CREATED", now_utc_str),
        ("LAST-MODIFIED", now_utc_str),
        ("SEQUENCE", "0"),
        ("STATUS", "CONFIRMED"),
        ("TRANSP", "TRANSPARENT"),
    ):
        e.extra.append(ContentLine(name=name, value=value))


@bp.route("/feed/<token>/calendrier.ics")
def export_feed(token: str):
    """Export the calendar as an iCalendar feed."""
    pceen = PCeen.verify_calendar_token(token)
    if not pceen:
        flask.abort(404)
    if not pceen.has_permission(PermissionType.read, PermissionScope.calendar):
        flask.abort(403)
        
    cal = ics.Calendar()
    cal.creator = "PC est magique"
    cal.extra.append(ContentLine(name='X-WR-CALNAME', value='Calendrier PCéen'))
    cal.extra.append(ContentLine(name='NAME', value='Calendrier PCéen'))
    cal.extra.append(ContentLine(name='X-WR-TIMEZONE', value='Europe/Paris'))
    cal.extra.append(ContentLine(name='X-WR-CALDESC', value='Calendrier des évènements de PC est magique'))
    cal.extra.append(ContentLine(name='DESCRIPTION', value='Calendrier des évènements de PC est magique'))
    
    three_years_ago = datetime.datetime.now() - datetime.timedelta(days=3 * 365)
    now_utc_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    tz = zoneinfo.ZoneInfo("Europe/Paris")
    
    events = db.session.scalars(
        db.select(Event).filter(Event.start_time >= three_years_ago)
    ).all()
    spectacles = db.session.scalars(
        db.select(ClubQSpectacle)
        .join(ClubQVoeu)
        .where(
            ClubQSpectacle.date >= three_years_ago,
            ClubQVoeu._pceen_id == pceen.id,
            ClubQVoeu.places_attribuees > 0,
        )
    ).all()
    
    for event in events:
        e = ics.Event()
        e.name = event.title
        
        if event.all_day:
            e.begin = event.start_time.date()
            e.make_all_day()
            end_date = event.end_time.date() + datetime.timedelta(days=1)
            if end_date <= event.start_time.date():
                end_date = event.start_time.date() + datetime.timedelta(days=1)
            e.end = end_date
        else:
            begin = event.start_time.replace(tzinfo=tz)
            end = event.end_time.replace(tzinfo=tz)
            if end <= begin:
                end = begin + datetime.timedelta(hours=1)
            e.begin = begin
            e.end = end
            
        e.location = event.location
        e.description = event.description
        _finalize_ics_event(
            e,
            event.club.name if event.club else None,
            event.club.color if event.club else None,
            now_utc_str,
        )
        cal.events.add(e)
        
    club_q = db.session.scalars(db.select(Club).filter_by(name=CLUB_Q_NAME)).first()
    for spec in spectacles:
        e = ics.Event()
        e.name = spec.nom
        e.begin = spec.date.replace(tzinfo=tz)
        e.end = (spec.date + datetime.timedelta(hours=2)).replace(tzinfo=tz)
        e.location = spec.salle.nom if spec.salle else None
        e.description = spec.description
        _finalize_ics_event(
            e,
            club_q.name if club_q else None,
            club_q.color if club_q else None,
            now_utc_str,
        )
        cal.events.add(e)

    jeu_reservations = db.session.scalars(
        db.select(JeuReservation)
        .options(selectinload(JeuReservation.jeu))
        .where(
            JeuReservation._pceen_id == pceen.id,
            JeuReservation.cancelled.is_(False),
            JeuReservation.end_date >= three_years_ago.date(),
        )
    ).all()
    _cj_id, cj_name, cj_color, _cj_contrast = JeuReservation.get_club_display_info()
    for res in jeu_reservations:
        if not res.jeu:
            continue
        e = ics.Event()
        e.name = res.calendar_title
        e.begin = res.end_date
        e.make_all_day()
        e.end = res.end_date + datetime.timedelta(days=1)
        e.location = res.calendar_location
        e.description = res.calendar_description
        _finalize_ics_event(e, cj_name, cj_color, now_utc_str)
        cal.events.add(e)

    if flask.request.args.get("vacances") == "1":
        for vac in get_espci_vacations(min_year=three_years_ago.year):
            e = ics.Event()
            e.name = vac.title
            e.begin = vac.start_date
            e.make_all_day()
            e.end = vac.end_date
            e.description = str(
                _(
                    "%(title)s (du %(start)s au %(end)s).",
                    title=vac.title,
                    start=vac.start_date.strftime("%d/%m/%Y"),
                    end=vac.end_date.strftime("%d/%m/%Y"),
                )
            )
            _finalize_ics_event(e, str(_("Vacances scolaires")), "#198754", now_utc_str)
            cal.events.add(e)

    return flask.Response(cal.serialize(), mimetype="text/calendar")

