"""PC est magique - Main Pages Routes"""

from collections import namedtuple
import base64
import datetime
import hashlib
import logging
import os

import flask
from flask_babel import _
from discord_webhook import DiscordWebhook
from markupsafe import Markup, escape
import sqlalchemy

from app import context, db
from app.models import (
    Ban,
    PermissionScope,
    PermissionType,
    Collection,
    Album,
    Photo,
    GlobalSetting,
    ClubQSeason,
    ClubQVoeu,
    ClubQSpectacle,
    Bekk,
    OrderPanierBio,
    PeriodPanierBio,
    Event,
    InfoBanner,
    InfoBannerPreset,
)
from app.routes.main import bp, forms
from app.utils import captcha, helpers, typing
from app.utils.global_settings import Settings
from app.routes.club_q.utils import pceen_prix_total
from app.routes.panier_bio.utils import command_open, what_are_next_days


@bp.route("/")
@bp.route("/index")
@context.logged_in_only
def index() -> typing.RouteReturn:
    """PC est magique home page."""
    pceen = context.g.pceen
    photos_infos = None
    if context.has_permission(PermissionType.read, PermissionScope.photos):
        photos_infos = namedtuple("PhotosInfos", ["nb_collections", "nb_albums", "nb_photos"])(
            db.session.scalar(db.select(sqlalchemy.func.count()).select_from(Collection)),
            db.session.scalar(db.select(sqlalchemy.func.count()).select_from(Album)),
            db.session.scalar(db.select(sqlalchemy.func.count()).select_from(Photo)),
        )

    club_q_infos = None
    if context.has_permission(PermissionType.read, PermissionScope.club_q):

        season_id = db.session.scalars(db.select(GlobalSetting).filter_by(key="SEASON_NUMBER_CLUB_Q")).one().value
        season = db.session.scalars(db.select(ClubQSeason).filter_by(id=season_id)).first()

        next_voeu = db.session.scalars(
            db.select(ClubQVoeu).filter(
                ClubQVoeu._pceen_id == pceen.id,
                ClubQVoeu.places_attribuees > 0,
                ClubQVoeu.spectacle.has(ClubQSpectacle.date > datetime.date.today()),
            )
        ).first()

        voeux = db.select(ClubQVoeu).filter_by(_pceen_id=pceen.id, _season_id=season_id)
        if db.session.scalars(voeux).first() is not None:
            to_pay = pceen_prix_total(pceen, voeux)
        else:
            to_pay = 0

        visibility = db.session.scalars(db.select(GlobalSetting).filter_by(key="ACCESS_CLUB_Q")).one().value

        club_q_infos = namedtuple("ClubQInfos", ["season", "next_voeu", "to_pay", "booking_open", "pceen"])(
            season,
            next_voeu,
            to_pay,
            visibility,
            pceen,
        )

    bekk_infos = None
    if context.has_permission(PermissionType.read, PermissionScope.bekk):

        bekks_stmt = db.select(Bekk).order_by(Bekk.date)
        last_bekk = db.session.scalars(bekks_stmt).first()

        if last_bekk is None:
            bekk_infos = namedtuple("BekkInfos", ["last_bekk", "promo", "nb_bekks", "last_bekk_id"])(
                "Aucun", "-", 0, -1
            )
        else:
            nb_bekks = db.session.scalar(db.select(sqlalchemy.func.count()).select_from(Bekk))
            bekk_infos = namedtuple("BekkInfos", ["last_bekk", "promo", "nb_bekks", "last_bekk_id"])(
                last_bekk.name, last_bekk.promo, nb_bekks, last_bekk.id
            )

    panier_bio_infos = None
    
    panier_bio_day = db.session.scalars(db.select(GlobalSetting).filter_by(key="PANIER_BIO_DAY")).one().value
    today = datetime.date.today()
    all_periods = db.session.scalars(
        db.select(PeriodPanierBio).filter_by(active=True)
        .filter(PeriodPanierBio.end_date >= today)
        .order_by(PeriodPanierBio.start_date.asc())
    ).all()
    
    next_days  = what_are_next_days(panier_bio_day, today, all_periods)
    if len(next_days) > 0:
        next_day = next_days[0]
    else:
        next_day = None
        
    all_orders = db.session.scalars(
        db.select(OrderPanierBio).filter_by(_pceen_id=pceen.id)
        .filter(OrderPanierBio.date >= today)
        .order_by(OrderPanierBio.date.asc())
    ).all()

    visibility = db.session.scalars(db.select(GlobalSetting).filter_by(key="ACCESS_PANIER_BIO")).one().value

    reserved = False
    for order in all_orders:
        if order.date == next_day:
            reserved = True

    panier_bio_infos = namedtuple("PanierBioInfos", ["visibility","next_day", "reserved"])(
                visibility, next_day, reserved
            )

    calendar_infos = None
    if context.has_permission(PermissionType.read, PermissionScope.calendar):
        next_real_events = db.session.scalars(
            db.select(Event)
            .where(Event.start_time >= datetime.datetime.now())
            .order_by(Event.start_time.asc())
            .limit(3)
        ).all()
    
        class DisplayEvent:
            def __init__(self, title, start_time, club_name, location, all_day):
                self.title = title
                self.start_time = start_time
                self.club = type('obj', (object,), {'name': club_name})()
                self.location = location
                self.all_day = all_day
    
        display_events = [DisplayEvent(e.title, e.start_time, e.club.name, e.location, e.all_day) for e in next_real_events]
    
        next_spectacles = db.session.scalars(
            db.select(ClubQSpectacle)
            .join(ClubQVoeu)
            .where(
                ClubQSpectacle.date >= datetime.datetime.now(),
                ClubQVoeu._pceen_id == pceen.id,
                ClubQVoeu.places_attribuees > 0,
            )
            .order_by(ClubQSpectacle.date.asc())
            .limit(3)
        ).all()
    
        display_events.extend([DisplayEvent(s.nom, s.date, "Club Q", s.salle.nom if s.salle else None, False) for s in next_spectacles])
        display_events.sort(key=lambda e: e.start_time)
        display_events = display_events[:3]
    
        calendar_infos = namedtuple("CalendarInfos", ["next_events"])(display_events)

    banners = []
    autoplay_delay = 8
    if calendar_infos:
        try:
            banners = db.session.scalars(db.select(InfoBanner).order_by(InfoBanner.order_index.asc())).all()
            autoplay_delay = Settings.carousel_autoplay_delay
        except Exception:
            pass

    return flask.render_template(
        "main/index.html",
        title=_("Accueil"),
        photos_infos=photos_infos,
        bekk_infos=bekk_infos,
        club_q_infos=club_q_infos,
        panier_bio_infos=panier_bio_infos,
        calendar_infos=calendar_infos,
        banners=banners,
        autoplay_delay=autoplay_delay
    )


