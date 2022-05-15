"""PC est magique - Photos Gallery Routes"""

import datetime
import flask
from flask_babel import _

from app import context, db
from app.routes.photos import bp, forms
from app.models import Collection, PermissionScope, PermissionType, Photo
from app.utils import typing


@bp.route("")
@context.permission_only(PermissionType.read, PermissionScope.photos)
def main() -> typing.RouteReturn:
    """Photos main page (list of collections)."""
    # Filter collections to display based on permissions
    collections = [
        collection
        for collection in Collection.query.all()
        if context.has_permission(
            collection.view_permission_type, PermissionScope.collection, elem=collection
        )
    ]
    return flask.render_template(
        "photos/main.html", collections=collections, title=_("Photos")
    )


@bp.route("<collection_dir>", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.photos)
def collection(collection_dir: str) -> typing.RouteReturn:
    """Photos collection page (list of albums)."""
    collection = Collection.query.filter_by(dir_name=collection_dir).first()
    if not collection:
        flask.abort(404)

    # Restrict access and filter albums to display based on permissions
    if context.has_permission(
        PermissionType.write, PermissionScope.collection, elem=collection
    ):
        # Write permission: show all albums
        albums = collection.albums.all()
    elif context.has_permission(
        PermissionType.read, PermissionScope.collection, elem=collection
    ):
        # Read permission: show visible albums + hidden albums for which
        # we have a specific write permission
        albums = collection.albums.filter_by(visible=True).all() + [
            album
            for album in collection.albums.filter_by(visible=False).all()
            if context.has_permission(
                PermissionType.write, PermissionScope.album, elem=album
            )
        ]
    else:
        # No permission on collection: check if albums-specific permissions
        albums = [
            album
            for album in collection.albums.all()
            if context.has_permission(
                album.view_permission_type, PermissionScope.album, elem=album
            )
        ]
    if not albums:
        # Nothing to show here
        flask.abort(403)
    # Access OK

    form = forms.EditCollectionForm()
    if form.validate_on_submit():
        collection.name = form.name.data
        collection.description = form.description.data
        collection.visible = form.visible.data
        collection.start = form.start.data
        collection.end = form.end.data
        flask.flash(_("Collection modifiée avec succès !"), "success")
        db.session.commit()
    return flask.render_template(
        "photos/collection.html",
        form=form,
        collection=collection,
        albums=albums,
        title=collection.name,
    )


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

    # Restrict access
    context.check_permission(
        album.view_permission_type, PermissionScope.album, elem=album
    )
    ip = flask.request.headers.get("X-Real-Ip") or flask.current_app.config["FORCE_IP"]
    if not ip:
        flask.flash("IP non détectable, impossible d'accéder aux photos", "danger")
        flask.abort(403)
    # Access OK

    photo_form = forms.EditPhotoForm()
    album_form = forms.EditAlbumForm()
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
            flask.flash(
                _("Cet album est maintenant la miniature de la " "collection !"),
                "success",
            )
        db.session.commit()

    elif photo_form.validate_on_submit():
        photo = album.photos.filter_by(file_name=photo_form.photo_name.data).first()
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
            flask.flash(
                _("Cette photo est maintenant la miniature de " "l'album !"), "success"
            )
            db.session.commit()

    photos = album.photos.order_by(Photo.timestamp).all()
    token_args = album.get_access_token(ip)
    return flask.render_template(
        "photos/album.html",
        album=album,
        photos=photos,
        token_args=token_args,
        album_form=album_form,
        photo_form=photo_form,
        title=f"{album.name} – {collection.name}",
    )


@bp.route("<collection_dir>/<album_dir>/<photo_file>")
@bp.route("<collection_dir>/<album_dir>/_thumbs/<photo_file>")
@context.logged_in_only
def photo(collection_dir: str, album_dir: str, photo_file: str) -> typing.RouteReturn:
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

    # Restrict access
    context.check_permission(
        album.view_permission_type, PermissionScope.album, elem=album
    )
    ip = flask.request.headers.get("X-Real-Ip") or flask.current_app.config["FORCE_IP"]
    if not ip:
        flask.flash("IP non détectable, impossible d'accéder aux photos", "danger")
        flask.abort(403)
    # Access OK

    token_args = album.get_access_token(ip)
    photo_url = flask.request.base_url.replace("/photos/", "/photo/")
    return flask.redirect(f"{photo_url}?{token_args}")
