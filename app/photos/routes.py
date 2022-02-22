"""PC est magique - Photos Gallery Routes"""

import datetime
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
    album_form = forms.EditAlbumForm()
    photo_form = forms.EditPhotoForm()
    if album_form.validate_on_submit():
        if album_form.submit.data:
            # Clicked on sumbit: modify album
            album.name = album_form.name.data
            album.description = album_form.description.data
            album.visible = album_form.visible.data
            album.start = album_form.start.data
            album.end = album_form.end.data
            flask.flash(_("Album modifié avec succès !"), "success")
        else:
            # Didn't (so clicked on star): mark album as featured
            album.collection.featured_album.featured = False
            album.featured = True
            flask.flash(_("Cet album est maintenant la miniature de la "
                          "collection !"), "success")
        db.session.commit()
    elif photo_form.validate_on_submit():
        photo = album.photos.filter_by(
            file_name=photo_form.photo_name.data
        ).first()
        if not photo:
            flask.flash(_("Impossible de modifier la photo !"), "warning")
        elif photo_form.submit.data:
            # Clicked on sumbit: modify photo
            photo.caption = photo_form.caption.data
            photo.author_str = photo_form.author_str.data
            if photo_form.date.data:
                photo.timestamp = datetime.datetime.combine(
                    photo_form.date.data,
                    photo_form.time.data or datetime.time(0, 0),
                )
            else:
                photo.timestamp = None
            photo.lat = photo_form.lat.data
            photo.lng = photo_form.lng.data
            flask.flash(_("Photo modifiée avec succès !"), "success")
            db.session.commit()
        else:
            # Didn't (so clicked on star): mark photo as featured
            photo.album.featured_photo.featured = False
            photo.featured = True
            flask.flash(_("Cette photo est maintenant la miniature de "
                          "l'album !"), "success")
            db.session.commit()

    token_args = album.get_access_token(ip)
    return flask.render_template("photos/album.html", album=album,
                                 token_args=token_args, album_form=album_form,
                                 photo_form=photo_form,
                                 title=f"{album.name} – {collection.name}")


@bp.route("<collection_dir>/<album_dir>/<photo_file>")
@context.logged_in_only
def photo(collection_dir: str, album_dir: str,
          photo_file: str)-> typing.RouteReturn:
    """Photo page: redirect to /photo with token, if access authorized.

    Let's take a little time to explain that:
      * /photos/<collection>/<album>/<photo> (this route), served by Flask,
            checks authorization to see the photo (user must be logged in)
            then (if OK) creates the security token and redirects to:
      * /photo/<collection>/<album>/<photo>, served by Nginx, that checks
            the security token and:
            * if OK, serves the photo;
            * if incorrect/expired, redirects to this route. That *could*
              create a redirections loop, if a token just generated by
              Flask is considered invalid by Nginx. This *should* however
              never happen.
    """
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
    token_args = album.get_access_token(ip)
    return flask.redirect(
        f"/photo/{collection_dir}/{album_dir}/{photo_file}?{token_args}"
    )