@bp.route("/contact", methods=["GET", "POST"])
def contact() -> typing.RouteReturn:
    """PC est magique contact page."""
    form = forms.ContactForm()
    if form.validate_on_submit():
        if not captcha.verify_captcha():
            flask.flash(
                _("Le captcha n'a pas pu être vérifié. Veuillez réessayer."),
                "danger",
            )
        else:
            role_id = flask.current_app.config["GRI_ROLE_ID"]
            webhook = DiscordWebhook(
                url=flask.current_app.config["MESSAGE_WEBHOOK"],
                content=f"<@&{role_id}> Nouveau message !",
            )
            webhook.add_embed(form.create_embed())
            rep = webhook.execute()
            if rep:
                flask.flash(_("Message transmis !"), "success")
                return helpers.ensure_safe_redirect("main.index")

            flask.flash(
                Markup(
                    _(
                        "Oh non ! Le message n'a pas pu être transmis. N'hésitez pas "
                        "à contacter un GRI aux coordonnées en bas de page.<br/>"
                        "(Erreur : "
                    )
                    + f"<code>{rep.code} / {rep.text}</code>)"
                ),
                "danger",
            )

    return flask.render_template("main/contact.html", title=_("Contact"), form=form)


@bp.route("/legal")
def legal() -> typing.RouteReturn:
    """PC est magique legal page."""
    return flask.render_template("main/legal.html", title=_("Mentions légales"))


