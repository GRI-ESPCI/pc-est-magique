"""PC est magique - Synchronise les photos entre le disque et la BDD.

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
import subprocess
import sys

import flask
import sqlalchemy.orm

try:
    from app import db
    from app.models import Collection, Album, Photo
    from app.utils import loggers, metadata
except ImportError:
    sys.stderr.write(
        "ERREUR - Ce script peut uniquement être appelé depuis Flask :\n"
        "  * Soit depuis l'interface en ligne (menu GRI) ;\n"
        "  * Soit par ligne de commande :\n"
        "    cd /home/pc-est-magique/pc-est-magique; "
        "    ./env/bin/flask script sync_photos.py\n"
    )
    sys.exit(1)


@loggers.log_exception(reraise=True)
def main() -> None:
    print("Syncing photos...")
    collections = {collection.dir_name: collection for collection in Collection.query.all()}

    n_collections_before = len(collections)
    n_albums_before = sum(len(collec.albums.all()) for collec in collections.values())
    n_photos_before = sum(collec.nb_photos for collec in collections.values())
    print(
        f"Currently in database: {n_collections_before} collections, "
        f"{n_albums_before} albums, {n_photos_before} photos"
    )

    print("Scanning files on disk...\n")
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
                    raise LookupError(f"Collection {collection_dir} not " "existing (but not detected before!?)")
                sync_albums(collection, dirnames)

            case ["", collection_dir, album_dir]:
                try:
                    collection = collections[collection_dir]
                    album = collection.albums.filter_by(dir_name=album_dir).one()
                except KeyError:
                    raise LookupError(f"Collection {collection_dir} not " "existing (but not detected before!?)")
                except sqlalchemy.orm.exc.NoResultFound:
                    raise LookupError(f"Album {collection_dir}/{album_dir} not " "existing (but not detected before!?)")
                sync_photos(album, filenames)

            case ["", _, _, "_thumbs"]:
                pass

            case ["", _, _, *_]:
                print(f"WARNING - directory {relative_path} too nested, pass")

            case _:
                print(f"!! WARNING !! - unhandled path: {relative_path}")

    print("\nWriting changes...")
    db.session.commit()
    n_collections_after = len(collections)
    n_albums_after = sum(len(collec.albums.all()) for collec in collections.values())
    n_photos_after = sum(collec.nb_photos for collec in collections.values())
    print(
        f"Sync done! Now in database: {n_collections_after} collections "
        f"({n_collections_after - n_collections_before:+}), "
        f"{n_albums_after} albums ({n_albums_after - n_albums_before:+}), "
        f"{n_photos_after} photos ({n_photos_after - n_photos_before:+})."
    )


def sync_collections(collections: dict[str, Collection], dirnames: list[str]) -> None:
    """Synchronise collections on disk and on database.

    Args:
        collections: Directory of collections in database, indexed by dir_name.
            Modified in place after syncing.
        dirnames: List of collections dir_names on disk.
    """
    expected_collections = collections.copy()
    for collection_dir in dirnames:
        if collection_dir in collections:
            expected_collections.pop(collection_dir)
        else:
            print(f"+ NEW COLLECTION: {collection_dir}")
            collection = Collection(
                visible=False,
                dir_name=collection_dir,
                name=f"[IMPORTED] {collection_dir}",
            )
            db.session.add(collection)
            collections[collection_dir] = collection

    # Remaining collections, deleted
    for collection_dir, collection in expected_collections.items():
        print(f"- DELETED COLLECTION: {collection_dir}")
        print(f"  - CASCADE: DELETED {len(collection.albums.all())} albums")
        print(f"    - CASCADE: DELETED {collection.nb_photos} photos")
        collections.pop(collection_dir)
        db.session.delete(collection)


def sync_albums(collection: Collection, dirnames: list[str]) -> None:
    """Synchronise albums in a collection on disk and on database.

    Args:
        collection: The collection to sync.
        dirnames: List of albums dir_names on disk in this collection.
    """
    print(f"COLLECTION OK: {collection.dir_name}")
    albums = {album.dir_name: album for album in collection.albums.all()}
    expected_albums = albums.copy()

    for album_dir in dirnames:
        if album_dir in albums:
            expected_albums.pop(album_dir)
        else:
            print(f"  + NEW ALBUM: {album_dir}")
            album = Album(
                visible=False,
                collection=collection,
                dir_name=album_dir,
                name=f"[IMPORTED] {album_dir}",
            )
            db.session.add(album)
            # Create thumbnails directory
            try:
                os.mkdir(album.thumbs_full_path)
            except FileExistsError:
                pass

    # Remaining albums, deleted
    for album_dir, album in expected_albums.items():
        print(f"  - DELETED album: {album_dir}")
        print(f"    - CASCADE: DELETED {album.nb_photos} photos")
        db.session.delete(album)


def sync_photos(album: Album, filenames: list[str]) -> None:
    """Synchronise photos in an album on disk and on database.

    Args:
        album: The album to sync.
        filenames: List of file names on disk in this album.
    """
    print(f"  ALBUM OK: {album.dir_name}")
    photos = {photo.file_name: photo for photo in album.photos.all()}
    expected_photos = photos.copy()

    ok = 0
    for file_name in filenames:
        if file_name in photos:
            expected_photos.pop(file_name)
            ok += 1
        else:
            # Check extension
            _, ext = os.path.splitext(file_name)
            if ext.lower() not in [".jpg", ".jpeg", ".png"]:
                if not ext.lower().endswith(".gz"):
                    print(f"    WARNING: Bad file type: {file_name} " "(only .jpg, .jpeg or .png accepted)")
                continue
            # Check metadata
            full_path = os.path.join(album.full_path, file_name)
            with open(full_path, "rb") as fp:
                image = metadata.ImageData(fp)
            if image.width and image.height:
                width, height = image.width, image.height
            else:
                width, height = metadata.get_size_fallback(full_path)
                if not width or not height:
                    print(
                        f"    WARNING: {file_name}: unable to get width/"
                        "height data, check the file in an editor and "
                        "re-save it if okay (may be corrupted)"
                    )
                    continue
            # New photo
            photo = Photo(
                album=album,
                file_name=file_name,
                width=width,
                height=height,
                author_str=image.author,
                timestamp=image.timestamp,
                lat=image.lat,
                lng=image.lng,
                caption=image.caption,
            )
            # Create thumbnail and gzipped versions
            try:
                subprocess.run(
                    [
                        "convert",
                        photo.full_path,  # Take the picture,
                        "-resize",
                        "136x136^",  # Fill a 136x136 box,
                        "-gravity",
                        "center",  # Refer to image center,
                        "-extent",
                        "136x136",  # Then crop overflow,
                        photo.thumb_full_path,  # There is the thumbnail!
                    ],
                    capture_output=True,
                    check=True,
                )
            except subprocess.CalledProcessError as exc:
                print(
                    f"    WARNING: {file_name} Unable to create thumbnail:",
                    exc.cmd,
                    exc.stderr.decode(),
                )
                continue
            except Exception as exc:
                print(f"    WARNING: {file_name} Unable to create thumbnail:", exc)
                continue
            subprocess.run(["gzip", "-fk", photo.full_path])
            subprocess.run(["gzip", "-fk", photo.thumb_full_path])
            # All OK: add photo
            print(f"    + NEW PHOTO: {file_name}")
            ok += 1
            db.session.add(photo)

    # Remaining photos, deleted
    deleted = 0
    for photo in expected_photos.values():
        deleted += 1
        # Remove thumbnail and gzipped versions, if left behind
        try:
            os.remove(photo.thumb_full_path)
        except FileNotFoundError:
            pass
        try:
            os.remove(f"{photo.full_path}.gz")
        except FileNotFoundError:
            pass
        try:
            os.remove(f"{photo.thumb_full_path}.gz")
        except FileNotFoundError:
            pass
        db.session.delete(photo)
    if deleted:
        print(f"    - DELETED {deleted} PHOTOS.")

    album.nb_photos = ok
    print(f"    {ok} PHOTOS OK.")
