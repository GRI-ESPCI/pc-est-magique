"""PC est magique - Photos Gallery Routes"""

import flask
from flask_babel import _

from app import context, db
from app.photos import bp, forms
from app.models import Collection
from app.tools import typing


@bp.route("")
@context.logged_in_only
def main() -> typing.RouteReturn:
    """Photos main page (list of collections)."""
    collections = Collection.query.all()
    # Restrictions d'accès ici (y compris visible=True)
    return flask.render_template("photos/main.html", collections=collections,
                                 title=_("Photos"))


@bp.route("<collection_dir>", methods=["GET", "POST"])
@context.logged_in_only
def collection(collection_dir: str) -> typing.RouteReturn:
    """Photos collection page (list of albums)."""
    collection = Collection.query.filter_by(dir_name=collection_dir).first()
    if not collection:
        flask.abort(404)
    # Restrictions d'accès ici (y compris visible=True)
    form = forms.EditCollectionForm()
    if form.validate_on_submit():
        collection.name = form.name.data
        collection.description = form.description.data
        collection.visible = form.visible.data
        collection.start = form.start.data
        collection.end = form.end.data
        flask.flash(_("Collection modifiée avec succès !"), "success")
        db.session.commit()
    return flask.render_template("photos/collection.html", form=form,
                                 collection=collection,
                                 title=collection.name)


@bp.route("<collection_dir>/<album_dir>", methods=["GET", "POST"])
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
    form = forms.EditAlbumForm()
    if form.validate_on_submit():
        if form.submit.data:
            # Clicked on sumbit: modify album
            album.name = form.name.data
            album.description = form.description.data
            album.visible = form.visible.data
            album.start = form.start.data
            album.end = form.end.data
            flask.flash(_("Album modifié avec succès !"), "success")
        else:
            # Didn't (so clicked on star): mark album as featured
            album.collection.albums.update(dict(featured=False))
            flask.flash(_("Cet album est maintenant la miniature de la "
                          "collection !"), "success")
            album.featured = True
        db.session.commit()
    token_args = album.get_access_token(ip)
    return flask.render_template("photos/album.html", album=album,
                                 token_args=token_args, form=form,
                                 title=f"{album.name} – {collection.name}")


@bp.route("<collection_dir>/<album_dir>/<photo_file>")
@context.logged_in_only
def photo(collection_dir: str, album_dir: str,
          photo_file: str)-> typing.RouteReturn:
    """Photo page: redirect to /photo (served by Nginx directly)."""
    return flask.redirect(f"/photo/{collection_dir}/{album_dir}/{photo_file}")
