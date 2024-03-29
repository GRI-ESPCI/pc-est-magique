"""Useful miscellaneous functions."""

import datetime
import logging
import os
import importlib

import flask
from flask_babel import lazy_gettext as _l
import werkzeug
from werkzeug import urls as wku

from app import PCEstMagiqueApp
from app.utils import typing


def log_action(message: str, warning: bool = False) -> None:
    """Report an action to Discord using :attr:`.PCEstMagiqueApp.actions_logger`.

    Args:
        message: The action description to log.
        warning: If ``True``, logs with level ``WARNING``, else ``INFO``.
    """
    current_app = flask.current_app
    if not isinstance(current_app, PCEstMagiqueApp):
        raise RuntimeError("Current app is not an PCEstMagiqueApp!?!")
    current_app.actions_logger.log(logging.WARNING if warning else logging.INFO, message)


def safe_redirect(endpoint: str, **params: str | bool | None) -> typing.RouteReturn | None:
    """Redirect to a specific page, except if we are already here.

    Avoids infinite redirection loops caused by redirecting to the
    current request endpoint.

    It also automatically add the following URL parameters if not present:
      * ``next``, allowing to go back to the original request later if
        necessary (see :func:`utils.helpers.redirect_to_next`). To disable
        this behavior, pass ``next=None``;
      * ``doas``, allowing to preserve doas mode through redirection
        (see :attr:`flask.g.doas`).

    Args:
        endpoint (str): The endpoint to redirect to (e.g. ``"main.index"``)
        **params: URL parameters to pass to :func:`flask.url_for`

    Returns:
        The redirection response, or ``None`` if unsafe.
    """
    if endpoint == flask.request.endpoint:
        # Do not redirect to request endpoint (infinite loop!)
        return None

    if "next" not in params:
        params["next"] = flask.request.endpoint
    elif params["next"] is None:
        del params["next"]

    try:
        doas = flask.g.doas
    except AttributeError:
        pass
    else:
        if doas and "doas" not in params:
            params["doas"] = flask.g.pceen.id

    return flask.redirect(flask.url_for(endpoint, **params))


def ensure_safe_redirect(endpoint: str, **params: str | bool | None) -> typing.RouteReturn:
    """Like :func:`.safe_redirect`, but raises an exception if cannot redirect.

    Args:
        endpoint, *params: Passed to :func:`.safe_redirect`.

    Returns:
        The redirection response.

    Raises:
        RuntimeError: If the redirect is unsafe. Should never happend if
            calls to this function are well designed.
    """
    redirect = safe_redirect(endpoint, **params)
    if not redirect:
        raise RuntimeError(
            f"Could not safely redirect to {endpoint} with params {params} "
            f"(from {flask.request.url} / {flask.request.endpoint}"
        )
    return redirect


def redirect_to_next(**params: str | bool | None) -> typing.RouteReturn:
    """Redirect to the ``next`` request parameter, or to homepage.

    Includes securities to avoid redirecting to the same page (infinite
    loop) or to external pages (security breach).

    Args:
        **params: The query arguments, passed to :func:`flask.url_for`.

    Returns:
        The redirection response.
    """
    next_endpoint = flask.request.args.get("next", "")
    if next_endpoint == flask.request.endpoint:
        next_endpoint = "main.index"

    try:
        next_page = flask.url_for(next_endpoint, **params)
    except werkzeug.routing.BuildError:  # type: ignore
        next_page = None

    if not next_page or wku.url_parse(next_page).netloc != "":
        # Do not redirect to absolute links (possible attack)
        next_endpoint = "main.index"

    params["next"] = None
    return ensure_safe_redirect(next_endpoint, **params)


def run_script(name: str) -> None:
    """Run a PC est magique script.

    Args:
        name: the name of a file in scripts/, with or without the .py

    Raises:
        FileNotFoundError: if the given name is not an existing script.
    """
    name = name.removesuffix(".py")
    file = os.path.join("scripts", f"{name}.py")
    if not os.path.isfile(file):
        raise FileNotFoundError(f"Script '{name}' not found (should be '{os.path.abspath(file)}')")
    script = importlib.import_module(f"scripts.{name}")
    script.main()


def list_scripts() -> dict[str, str]:
    """Build the list of existing scripts in app/scripts.

    Returns:
        The scripts names (without the `.py`) mapped to the first line of their docstring.
    """
    scripts = {}
    for file in os.scandir("scripts"):
        if not file.is_file():
            continue
        name, ext = os.path.splitext(file.name)
        if ext != ".py":
            continue

        with open(file, "r") as fp:
            first_line = fp.readline()
        doc = first_line.lstrip("'\"").strip()

        scripts[name] = doc

    return scripts


def print_progressbar(
    iteration: int,
    total: int,
    prefix: str = "",
    suffix: str = "",
    decimals: int = 1,
    length: int = 100,
    fill: str = "█",
    print_end: str = "\r",
) -> None:
    """Call in a loop to create a terminal progress bar.

    Args:
        iteration: Current iteration.
        total: Total iterations.
        prefix: Prefix string.
        suffix: Suffix string.
        decimals: Positive number of decimals in percent complete.
        length: Character length of bar.
        fill: Bar fill character.
        print_end: End character (e.g. "\r", "\r\n").
    """
    percent = f"{{0:.{decimals}f}}".format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + "-" * (length - filled_length)
    print(f"\r{prefix} |{bar}| {percent}% {suffix}", end=print_end)
    # Print new line on complete
    if iteration == total:
        print()
