"""PC est magique - Bekk Thumbnail Utilities"""

from __future__ import annotations

import logging
import os

import flask
import pymupdf 


THUMB_SUFFIX = "_thumb.jpg"
THUMB_HEIGHT_PX = 1200 


def _thumb_path(bekk_id: int) -> str:
    """Return the filesystem path for a bekk's thumbnail JPEG."""
    return os.path.join(
        flask.current_app.config["BEKKS_BASE_PATH"],
        f"{bekk_id}{THUMB_SUFFIX}",
    )


def thumbnail_exists(bekk_id: int) -> bool:
    """Return True if the thumbnail for bekk_id exists on disk."""
    return os.path.exists(_thumb_path(bekk_id))


def generate_bekk_thumbnail(bekk_id: int) -> bool:
    """Render page 1 of bekk bekk_id's PDF and save it as a JPEG thumbnail.

    The thumbnail is stored at ``<BEKKS_BASE_PATH>/<bekk_id>_thumb.jpg``.

    Returns:
        True on success, False if the PDF is missing or an error occurs.
    """
    pdf_path = os.path.join(
        flask.current_app.config["BEKKS_BASE_PATH"],
        f"{bekk_id}.pdf",
    )
    if not os.path.exists(pdf_path):
        logging.warning("generate_bekk_thumbnail: PDF not found for id=%s", bekk_id)
        return False
    try:
        doc = pymupdf.open(pdf_path)
        page = doc[0]
        orig_height = page.rect.height
        scale = THUMB_HEIGHT_PX / orig_height
        mat = pymupdf.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        pix.save(_thumb_path(bekk_id), output="jpeg")
        doc.close()
        return True
    except Exception:
        logging.exception("generate_bekk_thumbnail: failed for id=%s", bekk_id)
        return False


def get_or_generate_thumbnail(bekk_id: int) -> bool:
    """Return True if the thumbnail exists, generating it on the fly if needed.

    Used when rendering templates so that legacy bekks get thumbnails automatically without requiring a migration.
    """
    if thumbnail_exists(bekk_id):
        return True
    return generate_bekk_thumbnail(bekk_id)
