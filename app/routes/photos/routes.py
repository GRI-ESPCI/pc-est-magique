"""PC est magique - Photos Gallery Routes"""

import os
import flask
from flask_babel import _

from app import context, db
from app.routes.photos import bp, forms
from app.models import Album, Collection, PermissionScope, PermissionType, Photo
from app.routes.photos.utils import get_dir_name
from app.utils import typing, helpers


@bp.route("")
def main() -> typing.RouteReturn:
    """Photos main page (list of collections)."""
    # Filter collections to display based on permissions
    collections = [
        collection
        for collection in Collection.query.order_by(Collection.start.desc()).all()
        if context.has_permission(collection.view_permission_type, PermissionScope.collection, elem=collection)
    ]
    return flask.render_template("photos/main.html", collections=collections, title=_("Photos"))


@bp.route("<collection_dir>", methods=["GET", "POST"])
def collection(collection_dir: str) -> typing.RouteReturn:
    """Photos collection page (list of albums)."""
    collection = Collection.query.filter_by(dir_name=collection_dir).first()
    if not collection:
        flask.abort(404)

    # Restrict access and filter albums to display based on permissions
    if write_permission := context.has_permission(PermissionType.write, PermissionScope.collection, elem=collection):
        # Write permission: show all albums
        albums = collection.albums.all()
    elif context.has_permission(PermissionType.read, PermissionScope.collection, elem=collection):
        # Read permission: show visible albums + hidden albums for which
        # we have a specific write permission
        albums = collection.albums.filter_by(visible=True).all() + [
            album
            for album in collection.albums.filter_by(visible=False).all()
            if context.has_permission(PermissionType.write, PermissionScope.album, elem=album)
        ]
    else:
        # No permission on collection: check if albums-specific permissions
        albums = [
            album
            for album in collection.albums.all()
            if context.has_permission(album.view_permission_type, PermissionScope.album, elem=album)
        ]
    if not albums and not write_permission:
        # Nothing to show here
        flask.abort(403)
    # Access OK

    can_edit = context.has_permission(PermissionType.write, PermissionScope.collection, elem=collection)

    edit_form = forms.EditCollectionForm()
    create_form = forms.CreateAlbumForm(collection)

    if edit_form.validate_on_submit():
        if not can_edit:
            flask.abort(403)
        collection.name = edit_form.name.data
        collection.description = edit_form.description.data
        collection.visible = edit_form.visible.data
        collection.start = edit_form.start.data
        collection.end = edit_form.end.data
        if collection.visible and not collection.albums.filter_by(visible=True).count():
            collection.visible = False
            flask.flash(
                _("Une collection ne peut pas être rendue visible si elle ne contient aucun album visible !"), "warning"
            )
        else:
            flask.flash(_("Collection modifiée avec succès !"), "success")
        db.session.commit()

    elif create_form.validate_on_submit():
        if not can_edit:
            flask.abort(403)

        name = create_form.album_name.data
        dir_name = get_dir_name(name)

        album = Album(collection=collection, dir_name=dir_name, name=f"[CREATED] {name}", visible=False)
        os.mkdir(album.full_path)
        os.mkdir(album.thumbs_full_path)

        db.session.add(album)
        db.session.commit()
        flask.flash(_("Album créé !"), "success")
        return helpers.ensure_safe_redirect(
            "photos.album", collection_dir=collection_dir, album_dir=dir_name, edit=True, next=None
        )

    return flask.render_template(
        "photos/collection.html",
        edit_form=edit_form,
        create_form=create_form,
        collection=collection,
        albums=albums,
        can_edit=can_edit,
        is_edit_mode=can_edit and "edit" in flask.request.args,
        title=collection.name,
    )


@bp.route("<collection_dir>/<album_dir>", methods=["GET", "POST"])
def album(collection_dir: str, album_dir: str) -> typing.RouteReturn:
    """Photos album page (list of photos)."""
    collection = Collection.query.filter_by(dir_name=collection_dir).first()
    if not collection:
        flask.abort(404)
    album = collection.albums.filter_by(dir_name=album_dir).first()
    if not album:
        flask.abort(404)

    # Restrict access
    context.check_permission(album.view_permission_type, PermissionScope.album, elem=album)
    ip = flask.request.headers.get("X-Real-Ip") or flask.current_app.config["FORCE_IP"]
    if not ip:
        flask.flash(_("IP non détectable, impossible d'accéder aux photos"), "danger")
        flask.abort(403)
    # Access OK

    can_edit = context.has_permission(PermissionType.write, PermissionScope.album, elem=album)

    album_form = forms.EditAlbumForm()
    if album_form.validate_on_submit():
        if not can_edit:
            flask.abort(403)
        album.name = album_form.name.data
        album.description = album_form.description.data
        album.visible = album_form.visible.data
        album.start = album_form.start.data
        album.end = album_form.end.data
        if album.visible and not album.photos.count():
            album.visible = False
            flask.flash(_("Un album ne peut pas être rendu visible si il ne contient aucune photo !"), "warning")
        else:
            flask.flash(_("Album modifié avec succès !"), "success")
        db.session.commit()

    photo_form = forms.EditPhotoForm()

    photos = album.photos.order_by(Photo.timestamp.asc(), Photo.file_name.asc()).all()
    token_args = album.get_access_token(ip)
    return flask.render_template(
        "photos/album.html",
        album=album,
        photos=photos,
        token_args=token_args,
        album_form=album_form,
        photo_form=photo_form,
        can_edit=can_edit,
        is_edit_mode=can_edit and "edit" in flask.request.args,
        title=f"{album.name} – {collection.name}",
    )


@bp.route("<collection_dir>/<album_dir>/<photo_file>")
@bp.route("<collection_dir>/<album_dir>/_thumbs/<photo_file>")
@context.permission_only(PermissionType.read, PermissionScope.photos)
def photo(collection_dir: str, album_dir: str, photo_file: str) -> typing.RouteReturn:
    """Photo page: redirect to /photo with token, if access authorized.

    Let's take a little time to explain that:
      * /photos/<collection>/<album>/<photo> (this route), served by Flask,
            checks authorization to see the photo (user must be logged in)
            then (if OK) creates the security token and redirects to:
      * /photo/<collection>/<album>/<photo> (same but without the s at photos!),
            served by Nginx, that checks the security token and:
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
    context.check_permission(album.view_permission_type, PermissionScope.album, elem=album)
    ip = flask.request.headers.get("X-Real-Ip") or flask.current_app.config["FORCE_IP"]
    if not ip:
        flask.flash("IP non détectable, impossible d'accéder aux photos", "danger")
        flask.abort(403)
    # Access OK

    token_args = album.get_access_token(ip)
    photo_url = flask.request.base_url.replace("/photos/", "/photo/")
    return flask.redirect(f"{photo_url}?{token_args}")
