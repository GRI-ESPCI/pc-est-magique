"""PC est magique Nginx utilities."""

import base64
import datetime
import hashlib

import flask


def get_nginx_access_token(resource: str, ip: str, expires: datetime.datetime | None = None) -> str:
    """Get Nginx MD5 secret token used to access protected directories.

    Args:
        resource: The resource identifier (directory or special pattern).
        ip: IP of the user allowed to download the content.
        expires: The timestamp when the access right expires. Defaults to now plus
            ``PHOTOS_EXPIRES_DELAY`` environment variable.

    Returns:
        The URL query arguments to use to load the protected file.
    """
    if expires is None:
        expires = datetime.datetime.now() + datetime.timedelta(seconds=flask.current_app.config["PHOTOS_EXPIRES_DELAY"])
    expires_ts = int(expires.timestamp())
    secret = flask.current_app.config["PHOTOS_SECRET_KEY"]
    md5 = hashlib.md5(f"{expires_ts}{resource}{ip} {secret}".encode())
    b64 = base64.urlsafe_b64encode(md5.digest()).replace(b"=", b"")
    return f"md5={b64.decode()}&expires={expires_ts}"
