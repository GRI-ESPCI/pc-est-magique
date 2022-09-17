"""PC est magique Flask App - Photos Models"""

from __future__ import annotations

import base64
import datetime
import hashlib
import os
import typing

import flask
import flask_babel
import sqlalchemy as sa

from app import db
from app.enums import PermissionType, PermissionScope
from app.utils.columns import (
    column,
    one_to_many,
    many_to_one,
    Column,
    Relationship,
)


Model = typing.cast(type[type], db.Model)  # type checking hack


class Photo(Model):
    """A photo."""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    _album_id: Column[int] = column(sa.ForeignKey("album.id"), nullable=False)
    album: Relationship[Album] = many_to_one("Album.photos")
    file_name: Column[str] = column(sa.String(120), nullable=False)
    width: Column[int] = column(sa.Integer(), nullable=False)
    height: Column[int] = column(sa.Integer(), nullable=False)
    _author_id: Column[int | None] = column(sa.ForeignKey("pceen.id"), nullable=True)
    author: Relationship[models.PCeen | None] = many_to_one("PCeen.photos")
    author_str: Column[str | None] = column(sa.String(64), nullable=True)
    timestamp: Column[datetime.datetime | None] = column(sa.DateTime(), nullable=True)
    lat: Column[float | None] = column(sa.Float(), nullable=True)
    lng: Column[float | None] = column(sa.Float(), nullable=True)
    caption: Column[str | None] = column(sa.String(280), nullable=True)
    featured: Column[bool] = column(sa.Boolean(), nullable=False, default=False)

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<Photo #{self.id} ('{self.album}' /{self.file_name})>"

    @property
    def info(self) -> str:
        """Description of the photo, from different args."""
        parts = []
        if self.caption:
            parts.append(self.caption)
        if self.author:
            parts.append(self.author.full_name)
        elif self.author_str:
            parts.append(self.author_str)
        if self.timestamp:
            parts.append(flask_babel.format_datetime(self.timestamp, "long"))
        if self.lat and self.lng:
            parts.append(f"@{self.lat}/{self.lng}")
        return ", ".join(parts)

    @property
    def full_path(self) -> str:
        """The full path of the photo on disk."""
        return os.path.join(self.album.full_path, self.file_name)

    @property
    def thumb_full_path(self) -> str:
        """The full path of the photo's thumbnail (small version) on disk."""
        return os.path.join(self.album.thumbs_full_path, self.file_name)

    @property
    def src(self) -> str:
        """The online path to the photo."""
        return f"{self.album.src}/{self.file_name}"

    @property
    def src_with_token(self) -> str:
        """The online query to the photo's with md5 args."""
        ip = flask.request.headers.get("X-Real-Ip") or flask.current_app.config["FORCE_IP"]
        token_args = self.album.get_access_token(ip)
        return f"{self.src}?{token_args}"

    @property
    def thumb_src(self) -> str:
        """The online path to the photo's thumbnail (small version)."""
        return f"{self.album.src}/_thumbs/{self.file_name}"

    @property
    def thumb_src_with_token(self) -> str:
        """The online query to the photo's thumbnail with md5 args."""
        ip = flask.request.headers.get("X-Real-Ip") or flask.current_app.config["FORCE_IP"]
        token_args = self.album.get_access_token(ip)
        return f"{self.thumb_src}?{token_args}"