@bp.route("/changelog")
def changelog() -> typing.RouteReturn:
    """PC est magique changelog page."""
    return flask.render_template("main/changelog.html", title=_("Notes de mise à jour"), datetime=datetime)


@bp.route("/connect_check")
@context.internal_only
def connect_check() -> typing.RouteReturn:
    """Connect check page."""
    return flask.render_template("main/connect_check.html", title=_("Accès à Internet"))


@bp.route("/banned")
def banned() -> typing.RouteReturn:
    """Page shown when the Rezident is banned."""
    try:
        ban = db.session.get(Ban, context.g._ban)
    except AttributeError:
        return helpers.redirect_to_next()
    return flask.render_template("main/banned.html", ban=ban, title=_("Accès à Internet restreint"))


@bp.route("/home")
def rickroll() -> typing.RouteReturn:
    """The old good days..."""
    if context.g.logged_in:
        with open("logs/rickrolled.log", "a") as fh:
            fh.write(f"{datetime.datetime.now()}: rickrolled " f"{context.g.pceen.full_name}\n")
    return flask.redirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ")


@bp.route("/test")
@context.gris_only
def test() -> typing.RouteReturn:
    """Test page."""
    return flask.render_template("main/test.html", title=_("TEST"))


@bp.route("/test_mail/<blueprint>/<template>")
@context.gris_only
def test_mail(blueprint: str, template: str) -> typing.RouteReturn:
    """Mails test route"""
    from app.email import process_html, html_to_plaintext

    body = flask.render_template(f"{blueprint}/mails/{template}.html", pceen=context.g.pceen)
    body = process_html(body)
    if flask.request.args.get("txt"):
        return f"<pre>{escape(html_to_plaintext(body))}</pre>"
    else:
        return body


def _check_md5(album_src: str) -> bool:
    """Check md5 token (fallback if no Nginx, should NOT bu used!)"""
    token = flask.request.args.get("md5")
    expires = flask.request.args.get("expires")
    if not token or not expires or not expires.isdigit():
        return False
    expires_ts = int(expires)
    ip = flask.request.headers.get("X-Real-Ip") or flask.current_app.config["FORCE_IP"]
    if not ip:
        return False
    secret = flask.current_app.config["PHOTOS_SECRET_KEY"]
    md5 = hashlib.md5(f"{expires_ts}{album_src}{ip} {secret}".encode())
    b64 = base64.urlsafe_b64encode(md5.digest()).replace(b"=", b"")
    return b64.decode() == token


@bp.route("/photo/<collection_dir>/<album_dir>/<photo_file>")
@bp.route("/photo/<collection_dir>/<album_dir>/_thumbs/<photo_file>")
def photo(collection_dir: str, album_dir: str, photo_file: str) -> typing.RouteReturn:
    """Serve photo (fallback if no Nginx, should NOT bu used!)"""
    logging.warning("Photo served by Flask and not nginx!")
    if not _check_md5(f"/photo/{collection_dir}/{album_dir}"):
        # Bad token: redirect to photos.photo to build new token (if
        # authorized) then redirect back here
        return flask.redirect(flask.request.url.replace("/photo/", "/photos/"))
    base_dir = os.path.join(
        flask.current_app.config["PHOTOS_BASE_PATH"],
        collection_dir,
        album_dir,
    )
    target_dir = os.path.join(base_dir, "_thumbs") if "/_thumbs/" in flask.request.url else base_dir
    return flask.send_from_directory(target_dir, photo_file)


@bp.route("/bar_avatars/<promo>/<filename>")
def bar_avatar(promo: str, filename: str) -> typing.RouteReturn:
    """Serve bar avatar (fallback if no Nginx, should NOT be used!)"""
    target_dir = os.path.join(
        flask.current_app.config["PHOTOS_BASE_PATH"],
        "bar_avatars",
        promo,
    )
    return flask.send_from_directory(target_dir, filename)


