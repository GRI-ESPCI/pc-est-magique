"""PC est magique - Importe les albums de photos sur le disque et pas en base.

Explore le répertoire de photos (variable d'environnement PHOTOS_BASE_PATH),
crée les collections et albums manquants (en non visibles), ajoute les photos
contenues à la base de données, crée leurs versions miniatures et gzippées.
Supprime les collections, albums et photos supprimées de la base de données.

Ce script peut uniquement être appelé depuis Flask :
  * Soit depuis l'interface en ligne (menu GRI) ;
  * Soit par ligne de commande :
    cd /home/pc-est-magique/pc-est-magique
    ./env/bin/flask script sync_photos.py

02/2022 Loïc 137
"""

import os
import sys

import flask
import sqlalchemy.orm

try:
    from app import db
    from app.models import Collection, Album, Photo
except ImportError:
    sys.stderr.write(
        "ERREUR - Ce script peut uniquement être appelé depuis Flask :\n"
        "  * Soit depuis l'interface en ligne (menu GRI) ;\n"
        "  * Soit par ligne de commande :\n"
        "    cd /home/pc-est-magique/pc-est-magique; "
        "    ./env/bin/flask script sync_photos.py\n"
    )
    sys.exit(1)


def main() -> None:
    collections = {collection.dir_name: collection
                   for collection in Collection.query.all()}

    base = flask.current_app.config["PHOTOS_BASE_PATH"]
    for dirpath, dirnames, filenames in os.walk(base):
        relative_path = dirpath.removeprefix(base)
        match relative_path.split(os.sep):
            case [""]:
                sync_collections(collections, dirnames)

            case ["", collection_dir]:
                try:
                    collection = collections[collection_dir]
                except KeyError:
                    raise LookupError(f"Collection {collection_dir} not "
                                      "existing (but not detected before!?)")
                sync_albums(collection, dirnames)

            case ["", collection_dir, album_dir]:
                try:
                    collection = collections[collection_dir]
                    album = (collection.albums.filter_by(dir_name=album_dir)
                                              .one())
                except KeyError:
                    raise LookupError(f"Collection {collection_dir} not "
                                      "existing (but not detected before!?)")
                except sqlalchemy.orm.exc.NoResultFound:
                    raise LookupError(f"Album {collection_dir}/{album_dir} not "
                                      "existing (but not detected before!?)")
                sync_photos(album, filenames)

            case ["", _, _, *_]:
                print(f"WARNING - directory {relative_path} too nested, pass")

            case _:
                print(f"!! WARNING !! - unhandled path: {relative_path}")


def sync_collections(collections: dict[str, Collection],
                     dirnames: list[str]) -> None:
    """Synchronise collections on disk and on database.

    Args:
        collections: Directory of collections in database, indexed by dir_name.
            Modified in place after syncing.
        dirnames: List of collections dir_names on disk.
    """
    expected_collections = collections.copy()
    for collection_dir in dirnames:
        if collection_dir in collections:
            print(f"COLLECTION OK: {collection_dir}")
            expected_collections.pop(collection_dir)
        else:
            print(f"+ NEW COLLECTION: {collection_dir}")
            collection = Collection(
                visible=False, dir_name=collection_dir,
                name=f"[IMPORTED] {collection_dir}",
            )
            db.session.add(collection)
            collections[collection_dir] = collection

    # Remaining collections, deleted
    for collection_dir, collection in expected_collections.items():
        print(f"- DELETED COLLECTION: {collection_dir}")
        print(f"  - CASCADE: DELETED {len(collection.albums)} album(s)")
        print(f"    - CASCADE: DELETED {collection.nb_photos} photo(s)")
        collections.pop(collection_dir)
        db.session.delete(collection)


def sync_albums(collection: Collection, dirnames: list[str]) -> None:
    """Synchronise albums in a collection on disk and on database.

    Args:
        collection: The collection to sync.
        dirnames: List of albums dir_names on disk in this collection.
    """
    albums = {album.dir_name: album for album in collection.albums.all()}
    expected_albums = albums.copy()

    for album_dir in dirnames:
        if album_dir in albums:
            print(f"  ALBUM OK: {album_dir}")
            expected_albums.pop(album_dir)
        else:
            print(f"  + NEW ALBUM: {album_dir}")
            album = Album(
                visible=False, collection=collection,
                dir_name=album_dir, name=f"[IMPORTED] {album_dir}",
            )
            db.session.add(album)

    # Remaining albums, deleted
    for album_dir, album in expected_albums.items():
        print(f"  - DELETED album: {album_dir}")
        print(f"    - CASCADE: DELETED {album.nb_photos} photo(s)")
        db.session.delete(album)


def sync_photos(album: Album, filenames: list[str]) -> None:
    """Synchronise photos in an album on disk and on database.

    Args:
        album: The album to sync.
        filenames: List of file names on disk in this album.
    """
    photos = {photo.file_name: photo for photo in album.photos.all()}
    expected_photos = photos.copy()

    ok = 0
    for file_name in filenames:
        if file_name in photos:
            expected_photos.pop(file_name)
            ok += 1
        else:
            # Check extension
            _, ext = os.path.splitext()
            if ext.lower() not in ["jpg", "jpeg", "png"]:
                print(f"    WARNING: Bad file type: {file_name}")
                continue
            # New photo
            print(f"    + NEW PHOTO: {file_name}.")
            photo = Photo(
                album=album, file_name=file_name,
                # width="HELLO", height="OUI",
                # EXTRACT METADATA HERE
            )
            db.session.add(photo)
            # THUMB AND GZIP HERE (or register for later, or all later)

    # Remaining albums, deleted
    deleted = 0
    for photo in expected_photos.values():
        deleted += 1
        db.session.delete(photo)
        # REMOVE THUMB AND GZIP HERE?
    if deleted:
        print(f"    - DELETED {deleted} PHOTOS.")

    print(f"    {ok} PHOTOS OK.")
