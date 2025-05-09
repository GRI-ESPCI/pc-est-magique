"""PC est magique - Main Pages Routes"""

from collections import namedtuple
import base64
import datetime
import hashlib
import logging
import os
import datetime

import flask
from flask_babel import _
from discord_webhook import DiscordWebhook

from app import context
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
    PeriodPanierBio
)
from app.routes.main import bp, forms
from app.utils import captcha, helpers, typing
from datetime import date
from app.routes.club_q.utils import pceen_prix_total
from app.routes.panier_bio.utils import command_open, what_are_next_days


@bp.route("/")
@bp.route("/index")
@context.logged_in_only
def index() -> typing.RouteReturn:
    """PC est magique home page."""
    # if context.has_permission(PermissionType.read, PermissionScope.intrarez) and not context.g.intrarez_setup:
    #    return helpers.safe_redirect(context.g.redemption_endpoint, **context.g.redemption_params)

    pceen = context.g.pceen
    photos_infos = None
    if context.has_permission(PermissionType.read, PermissionScope.photos):
        photos_infos = namedtuple("PhotosInfos", ["nb_collections", "nb_albums", "nb_photos"])(
            len(Collection.query.all()),
            len(Album.query.all()),
            len(Photo.query.all()),
        )

    club_q_infos = None
    if context.has_permission(PermissionType.read, PermissionScope.club_q):

        season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value
        season = ClubQSeason.query.filter_by(id=season_id).first()

        next_voeu = ClubQVoeu.query.filter(
            ClubQVoeu._pceen_id == pceen.id,
            ClubQVoeu.places_attribuees > 0,
            ClubQVoeu.spectacle.has(ClubQSpectacle.date > date.today()),
        ).first()

        voeux = ClubQVoeu.query.filter_by(_pceen_id=pceen.id, _season_id=season_id)
        if voeux.first() is not None:
            to_pay = pceen_prix_total(pceen, voeux)
        else:
            to_pay = 0

        visibility = GlobalSetting.query.filter_by(key="ACCESS_CLUB_Q").one().value

        club_q_infos = namedtuple("ClubQInfos", ["season", "next_voeu", "to_pay", "booking_open", "pceen"])(
            season,
            next_voeu,
            to_pay,
            visibility,
            pceen,
        )

    bekk_infos = None
    if context.has_permission(PermissionType.read, PermissionScope.bekk):

        bekks = Bekk.query.order_by(Bekk.date)
        last_bekk = bekks.first()

        if bekks.first() is None:
            bekk_infos = namedtuple("BekkInfos", ["last_bekk", "promo", "nb_bekks", "last_bekk_id"])(
                "Aucun", "-", 0, -1
            )
        else:
            bekk_infos = namedtuple("BekkInfos", ["last_bekk", "promo", "nb_bekks", "last_bekk_id"])(
                last_bekk.name, last_bekk.promo, bekks.count(), last_bekk.id
            )

    panier_bio_infos = None
    
    panier_bio_day = GlobalSetting.query.filter_by(key="PANIER_BIO_DAY").one().value
    today = datetime.date.today()
    all_periods = PeriodPanierBio.query.filter_by(active=True).filter(PeriodPanierBio.end_date>=today).order_by(PeriodPanierBio.start_date.asc()).all()
    
    next_days  = what_are_next_days(panier_bio_day, today, all_periods)
    if len(next_days) > 0:
        next_day = next_days[0]
    else:
        next_day = None
        
    all_orders = OrderPanierBio.query.filter_by(_pceen_id=pceen.id).filter(OrderPanierBio.date>=today).order_by(OrderPanierBio.date.asc()).all()

    visibility = GlobalSetting.query.filter_by(key="ACCESS_PANIER_BIO").one().value

    reserved = False
    for order in all_orders:
        if order.date == next_day:
            reserved = True

    panier_bio_infos = namedtuple("PanierBioInfos", ["visibility","next_day", "reserved"])(
                visibility, next_day, reserved
            )

    return flask.render_template(
        "main/index.html",
        title=_("Accueil"),
        photos_infos=photos_infos,
        bekk_infos=bekk_infos,
        club_q_infos=club_q_infos,
        panier_bio_infos=panier_bio_infos
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
                flask.Markup(
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
        ban = Ban.query.get(context.g._ban)
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
        return f"<pre>{flask.escape(html_to_plaintext(body))}</pre>"
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
    album_dir = os.path.join(
        flask.current_app.config["PHOTOS_BASE_PATH"],
        collection_dir,
        album_dir,
    )
    if "/_thumbs/" in flask.request.url:
        return flask.send_file(os.path.join(album_dir, "_thumbs", photo_file))
    else:
        return flask.send_file(os.path.join(album_dir, photo_file))


@bp.route("/bar_avatar/<promo>/<filename>")
def bar_avatar(promo: str, filename: str) -> typing.RouteReturn:
    """Serve bar avatar (fallback if no Nginx, should NOT be used!)"""
    filepath = os.path.join(
        flask.current_app.config["PHOTOS_BASE_PATH"],
        "bar_avatars",
        promo,
        filename,
    )
    return flask.send_file(filepath)


@bp.route("/theatre_posters/<saison>/<filename>")
def theatre_posters(saison: str, filename: str) -> typing.RouteReturn:
    """Serve theatre poster (fallback if no Nginx, should NOT be used!)"""
    filepath = os.path.join(
        flask.current_app.config["THEATRE_BASE_PATH"],
        saison,
        filename,
    )
    return flask.send_file(filepath)


@bp.route("/bekks/<filename>")
def bekks(filename: str) -> typing.RouteReturn:
    """Serve Bekks files (fallback if no Nginx, should NOT be used!)"""
    logging.warning("Bekk served by Flask and not nginx!")

    filepath = os.path.join(flask.current_app.config["BEKKS_BASE_PATH"], filename)
    return flask.send_file(filepath)


@bp.route("/club_q_images/<season_id>/<filename>")
def club_q_images(season_id: str, filename: str) -> typing.RouteReturn:
    """Serve Club Q files (fallback if no Nginx, should NOT be used!)"""
    logging.warning("Club Q served by Flask and not nginx!")

    filepath = os.path.join(flask.current_app.config["CLUB_Q_BASE_PATH"], season_id, filename)
    return flask.send_file(filepath)


@bp.route("/club_q_plaquettes/<filename>")
def club_q_plaquettes(filename: str) -> typing.RouteReturn:
    """Serve Club Q files (fallback if no Nginx, should NOT be used!)"""
    logging.warning("Club Q served by Flask and not nginx!")

    filepath = os.path.join(flask.current_app.config["CLUB_Q_BASE_PATH"], "plaquettes", filename)
    return flask.send_file(filepath)


@bp.route("/custom_files/<folder>/<filename>")
def custom_files(folder: str, filename: str) -> typing.RouteReturn:
    """Serve WYSIYG files (fallback if no Nginx, should NOT be used!)"""
    logging.warning("WYSIYG served by Flask and not nginx!")
    if folder == "club_q":
        path = flask.current_app.config["CLUB_Q_BASE_PATH"]
    elif folder == "bekk":
        path = flask.current_app.config["BEKK_BASE_PATH"]
    filepath = os.path.join(path, filename)
    return flask.send_file(filepath)