@bp.route("/theatre_posters/<saison>/<filename>")
def theatre_posters(saison: str, filename: str) -> typing.RouteReturn:
    """Serve theatre poster (fallback if no Nginx, should NOT be used!)"""
    target_dir = os.path.join(
        flask.current_app.config["THEATRE_BASE_PATH"],
        saison,
    )
    return flask.send_from_directory(target_dir, filename)


@bp.route("/bekks/<filename>")
def bekks(filename: str) -> typing.RouteReturn:
    """Serve Bekks files (fallback if no Nginx, should NOT be used!)"""
    logging.warning("Bekk served by Flask and not nginx!")

    target_dir = flask.current_app.config["BEKKS_BASE_PATH"]
    return flask.send_from_directory(target_dir, filename)


@bp.route("/club_q_images/<season_id>/<filename>")
def club_q_images(season_id: str, filename: str) -> typing.RouteReturn:
    """Serve Club Q files (fallback if no Nginx, should NOT be used!)"""
    logging.warning("Club Q served by Flask and not nginx!")

    target_dir = os.path.join(flask.current_app.config["CLUB_Q_BASE_PATH"], season_id)
    return flask.send_from_directory(target_dir, filename)


@bp.route("/club_q_plaquettes/<filename>")
def club_q_plaquettes(filename: str) -> typing.RouteReturn:
    """Serve Club Q files (fallback if no Nginx, should NOT be used!)"""
    logging.warning("Club Q served by Flask and not nginx!")

    target_dir = os.path.join(flask.current_app.config["CLUB_Q_BASE_PATH"], "plaquettes")
    return flask.send_from_directory(target_dir, filename)


@bp.route("/custom_files/<folder>/<filename>")
def custom_files(folder: str, filename: str) -> typing.RouteReturn:
    """Serve WYSIYG files (fallback if no Nginx, should NOT be used!)"""
    logging.warning("WYSIYG served by Flask and not nginx!")
    if folder == "club_q":
        target_dir = flask.current_app.config["CLUB_Q_BASE_PATH"]
    elif folder == "bekk":
        target_dir = flask.current_app.config["BEKK_BASE_PATH"]
    else:
        flask.abort(404)
        
    return flask.send_from_directory(target_dir, filename)


@bp.route("/set_theme/<theme>")
def set_theme(theme: str) -> typing.RouteReturn:
    """Set the interface theme."""
    valid_themes = ["material", "frost", "classic"]
    if theme not in valid_themes:
        theme = "material"
    
    resp = flask.make_response(helpers.redirect_to_next())
    resp.set_cookie("theme", theme, max_age=60*60*24*365)
    return resp

@bp.route("/set_mode/<mode>")
def set_mode(mode: str) -> typing.RouteReturn:
    """Set the interface custom mode (light/dark/auto)."""
    valid_modes = ["light", "dark", "auto"]
    if mode not in valid_modes:
        mode = "auto"
    
    resp = flask.make_response(helpers.redirect_to_next())
    resp.set_cookie("mode", mode, max_age=60*60*24*365)
    return resp


@bp.route("/banners/img/<filename>")
@context.permission_only(PermissionType.read, PermissionScope.calendar)
def serve_banner_file(filename: str) -> typing.RouteReturn:
    """Serve uploaded banner images to users with calendar access."""
    return flask.send_from_directory(flask.current_app.config["BANNERS_BASE_PATH"], filename)


@bp.route("/banners/download/<int:banner_id>")
@context.permission_only(PermissionType.read, PermissionScope.calendar)
def download_banner_file(banner_id: int) -> typing.RouteReturn:
    """Download the attached file of a banner."""
    banner = db.session.get(InfoBanner, banner_id)
    if not banner or not banner.file_filename:
        flask.abort(404)
    return flask.send_from_directory(
        flask.current_app.config["BANNERS_BASE_PATH"],
        banner.file_filename,
        as_attachment=True,
        download_name=banner.file_original_name
    )


