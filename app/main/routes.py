"""PC est magique - Main Pages Routes"""

import base64
import datetime
import hashlib
import os

import flask
from flask_babel import _
from discord_webhook import DiscordWebhook

from app import context
from app.main import bp, forms
from app.tools import captcha, utils, typing


@bp.route("/")
@bp.route("/index")
def index() -> typing.RouteReturn:
    """PC est magique home page."""
    return flask.render_template("main/index.html", title=_("Accueil"))


@bp.route("/contact", methods=["GET", "POST"])
def contact() -> typing.RouteReturn:
    """PC est magique contact page."""
    form = forms.ContactForm()
    if form.validate_on_submit():
        if not captcha.verify_captcha():
            flask.flash(_("Le captcha n'a pas pu être vérifié. "
                          "Veuillez réessayer."), "danger")
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
                return utils.ensure_safe_redirect("main.index")

            flask.flash(flask.Markup(_(
                "Oh non ! Le message n'a pas pu être transmis. N'hésitez pas "
                "à contacter un GRI aux coordonnées en bas de page.<br/>"
                "(Erreur : ") + f"<code>{rep.code} / {rep.text}</code>)"),
                "danger"
            )

    return flask.render_template("main/contact.html", title=_("Contact"),
                                 form=form)


@bp.route("/legal")
def legal() -> typing.RouteReturn:
    """PC est magique legal page."""
    return flask.render_template("main/legal.html",
                                 title=_("Mentions légales"))


@bp.route("/changelog")
def changelog() -> typing.RouteReturn:
    """PC est magique changelog page."""
    return flask.render_template("main/changelog.html",
                                 title=_("Notes de mise à jour"),
                                 datetime=datetime)


@bp.route("/test")
@context.gris_only
def test() -> typing.RouteReturn:
    """Test page."""
    return flask.render_template("main/test.html",
                                 title=_("TEST"))


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


def check_md5(album_src: str) -> bool:
    """Check md5 token (fallback if no Nginx, should NOT bu used!)"""
    token = flask.request.args.get("md5")
    expires = flask.request.args.get("expires")
    if not token or not expires or not expires.isdigit():
        return False
    expires_ts = int(expires)
    ip = flask.request.headers.get("X-Real-Ip") or "10.1.2.14"                          # REMOVE THAT
    if not ip:
        return False
    secret = flask.current_app.config["PHOTOS_SECRET_KEY"]
    md5 = hashlib.md5(f"{expires_ts}{album_src}{ip} {secret}".encode())
    b64 = base64.urlsafe_b64encode(md5.digest()).replace(b"=", b"")
    return (b64.decode() == token)


@bp.route("/photo/<collection_dir>/<album_dir>/<photo_file>")
def photo(collection_dir: str, album_dir: str,
          photo_file: str) -> typing.RouteReturn:
    """Serve photo (fallback if no Nginx, should NOT bu used!)"""
    if not check_md5(f"/photo/{collection_dir}/{album_dir}"):
        # Bad token: redirect to photos.photo to build new token (if
        # authorized) then redirect back here
        return flask.redirect(flask.url_for(
            "photos.photo", collection_dir=collection_dir,
            album_dir=album_dir, photo_file=photo_file,
        ))
    return flask.send_file(os.path.join(
        flask.current_app.config["PHOTOS_BASE_PATH"],
        collection_dir,
        album_dir,
        photo_file,
    ))


@bp.route("/photo/<collection_dir>/<album_dir>/_thumbs/<photo_file>")
def photo_thumb(collection_dir: str, album_dir: str,
                photo_file: str) -> typing.RouteReturn:
    """Serve photo thumbnail (fallback if no Nginx, should NOT bu used!)"""
    if not check_md5(f"/photo/{collection_dir}/{album_dir}"):
        # Bad token: redirect to photos.photo to build new token (if
        # authorized) then redirect back here
        return flask.redirect(flask.url_for(
            "photos.photo", collection_dir=collection_dir,
            album_dir=album_dir, photo_file=photo_file,
        ))
    return flask.send_file(os.path.join(
        flask.current_app.config["PHOTOS_BASE_PATH"],
        collection_dir,
        album_dir,
        "_thumbs",
        photo_file,
    ))
