"""PC est magique - Image Metadata Utilities"""

from __future__ import annotations

from typing import Any

import datetime
import PIL.Image

import exif


width_attrs = ["image_width", "pixel_x_dimension"]
height_attrs = ["image_height", "pixel_y_dimension"]
author_attrs = ["Artist", "XPAuthor"]
caption_attrs = ["ImageDescription", "XPTitle", "XPComment"]
datetime_attrs = ["datetime", "datetime_original", "datetime_digitized"]
offset_attrs = ["offset_time", "offset_time_original", "offset_time_digitized"]


class ImageData(exif.Image):
    """EXIF data on an image."""

    @property
    def width(self) -> int | None:
        """Image width, or ``None`` if not available."""
        return self._get_from_attrs(*width_attrs)

    @property
    def height(self) -> int | None:
        """Image height, or ``None`` if not available."""
        return self._get_from_attrs(*height_attrs)

    @property
    def author(self) -> str | None:
        """Image author, or ``None`` if not available."""
        return self._get_from_attrs(*author_attrs)

    @property
    def caption(self) -> str | None:
        """Image caption / description, or ``None`` if not available."""
        return self._get_from_attrs(*author_attrs)

    @property
    def timestamp(self) -> datetime.datetime | None:
        """Image timestamp, or ``None`` if not available."""
        if str_timestamp := self._get_from_attrs(*datetime_attrs):
            if offset := self._get_from_attrs(*offset_attrs):
                offset_z = offset.replace(":", "")
                return datetime.datetime.strptime(f"{str_timestamp} {offset_z}", "%Y:%m:%d %H:%M:%S %z")
            return datetime.datetime.strptime(f"{str_timestamp}", "%Y:%m:%d %H:%M:%S")
        return None

    @property
    def lat(self) -> float | None:
        """Image latitude, or ``None`` if not available."""
        return self._get_gps_coord("gps_latitude", "gps_latitude_ref")

    @property
    def lng(self) -> float | None:
        """Image longitude, or ``None`` if not available."""
        return self._get_gps_coord("gps_longitude", "gps_longitude_ref")

    def _get_from_attrs(self, *attrs: str) -> Any:
        for attr in attrs:
            if value := self._safe_get(attr):
                return value
        return None

    def _get_gps_coord(self, value_attr: str, ref_attr: str) -> float | None:
        match self._safe_get(value_attr), self._safe_get(ref_attr):
            case (deg, minutes, seconds), "N" | "E" | None:
                return deg + minutes / 60 + seconds / 3600
            case (deg, minutes, seconds), "S" | "W":
                return -(deg + minutes / 60 + seconds / 3600)
            case _:
                return None

    def _safe_get(self, attr: str, default: Any = None) -> Any:
        try:
            return self.get(attr, default=default)
        except Exception:
            return None


def get_size_fallback(path: str) -> tuple(int, int) | tuple(None, None):
    """Get width and height of an image using Pillow.

    Much slower than EXIF method, so use only if metadata missing.

    Args:
        path: Full path to the files to get dimensions of.

    Returns:
        The tuple ``(width, height)`` (``(None, None)`` if any error occurs).
    """
    try:
        return PIL.Image.open(path).size
    except Exception:
        return (None, None)
