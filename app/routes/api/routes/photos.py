"""PC est magique - Photos API Routes"""

import datetime
import os
import re

import flask
from flask_babel import _

from app import context, db
from app.models import Album, Collection, PermissionScope, PermissionType, Photo
from app.routes.photos import forms
from app.routes.photos.utils import register_new_photo, PhotoRegistrationError, remove_photo_on_disk

sbp = flask.Blueprint("photos", __name__)

ALBUM_URL = re.compile(r"/photos/(.+?)/(.+?)/?")


def _check_rights_and_get_album() -> Album:
    collection_name = flask.request.form.get("collection")
    if not collection_name:
        flask.abort(400, "Form field 'collection' missing")
    album_name = flask.request.form.get("album")
    if not album_name:
        flask.abort(400, "Form field 'album' missing")

    collection = Collection.query.filter_by(dir_name=collection_name).first()
    if not collection:
        flask.abort(400, f"Invalid collection: '{collection_name}'")
    album = collection.albums.filter_by(dir_name=album_name).first()
    if not album:
        flask.abort(400, f"Invalid collection: '{collection_name}'")
    if not context.has_permission(PermissionType.write, PermissionScope.album, elem=album):
        flask.abort(403, "Unauthorized")

    return album


@sbp.route("/upload", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.photos)
def upload():
    """Upload a photo to an album (write it to disk and in database)."""
    album = _check_rights_and_get_album()

    file = flask.request.files["file"]
    if not file:
        flask.abort(400, "Missing file (expected as 'file' multipart field)")

    if album.photos.filter_by(file_name=file.filename).count():
        flask.abort(409, "A photo with the same filename already exists in this album.")

    # Save photo
    full_path = os.path.join(album.full_path, file.filename)
    with open(full_path, "wb") as fp:
        fp.write(file.read())

    # Register photo
    try:
        photo = register_new_photo(album, file.filename)
    except PhotoRegistrationError as exc:
        os.remove(full_path)
        flask.abort(400, " - ".join(exc.args))

    db.session.add(photo)
    album.nb_photos += 1
    db.session.commit()

    return "OK", 201


@sbp.route("/edit_photo", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.photos)
def edit_photo():
    """Edit a photo details."""
    album = _check_rights_and_get_album()

    photo_form = forms.EditPhotoForm()
    if not photo_form.validate_on_submit():
        flask.abort(400, "Invalid form body")

    photo: Photo = album.photos.filter_by(file_name=photo_form.photo_name.data).first()
    if not photo:
        flask.abort(400, "This photo does not exist")

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

    db.session.commit()
    return _("Photo modifiée avec succès (recharger la page pour voir)"), 200


@sbp.route("/star_photo", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.photos)
def star_photo():
    """Make a photo the album thumbnail."""
    album = _check_rights_and_get_album()

    photo_name = flask.request.form.get("photo")
    if not photo_name:
        flask.abort(400, "Form field 'photo' missing")

    photo: Photo = album.photos.filter_by(file_name=photo_name).first()
    if not photo:
        flask.abort(400, "This photo does not exist")
    if photo.featured:
        flask.abort(409, "This photo is already the thumbnail of the album")

    photo.album.featured_photo.featured = False
    photo.featured = True
    db.session.commit()
    return _("Cette photo est maintenant la miniature de l'album."), 200


@sbp.route("/delete_photo", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.photos)
def delete_photo():
    """Make a photo the album thumbnail."""
    album = _check_rights_and_get_album()

    photo_name = flask.request.form.get("photo")
    if not photo_name:
        flask.abort(400, "Form field 'photo' missing")

    photo: Photo = album.photos.filter_by(file_name=photo_name).first()
    if not photo:
        flask.abort(400, "This photo does not exist")

    remove_photo_on_disk(photo)
    db.session.delete(photo)
    album.nb_photos -= 1
    db.session.commit()
    return _("Photo définitivement supprimée."), 200