def _process_banner_form(banner: InfoBanner, form: forms.BannerForm, is_new: bool = False) -> bool:
    """Banner forms for creation and editing."""
    error = False
    
    img_file = flask.request.files.get("image_file")
    att_file = flask.request.files.get("attached_file")
    
    if not form.is_text.data:
        if not banner.image_filename and (not img_file or not img_file.filename):
            flask.flash(_("Une image est requise pour une bannière de type image."), "danger")
            error = True
        elif img_file and img_file.filename:
            img_file.seek(0, os.SEEK_END)
            size = img_file.tell()
            img_file.seek(0)
            if size > 10 * 1024 * 1024:
                flask.flash(_("L'image de la bannière dépasse la taille maximale de 10 Mo."), "danger")
                error = True
                
    if att_file and att_file.filename:
        att_file.seek(0, os.SEEK_END)
        size = att_file.tell()
        att_file.seek(0)
        if size > 10 * 1024 * 1024:
            flask.flash(_("Le fichier joint dépasse la taille maximale de 10 Mo."), "danger")
            error = True
            
    if not error:
        os.makedirs(flask.current_app.config["BANNERS_BASE_PATH"], exist_ok=True)
        
        banner.title = form.title.data
        banner.is_text = form.is_text.data
        banner.text_content = form.text_content.data if form.is_text.data else None
        banner.background_color = form.background_color.data or "#152f4e"
        banner.text_color = form.text_color.data or "#ffffff"
        banner.link_url = form.link_url.data or None
        banner._preset_id = form.preset_id.data
        banner.icon = form.icon.data or None
        banner.text_alignment = form.text_alignment.data or "center"
        banner.layout_style = form.layout_style.data or "vertical"
        banner.overlay_opacity = form.overlay_opacity.data if form.overlay_opacity.data is not None else 70
        
        if img_file and img_file.filename:
            if not is_new and banner.image_filename:
                old_path = os.path.join(flask.current_app.config["BANNERS_BASE_PATH"], banner.image_filename)
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except Exception as e:
                        logging.error(f"Error removing old banner image: {e}")
            
            ext = os.path.splitext(img_file.filename)[1]
            safe_name = f"banner_{int(datetime.datetime.utcnow().timestamp())}{ext}"
            img_file.save(os.path.join(flask.current_app.config["BANNERS_BASE_PATH"], safe_name))
            banner.image_filename = safe_name
            
        if att_file and att_file.filename:
            if not is_new and banner.file_filename:
                old_path = os.path.join(flask.current_app.config["BANNERS_BASE_PATH"], banner.file_filename)
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except Exception as e:
                        logging.error(f"Error removing old banner attachment: {e}")
            
            ext = os.path.splitext(att_file.filename)[1]
            safe_name = f"file_{int(datetime.datetime.utcnow().timestamp())}{ext}"
            att_file.save(os.path.join(flask.current_app.config["BANNERS_BASE_PATH"], safe_name))
            banner.file_filename = safe_name
            banner.file_original_name = att_file.filename
            
        if is_new:
            max_order = db.session.scalar(db.select(sqlalchemy.func.max(InfoBanner.order_index))) or 0
            banner.order_index = max_order + 1
            db.session.add(banner)
            
        db.session.commit()
        return True
        
    return False


