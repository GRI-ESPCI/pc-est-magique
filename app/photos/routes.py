"""PC est magique - Main Pages Routes"""

import flask
from flask_babel import _

from app import context
from app.photos import bp
from app.models import Collection
from app.tools import typing


@bp.route("")
@bp.route("/")
@context.logged_in_only
def main() -> typing.RouteReturn:
    """Photos main page (list of collections)."""
    collections = Collection.query.filter_by(visible=True).all()
    # Restrictions d'accès ici (y compris visible=True)
    return flask.render_template("photos/main.html", collections=collections,
                                 title=_("Photos"))


@bp.route("<collection_dir>")
@bp.route("<collection_dir>/")
@context.logged_in_only
def collection(collection_dir: str) -> typing.RouteReturn:
    """Photos collection page (list of albums)."""
    collection = Collection.query.filter_by(dir_name=collection_dir).first()
    if not collection:
        flask.abort(404)
    # Restrictions d'accès ici (y compris visible=True)
    return flask.render_template("photos/collection.html",
                                 collection=collection,
                                 title=collection.name)


@bp.route("<collection_dir>/<album_dir>")
@bp.route("<collection_dir>/<album_dir>/")
@context.logged_in_only
def album(collection_dir: str, album_dir: str) -> typing.RouteReturn:
    """Photos album page (list of photos)."""
    collection = Collection.query.filter_by(dir_name=collection_dir).first()
    if not collection:
        flask.abort(404)
    album = collection.albums.filter_by(dir_name=album_dir).first()
    if not album:
        flask.abort(404)
    # Restrictions d'accès ici (y compris visible=True)
    ip = flask.request.headers.get("X-Real-Ip") or "10.1.2.14"                          # REMOVE THAT
    if not ip:
        flask.flash("IP non détectable, impossible d'accéder aux photos",
                    "danger")
        flask.abort(403)
    md5, expires = album.get_access_token(ip)
    return flask.render_template("photos/album.html", album=album,
                                 md5=md5, expires=expires,
                                 title=f"{album.name} – {collection.name}")


@bp.route("<collection_dir>/<album_dir>/<photo_file>")
@context.logged_in_only
def photo(collection_dir: str, album_dir: str,
          photo_file: str)-> typing.RouteReturn:
    """Photo page: redirect to /photo (served by Nginx directly)."""
    return flask.redirect(f"/photo/{collection_dir}/{album_dir}/{photo_file}")
