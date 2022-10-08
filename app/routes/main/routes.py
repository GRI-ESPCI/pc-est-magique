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

from app import context
from app.models import Ban, PermissionScope, PermissionType, Collection, Album, Photo
from app.routes.main import bp, forms
from app.utils import captcha, helpers, typing


@bp.route("/")
@bp.route("/index")
@context.logged_in_only
def index() -> typing.RouteReturn:
    """PC est magique home page."""
    if context.has_permission(PermissionType.read, PermissionScope.intrarez) and not context.g.intrarez_setup:
        return helpers.safe_redirect(context.g.redemption_endpoint, **context.g.redemption_params)

    photos_infos = None
    if context.has_permission(PermissionType.read, PermissionScope.photos):
        photos_infos = namedtuple("PhotosInfos", ["nb_collections", "nb_albums", "nb_photos"])(
            len(Collection.query.all()),
            len(Album.query.all()),
            len(Photo.query.all()),
        )

    return flask.render_template("main/index.html", title=_("Accueil"), photos_infos=photos_infos)


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

    body = flask.render_template(f"{blueprint}/mails/{template}.html")
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