class Album(Model):
    """A album of photos."""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    visible: Column[bool] = column(sa.Boolean(), nullable=False, default=False)
    _collection_id: Column[int] = column(sa.ForeignKey("collection.id"), nullable=False)
    collection: Relationship[Collection] = many_to_one("Collection.albums")
    dir_name: Column[str] = column(sa.String(120), nullable=False)
    name: Column[str] = column(sa.String(120), nullable=False)
    description: Column[str] = column(sa.String(280), nullable=True)
    start: Column[datetime.date] = column(sa.Date(), nullable=True)
    end: Column[datetime.date] = column(sa.Date(), nullable=True)
    featured: Column[bool] = column(sa.Boolean(), nullable=False, default=False)
    nb_photos: Column[int] = column(sa.Integer, nullable=False, default=0)

    photos: Relationship[list[Photo]] = one_to_many(
        "Photo.album",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<Album #{self.id} ('{self.dir_name}')>"

    def __str__(self) -> str:
        """Human-readible description of the album."""
        return f"{self.collection.name} / {self.name}"

    @property
    def view_permission_type(self) -> PermissionScope:
        """The permission type needed to view this album."""
        return PermissionType.read if self.visible else PermissionType.write

    @property
    def full_path(self) -> str:
        """The full path of the album on disk."""
        return os.path.join(self.collection.full_path, self.dir_name)

    @property
    def thumbs_full_path(self) -> str:
        """The full path of the album thumbnails (small versions) on disk."""
        return os.path.join(self.full_path, "_thumbs")

    @property
    def src(self) -> str:
        """The online path to the album."""
        return f"{self.collection.src}/{self.dir_name}"

    @property
    def featured_photo(self) -> Photo | None:
        """The (first) photo of this album marked as featured, if any."""
        return self.photos.filter_by(featured=True).first() or self.photos.first()

    def get_access_token(self, ip: str, expires: datetime.datetime = None) -> str:
        """Forges the md5 token allowing access to the photos of this album.

        Args:
            ip: Remote IPv4 address allowed to access these photos.
            expires: Timestamp of when the access expires. If ``None``,
                defaults to PHOTOS_EXPIRES_DELAY seconds after now
                (defaults to 3600 if the environment variable is empty).

        Returns:
            A tuple of the md5-hashed base64-encoded token and the expire
            timestamp to pass to the server.
        """
        if expires is None:
            expires = datetime.datetime.now() + datetime.timedelta(
                seconds=flask.current_app.config["PHOTOS_EXPIRES_DELAY"]
            )
        expires_ts = int(expires.timestamp())
        secret = flask.current_app.config["PHOTOS_SECRET_KEY"]
        md5 = hashlib.md5(f"{expires_ts}{self.src}{ip} {secret}".encode())
        b64 = base64.urlsafe_b64encode(md5.digest()).replace(b"=", b"")
        return f"md5={b64.decode()}&expires={expires_ts}"


class Collection(Model):
    """A collection of albums."""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    visible: Column[bool] = column(sa.Boolean(), nullable=False, default=False)
    dir_name: Column[str] = column(sa.String(120), unique=True, nullable=False)
    name: Column[str] = column(sa.String(120), nullable=False)
    description: Column[str] = column(sa.String(280), nullable=True)
    start: Column[datetime.date] = column(sa.Date(), nullable=True)
    end: Column[datetime.date] = column(sa.Date(), nullable=True)

    albums: Relationship[list[Album]] = one_to_many(
        "Album.collection",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<Collection #{self.id} ('{self.dir_name}')>"

    def __str__(self) -> str:
        """Human-readible description of the collection."""
        return self.name

    @property
    def view_permission_type(self) -> PermissionScope:
        """The permission type needed to view this collection."""
        return PermissionType.read if self.visible else PermissionType.write

    @property
    def full_path(self) -> str:
        """The full path of the collection on disk."""
        return os.path.join(flask.current_app.config["PHOTOS_BASE_PATH"], self.dir_name)

    @property
    def src(self) -> str:
        """The online path to the collection."""
        return f"/photo/{self.dir_name}"

    @property
    def featured_album(self) -> Photo | None:
        """The (first) album of this collection marked as featured, if any."""
        return self.albums.filter_by(featured=True).first() or self.albums.first()

    @property
    def featured_photo(self) -> Photo | None:
        """The featured photo of the collection's featured album, if any."""
        if album := self.featured_album:
            return album.featured_photo
        else:
            return None

    @property
    def nb_albums(self) -> int:
        """The number of visible albums in the collection."""
        return len(self.albums.filter_by(visible=True).all())

    @property
    def nb_photos(self) -> int:
        """The total number of photos in the collection."""
        return sum(album.nb_photos for album in self.albums.filter_by(visible=True).all())


from app import models
