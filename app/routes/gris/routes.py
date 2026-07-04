"""PC est magique - Gris Pages Routes"""

import contextlib
import enum
import io
import traceback
import sys

import flask
from flask_babel import _
from markupsafe import Markup

from app import context, db
from app.routes.gris import bp, forms
from app.models import PCeen, Role, Permission, PermissionScope, PermissionType
from app.routes.gris.utils import (
    add_perm,
    add_remove_role,
    get_perm_elements,
    remove_perm,
    add_edit_ban,
)
from app.utils import helpers, typing

from app.routes.auth import email
from app.routes.auth.utils import new_username

class PCeensViewEnum(enum.Enum):
    active = enum.auto()
    rez = enum.auto()
    bar = enum.auto()
    all = enum.auto()


@bp.route("/pceens", methods=["GET", "POST"])
@bp.route("/pceens/<view>", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.pceen)
def pceens(view: str = "active") -> typing.RouteReturn:
    """PCéens list page."""
    try:
        view = PCeensViewEnum[view]
    except KeyError:
        flask.abort(404)

    roles_form = forms.AddRemoveRoleForm()
    ban_form = forms.BanForm()
    add_pceen_form = forms.AddPCeenForm()
    add_pceen_form.roles.choices = [(r.id, r.name) for r in db.session.scalars(db.select(Role)).all()]

    if add_pceen_form.submit.data:
        if add_pceen_form.validate_on_submit():
            nom = add_pceen_form.nom.data.title()
            prenom = add_pceen_form.prenom.data.title()
            promo = add_pceen_form.promo.data
            
            existing_pceen = PCeen.find_by_fuzzy_name(nom, prenom, promo)
            if existing_pceen:
                flask.flash(_("Un utilisateur avec ce nom, prénom et promo existe déjà (%(nom)s, %(prenom)s, %(promo)s).", nom=existing_pceen.nom, prenom=existing_pceen.prenom, promo=existing_pceen.promo), "danger")
            else:
                pceen = PCeen(
                    username=new_username(prenom, nom),
                    nom=nom,
                    prenom=prenom,
                    promo=promo,
                    email=add_pceen_form.email.data,
                )
                
                # Add selected roles
                for role_id in add_pceen_form.roles.data:
                    role = db.session.get(Role, role_id)
                    if role:
                        pceen.roles.append(role)
                        
                db.session.add(pceen)
                db.session.commit()
                
                creator = flask.g.pceen
                role_names = [r.name for r in pceen.roles]
                log_msg = (
                    f"PCéen created manually by {creator.full_name} (ID: {creator.id}): "
                    f"New PCéen ID={pceen.id}, Nom='{pceen.nom}', Prénom='{pceen.prenom}', "
                    f"Email='{pceen.email}', Roles={role_names}"
                )
                helpers.log_action(log_msg)
                
                flask.flash(_("PCéen %(nom)s %(prenom)s créé avec succès !", nom=pceen.nom, prenom=pceen.prenom), "success")
                
                # Send password setup email
                email.send_password_reset_email(pceen)
        return helpers.redirect_to_next()

    elif ban_form["submit"].data or ban_form["unban"].data:
        if ban_form.validate_on_submit():
            add_edit_ban(
                unban=ban_form.unban.data,
                pceen=ban_form.pceen.data,
                ban_id=ban_form.ban_id.data,
                infinite=ban_form.infinite.data,
                hours=ban_form.hours.data,
                days=ban_form.days.data,
                months=ban_form.months.data,
                reason=ban_form.reason.data,
                message=ban_form.message.data,
            )
    else:
        if roles_form.is_submitted():
            # Check request is well formed
            if roles_form.validate():
                return add_remove_role(
                    roles_form.action.data,
                    roles_form.pceen_id.data,
                    roles_form.role_id.data,
                )
            else:
                return {"message": "Bad formed request", "detail": roles_form.errors}, 400

    page = flask.request.args.get("page", 1, type=int)
    q = flask.request.args.get("q", "").strip()
    sort = flask.request.args.get("sort", "id")
    way = flask.request.args.get("way", "desc")

    stmt = db.select(PCeen)
    if q:
        stmt = stmt.filter(
            db.or_(
                PCeen.nom.ilike(f"%{q}%"),
                PCeen.prenom.ilike(f"%{q}%"),
                PCeen.username.ilike(f"%{q}%"),
                PCeen.email.ilike(f"%{q}%"),
            )
        )

    match view:
        case PCeensViewEnum.active:
            stmt = stmt.filter(PCeen.activated == True)
        case PCeensViewEnum.rez:
            stmt = (
                stmt.join(PCeen.roles)
                .join(Role.permissions)
                .filter(Permission.type == PermissionType.read, Permission.scope == PermissionScope.intrarez)
            )
        case PCeensViewEnum.bar:
            stmt = (
                stmt.join(PCeen.roles)
                .join(Role.permissions)
                .filter(
                    Permission.type == PermissionType.read,
                    Permission.scope.in_([PermissionScope.bar, PermissionScope.bar_stats]),
                )
            )
        case PCeensViewEnum.all:
            pass

    # Sorting
    sort_column = PCeen.id
    if sort == "nom":
        sort_column = PCeen.nom
    elif sort == "prenom":
        sort_column = PCeen.prenom
    elif sort == "promo":
        sort_column = PCeen.promo
    elif sort == "email":
        sort_column = PCeen.email
    elif sort == "username":
        sort_column = PCeen.username
    
    if way == "desc":
        stmt = stmt.order_by(sort_column.desc())
    else:
        stmt = stmt.order_by(sort_column.asc())

    paginator = db.paginate(stmt, page=page, per_page=150, error_out=False)

    return flask.render_template(
        "gris/pceens.html",
        roles_form=roles_form,
        ban_form=ban_form,
        add_pceen_form=add_pceen_form,
        view=view.name,
        pceens=paginator.items,
        paginator=paginator,
        q=q,
        sort=sort,
        way=way,
        roles=db.session.scalars(db.select(Role)).all(),
        title=_("Gestion des PCéens"),
    )