@bp.route("/banners/admin", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.calendar)
def manage_banners() -> typing.RouteReturn:
    """Manage banners: add a new banner or view the list."""
    form = forms.BannerForm()
    config_form = forms.CarouselConfigForm()

    # Populate preset choices
    presets = db.session.scalars(db.select(InfoBannerPreset).order_by(InfoBannerPreset.name)).all()
    preset_choices = [(None, _("— Pas de preset —"))] + [(p.id, p.name) for p in presets]
    form.preset_id.choices = preset_choices

    if flask.request.method == "GET":
        try:
            config_form.autoplay_delay.data = Settings.carousel_autoplay_delay
        except Exception:
            config_form.autoplay_delay.data = 6

    if form.submit.data and form.validate():
        banner = InfoBanner()
        if _process_banner_form(banner, form, is_new=True):
            flask.flash(_("Bannière ajoutée avec succès."), "success")
            return flask.redirect(flask.url_for("main.manage_banners"))
            
    elif config_form.submit.data and config_form.validate():
        Settings.carousel_autoplay_delay = config_form.autoplay_delay.data
        flask.flash(_("Configuration du carrousel mise à jour."), "success")
        return flask.redirect(flask.url_for("main.manage_banners"))
            
    banners = db.session.scalars(db.select(InfoBanner).order_by(InfoBanner.order_index.asc())).all()
    return flask.render_template(
        "main/manage_banners.html",
        form=form,
        config_form=config_form,
        banners=banners,
        presets=presets,
    )


@bp.route("/banners/edit/<int:banner_id>", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.calendar)
def edit_banner(banner_id: int) -> typing.RouteReturn:
    """Edit an existing banner."""
    banner = db.session.get(InfoBanner, banner_id)
    if not banner:
        flask.abort(404)
        
    form = forms.BannerForm(obj=banner)
    
    # Populate preset choices
    presets = db.session.scalars(db.select(InfoBannerPreset).order_by(InfoBannerPreset.name)).all()
    preset_choices = [(None, _("— Pas de preset —"))] + [(p.id, p.name) for p in presets]
    form.preset_id.choices = preset_choices

    if form.validate_on_submit():
        if _process_banner_form(banner, form, is_new=False):
            flask.flash(_("Bannière mise à jour."), "success")
            return flask.redirect(flask.url_for("main.manage_banners"))

    elif flask.request.method == "GET":
        # Pre-populate new fields from the banner object
        form.preset_id.data = banner._preset_id
        form.icon.data = banner.icon or ""
        form.text_alignment.data = banner.text_alignment
        form.layout_style.data = banner.layout_style
        form.overlay_opacity.data = banner.overlay_opacity
        
    return flask.render_template("main/edit_banner.html", form=form, banner=banner, presets=presets)


@bp.route("/banners/edit/<int:banner_id>/delete_file", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.calendar)
def delete_banner_file(banner_id: int) -> typing.RouteReturn:
    """Delete the attached file of a banner."""
    banner = db.session.get(InfoBanner, banner_id)
    if not banner or not banner.file_filename:
        flask.abort(404)
        
    old_path = os.path.join(flask.current_app.config["BANNERS_BASE_PATH"], banner.file_filename)
    if os.path.exists(old_path):
        try:
            os.remove(old_path)
        except Exception as e:
            logging.error(f"Error removing banner attachment: {e}")
            
    banner.file_filename = None
    banner.file_original_name = None
    db.session.commit()
    flask.flash(_("Fichier joint supprimé."), "success")
    return flask.redirect(flask.url_for("main.edit_banner", banner_id=banner_id))


@bp.route("/banners/delete/<int:banner_id>", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.calendar)
def delete_banner(banner_id: int) -> typing.RouteReturn:
    """Delete a banner."""
    banner = db.session.get(InfoBanner, banner_id)
    if not banner:
        flask.abort(404)
        
    if banner.image_filename:
        path = os.path.join(flask.current_app.config["BANNERS_BASE_PATH"], banner.image_filename)
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                logging.error(f"Error removing banner image: {e}")
                
    if banner.file_filename:
        path = os.path.join(flask.current_app.config["BANNERS_BASE_PATH"], banner.file_filename)
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                logging.error(f"Error removing banner file: {e}")
                
    db.session.delete(banner)
    db.session.commit()
    flask.flash(_("Bannière supprimée."), "success")
    return flask.redirect(flask.url_for("main.manage_banners"))


