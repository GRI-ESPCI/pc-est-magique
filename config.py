"""PC est magique Flask App - Configuration"""

import os

from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


def get_or_die(name: str) -> str:
    """Check availability and get the value of an environment variable.

    Args:
        name (str): The environment variable to get.

    Returns:
        The environment variable value, if it is set.

    Raises:
        RuntimeError: if the environment variable is not set.
    """
    var = os.environ.get(name)
    if var is None:
        raise RuntimeError(f"Missing environment variable '{name}'")
    return var


class Config:
    """PC est magique Flask Web App Configuration."""

    SECRET_KEY = get_or_die("SECRET_KEY")

    LANGUAGES = ["fr", "en"]

    PREFERRED_URL_SCHEME = os.environ.get("PREFERRED_URL_SCHEME")
    SERVER_NAME = os.environ.get("SERVER_NAME")
    APPLICATION_ROOT = os.environ.get("APPLICATION_ROOT")

    SQLALCHEMY_DATABASE_URI = get_or_die("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 25)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS") is not None
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_SUPPRESS_SEND = os.environ.get("MAIL_SUPPRESS_SEND")
    ADMINS = os.environ.get("ADMINS", "").split(";")
    CLUB_Q = os.environ.get("CLUB_Q")

    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 25000000))

    ERROR_WEBHOOK = os.environ.get("ERROR_WEBHOOK")
    LOGGING_WEBHOOK = os.environ.get("LOGGING_WEBHOOK")
    MESSAGE_WEBHOOK = os.environ.get("MESSAGE_WEBHOOK")
    MAIL_WEBHOOK = os.environ.get("MAIL_WEBHOOK")
    GRI_ROLE_ID = os.environ.get("GRI_ROLE_ID")

    BEKKS_BASE_PATH = os.environ.get("BEKKS_BASE_PATH")

    PHOTOS_BASE_PATH = os.environ.get("PHOTOS_BASE_PATH")
    PHOTOS_SECRET_KEY = os.environ.get("PHOTOS_SECRET_KEY")
    _delay_str = os.environ.get("PHOTOS_EXPIRES_DELAY")
    PHOTOS_EXPIRES_DELAY = int(_delay_str) if _delay_str.isdigit() else 3600

    LYDIA_BASE_URL = os.environ.get("LYDIA_BASE_URL")
    LYDIA_VENDOR_TOKEN = os.environ.get("LYDIA_VENDOR_TOKEN")
    LYDIA_PRIVATE_TOKEN = os.environ.get("LYDIA_PRIVATE_TOKEN")

    GOOGLE_RECAPTCHA_SITEKEY = os.environ.get("GOOGLE_RECAPTCHA_SITEKEY")
    GOOGLE_RECAPTCHA_SECRET = os.environ.get("GOOGLE_RECAPTCHA_SECRET")

    BAR_USERS_PER_PAGE = int(os.environ.get("BAR_USERS_PER_PAGE"))
    BAR_ITEMS_PER_PAGE = int(os.environ.get("BAR_ITEMS_PER_PAGE"))

    SAML_IDP_METADATA_URL = get_or_die("SAML_IDP_METADATA_URL")
    SAML_IDP_METADATA_FALLBACK_URL = os.environ.get("SAML_IDP_METADATA_FALLBACK_URL")
    SAML_CERTIFICATE_PRIVATE_KEY_FILE = os.environ.get("SAML_CERTIFICATE_PRIVATE_KEY_FILE")
    SAML_CERTIFICATE_PUBLIC_KEY_FILE = os.environ.get("SAML_CERTIFICATE_PUBLIC_KEY_FILE")

    GRI_BASIC_PASSWORD = os.environ.get("GRI_BASIC_PASSWORD")

    BRANCH = os.environ.get("BRANCH")
    FORCE_IP = os.environ.get("FORCE_IP")
    FORCE_MAC = os.environ.get("FORCE_MAC")

    NETLOCS = os.environ.get("NETLOCS")
    if NETLOCS is not None:
        NETLOCS = NETLOCS.split(";")

    MAINTENANCE = bool(os.environ.get("MAINTENANCE"))