@bp.route("/roles", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.role)
def roles() -> typing.RouteReturn:
    """Roles list page."""
    form = forms.AddRemovePermissionForm()
    if form.is_submitted():
        # Check request is well formed
        if not form.validate():
            return "Bad formed request", 400
        match form.action.data:
            case "get_elements":
                return get_perm_elements(form.scope_name.data)
            case "add":
                return add_perm(
                    form.role_id.data,
                    form.perm_id.data,
                    form.type_name.data,
                    form.scope_name.data,
                    form.ref_id.data,
                )
            case "remove":
                return remove_perm(form.role_id.data, form.perm_id.data)
            case action:
                return f"Invalid action '{action}'", 400

    return flask.render_template(
        "gris/roles.html",
        form=form,
        roles=db.session.scalars(db.select(Role)).all(),
        title=_("Gestion des rôles"),
    )


@bp.route("/run_script", methods=["GET", "POST"])
@context.gris_only
def run_script() -> typing.RouteReturn:
    """Run a PC est magique script."""
    form = forms.ChoseScriptForm()
    if form.validate_on_submit():
        script = form.script.data
        helpers.log_action(f"Executing script from GRI menu: {script}")
        # Exécution du script
        _stdin = sys.stdin
        sys.stdin = io.StringIO()  # Block script for wainting for stdin
        try:
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                with contextlib.redirect_stderr(sys.stdout):
                    try:
                        helpers.run_script(script)
                    except Exception as exc:
                        helpers.log_action(f" -> ERROR: {exc}", warning=True)
                        output = stdout.getvalue() + traceback.format_exc()
                    else:
                        output = stdout.getvalue()
        finally:
            sys.stdin = _stdin

        output_str = str(flask.escape(output))
        output = Markup(output_str.replace("\n", "<br/>").replace(" ", "&nbsp;"))
        return flask.render_template(
            "gris/run_script.html",
            form=form,
            output=output,
            title=_("Exécuter un script"),
        )
    return flask.render_template("gris/run_script.html", form=form, output=None, title=_("Exécuter un script"))


@bp.route("/monitoring_ds")
@context.gris_only
def monitoring_ds() -> typing.RouteReturn:
    """Integration of Darkstat network monitoring."""
    return flask.render_template("gris/monitoring_ds.html", title=_("Darkstat network monitoring"))


@bp.route("/monitoring_bw")
@context.gris_only
def monitoring_bw() -> typing.RouteReturn:
    """Integration of Bandwidthd network monitoring."""
    return flask.render_template("gris/monitoring_bw.html", title=_("Bandwidthd network monitoring"))

