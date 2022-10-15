"""PC est magique - API Errors"""

import logging
import traceback

import flask
from werkzeug.exceptions import HTTPException

from app import context, db
from app.routes.api import bp
from app.utils import typing


def _create_http_error_payload(error: HTTPException, log_level: int = logging.WARNING) -> dict[str, str]:
    err_name = f"{error.code} {error.name}"
    flask.current_app.logger.log(log_level, f"{err_name} -- {flask.request}")
    payload = {"status": error.code, "name": error.name, "message": error.description}
    if error.args:
        payload |= {"detail": error.args[0]}
    return payload


@bp.errorhandler(418)
def theiere_error(error: HTTPException) -> typing.RouteReturn:
    return {"error": {"status": 418, "name": error.name, "message": "Would you like a cup of tea?"}}, 418


@bp.errorhandler(503)
def service_unavailable_error(error: HTTPException) -> typing.RouteReturn:
    payload = _create_http_error_payload(
        error, 503, log_level=logging.INFO if flask.current_app.config["MAINTENANCE"] else logging.ERROR
    )
    return {"error": payload}, 503


@bp.errorhandler(Exception)
def other_error(error: Exception) -> typing.RouteReturn:
    if isinstance(error, HTTPException):
        return {"error": _create_http_error_payload(error, log_level=logging.ERROR)}, error.code

    flask.current_app.logger.error(traceback.format_exc())
    db.session.rollback()
    payload = {
        "status": 500,
        "name": "Python Exception",
        "message": "A Python exception stopped the execution of the request.",
    }

    try:
        is_gri = context.g.is_gri
    except AttributeError:
        # Very early error
        is_gri = False
    if is_gri:
        # GRI: show traceback
        payload |= {"traceback": traceback.format_exc()}

    return {"error": payload}, 500
