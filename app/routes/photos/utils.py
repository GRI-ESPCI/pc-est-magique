import os
import re
import subprocess

import plum.exceptions
import unidecode

from app.models import Album, Photo
from app.utils import metadata


class PhotoRegistrationError(RuntimeError):
    pass


def _is_animated(full_path: str) -> bool:
    try:
        result = subprocess.run(["identify", "-format", "%n", full_path], capture_output=True, timeout=10)
        return int(result.stdout) > 1
    except Exception:
        return True


def register_new_photo(album: Album, file_name: str) -> Photo | None:
    full_path = os.path.join(album.full_path, file_name)

    # Check extension
    file, ext = os.path.splitext(file_name)
    if ext.lower() in [".heic", ".raw", ".nef"] or ext.lower() == ".gif" and not _is_animated(full_path):
        # Non-standard image format: convert file
        file_name = f"{file}.jpeg"
        try:
            subprocess.run(["convert", full_path, os.path.join(album.full_path, file_name)], timeout=10, check=True)
        except Exception:
            raise PhotoRegistrationError(
                f"Invalid file extension and cannot convert: '{ext.lower()}' (only .jpg, .jpeg or .png accepted)"
            )
        else:
            os.remove(full_path)
            ext = ".jpeg"
            full_path = os.path.join(album.full_path, file_name)

    if ext.lower() not in [".jpg", ".jpeg", ".png"]:
        raise PhotoRegistrationError(f"Invalid file extension: '{ext.lower()}' (only .jpg, .jpeg or .png accepted)")

    # Check metadata
    with open(full_path, "rb") as fp:
        try:
            image = metadata.ImageData(fp)
        except plum.exceptions.UnpackError:
            raise PhotoRegistrationError(
                f"Unable to parse image metadata; please check its encoding / re-save it in a regular JPEG/PNG format"
            )

    if image.width and image.height:
        width, height = image.width, image.height
    else:
        width, height = metadata.get_size_fallback(full_path)
        if not width or not height:
            raise PhotoRegistrationError(
                f"Unable to get width/height data, check the file and re-save it if okay (may be corrupted)"
            )

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
    mtime = os.path.getmtime(photo.full_path)
    if not os.path.exists(photo.thumb_full_path) or os.path.getmtime(photo.thumb_full_path) < mtime:
        print("Creating thumbnail...")
        _create_thumbnail(photo)
    if not os.path.exists(f"{photo.full_path}.gz") or os.path.getmtime(f"{photo.full_path}.gz") < mtime:
        print("Compressing photo...")
        subprocess.run(["gzip", "-fk", photo.full_path])
    if not os.path.exists(f"{photo.thumb_full_path}.gz") or os.path.getmtime(f"{photo.thumb_full_path}.gz") < mtime:
        print("Compressing thumbnail...")
        subprocess.run(["gzip", "-fk", photo.thumb_full_path])

    return photo


def _create_thumbnail(photo: Photo) -> None:
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
        raise PhotoRegistrationError("Unable to create thumbnail:", exc.cmd, exc.stderr.decode())
    except Exception as exc:
        raise PhotoRegistrationError("Unable to create thumbnail:", exc)


def _rm_if_exists(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def remove_photo_on_disk(photo: Photo) -> None:
    _rm_if_exists(photo.full_path)
    _rm_if_exists(photo.full_path + ".gz")
    _rm_if_exists(photo.thumb_full_path)
    _rm_if_exists(photo.thumb_full_path + ".gz")


def get_dir_name(name: str) -> str:
    name = unidecode.unidecode(name).lower()
    name = re.sub(r"\W", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")