def _send_push_notifications(app, subs_data, message, vapid_private_key, vapid_claims):
    import json
    from pywebpush import webpush, WebPushException
    from app import db
    from app.models.push import PushSubscription
    from app.utils import helpers

    with app.app_context():
        success_count = 0
        to_delete = []

        for sub in subs_data:
            try:
                webpush(
                    subscription_info={
                        "endpoint": sub["endpoint"],
                        "keys": {
                            "p256dh": sub["p256dh"],
                            "auth": sub["auth"]
                        }
                    },
                    data=json.dumps(message),
                    vapid_private_key=vapid_private_key,
                    vapid_claims=vapid_claims,
                    headers={"Urgency": "high"}
                )
                success_count += 1
            except WebPushException as ex:
                if ex.response and ex.response.status_code in [404, 410]:
                    to_delete.append(sub["id"])
                else:
                    helpers.log_action(f"Push error: {ex}", warning=True)
            except Exception as e:
                helpers.log_action(f"Push error generic: {e}", warning=True)

        if to_delete:
            import sqlalchemy as sa
            db.session.execute(sa.delete(PushSubscription).where(PushSubscription.id.in_(to_delete)))
            db.session.commit()
            
        helpers.log_action(f"Fin de l'envoi de la notification push '{message['title']}'. Envoyée avec succès à {success_count} / {len(subs_data)} appareils.")

@bp.route("/push_notifications", methods=["GET", "POST"])
@context.gris_only
def push_notifications() -> typing.RouteReturn:
    """Send push notifications to users."""
    import json
    from pywebpush import webpush, WebPushException
    from app.models.push import PushSubscription, Notification

    form = forms.PushNotificationForm()
    form.roles.choices = [(r.id, r.name) for r in db.session.scalars(db.select(Role)).all()]

    if form.validate_on_submit():
        target = form.target.data
        
        stmt = db.select(PushSubscription).join(PCeen)

        if target == "eleves":
            stmt = stmt.filter(PCeen.roles.any(Role.name == "Élève"))
        elif target == "rez":
            from app.models.auth import SubState
            stmt = stmt.filter(PCeen.sub_state.in_([SubState.subscribed, SubState.trial]))
        elif target == "role":
            role_ids = form.roles.data
            stmt = stmt.filter(PCeen.roles.any(Role.id.in_(role_ids)))

        subs = db.session.scalars(stmt).all()

        # Save notification to history first to get ID
        notif = Notification(
            title=form.title.data,
            body=form.body.data,
            image=form.image.data or None,
            url=form.url.data or None,
            target_type=target,
            role_id=form.roles.data[0] if target == "role" and form.roles.data else None
        )
        db.session.add(notif)
        db.session.commit()

        message = {
            "title": form.title.data,
            "body": form.body.data,
            "image": form.image.data or "",
            "url": form.url.data or "/",
            "quiet": form.quiet.data,
            "id": notif.id
        }
        
        vapid_private_key = flask.current_app.config.get("VAPID_PRIVATE_KEY_PATH")
        if not vapid_private_key:
            flask.flash(_("Erreur : la clé VAPID privée n'est pas configurée sur le serveur."), "danger")
            return flask.redirect(flask.url_for("gris.push_notifications"))
            
        mail = flask.current_app.config.get("MAIL_USERNAME") or "admin@example.com"
        vapid_claims = {"sub": f"mailto:{mail}"}

        subs_data = [
            {
                "id": sub.id,
                "endpoint": sub.endpoint,
                "p256dh": sub.p256dh,
                "auth": sub.auth
            }
            for sub in subs
        ]

        import threading
        threading.Thread(
            target=_send_push_notifications,
            args=(flask.current_app._get_current_object(), subs_data, message, vapid_private_key, vapid_claims)
        ).start()

        helpers.log_action(f"Push notification envoyée par ID: {flask.g.pceen.id}, Nom: {flask.g.pceen.prenom} {flask.g.pceen.nom}, Promo: {flask.g.pceen.promo} | Cible: {target} | Titre: '{form.title.data}' | Message: '{form.body.data}'")
        
        flask.flash(_("Notification en cours d'envoi à %(count)d appareils.", count=len(subs_data)), "success")
        return flask.redirect(flask.url_for("gris.push_notifications"))

    return flask.render_template("gris/push_notifications.html", form=form, title=_("Push Notifications"), roles=db.session.scalars(db.select(Role)).all())
    