@bp.route("/banners/reorder", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.calendar)
def reorder_banners() -> typing.RouteReturn:
    """Update display order of all banners."""
    if flask.request.is_json:
        data = flask.request.get_json()
        banner_ids = data.get("banner_ids") if data else None
    else:
        banner_ids = flask.request.form.getlist("banner_ids[]")
        
    if banner_ids:
        for index, b_id in enumerate(banner_ids):
            try:
                banner = db.session.get(InfoBanner, int(b_id))
                if banner:
                    banner.order_index = index
            except (ValueError, TypeError):
                continue
        db.session.commit()
        flask.flash(_("Ordre des bannières mis à jour."), "success")
        return flask.jsonify({"status": "success"})
        
    return flask.jsonify({"status": "error", "message": "No IDs provided"}), 400


@bp.route("/banners/presets", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.calendar)
def manage_presets() -> typing.RouteReturn:
    """Manage banner style presets: list, create, and edit."""
    form = forms.PresetForm()

    if form.validate_on_submit():
        img_file = flask.request.files.get("image_file")
        preset_id = form.id.data
        if preset_id:
            preset = db.session.get(InfoBannerPreset, int(preset_id))
            if not preset:
                flask.abort(404)
        else:
            preset = InfoBannerPreset()
            db.session.add(preset)

        preset.name = form.name.data
        preset.background_color = form.background_color.data or "#152f4e"
        preset.text_color = form.text_color.data or "#ffffff"
        preset.icon = form.icon.data or None
        preset.text_alignment = form.text_alignment.data or "center"
        preset.layout_style = form.layout_style.data or "vertical"
        preset.overlay_opacity = form.overlay_opacity.data if form.overlay_opacity.data is not None else 70

        if img_file and img_file.filename:
            img_file.seek(0, os.SEEK_END)
            size = img_file.tell()
            img_file.seek(0)
            if size > 10 * 1024 * 1024:
                flask.flash(_("L'image dépasse la taille maximale de 10 Mo."), "danger")
            else:
                os.makedirs(flask.current_app.config["BANNERS_BASE_PATH"], exist_ok=True)
                # Remove old image if it exists
                if preset.image_filename:
                    old_path = os.path.join(flask.current_app.config["BANNERS_BASE_PATH"], preset.image_filename)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except Exception as e:
                            logging.error(f"Error removing old preset image: {e}")
                ext = os.path.splitext(img_file.filename)[1]
                safe_name = f"preset_{int(datetime.datetime.utcnow().timestamp())}{ext}"
                img_file.save(os.path.join(flask.current_app.config["BANNERS_BASE_PATH"], safe_name))
                preset.image_filename = safe_name

        db.session.commit()
        flask.flash(_("Preset enregistré."), "success")
        return flask.redirect(flask.url_for("main.manage_presets"))

    presets = db.session.scalars(db.select(InfoBannerPreset).order_by(InfoBannerPreset.name)).all()
    return flask.render_template("main/manage_presets.html", form=form, presets=presets, title=_("Gestion des presets"))


@bp.route("/banners/presets/delete/<int:preset_id>", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.calendar)
def delete_preset(preset_id: int) -> typing.RouteReturn:
    """Delete a banner style preset."""
    preset = db.session.get(InfoBannerPreset, preset_id)
    if not preset:
        flask.abort(404)
    # Clean up preset image if any
    if preset.image_filename:
        img_path = os.path.join(flask.current_app.config["BANNERS_BASE_PATH"], preset.image_filename)
        if os.path.exists(img_path):
            try:
                os.remove(img_path)
            except Exception as e:
                logging.error(f"Error removing preset image: {e}")
    db.session.delete(preset)
    db.session.commit()
    flask.flash(_("Preset supprimé."), "success")
    return flask.redirect(flask.url_for("main.manage_presets"))


@bp.route("/sw.js")
def service_worker() -> typing.RouteReturn:
    """Serve the service worker with the correct MIME type and scope."""
    response = flask.make_response(flask.send_from_directory("static", "sw.js"))
    response.headers["Content-Type"] = "application/javascript"
    response.headers["Service-Worker-Allowed"] = "/"
    return response
