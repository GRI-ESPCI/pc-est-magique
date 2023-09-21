"""PC est magique - Bekk Gallery Routes"""

import flask
from flask_babel import _

from app import context, db
from app.routes.bekk import bp, forms
from app.utils import typing
from app.models import Bekk

@bp.route("", methods=["GET", "POST"])
@bp.route("/", methods=["GET", "POST"])
#@context.permission_only(PermissionType.read, PermissionScope.bekk)
def main() -> typing.RouteReturn:
    """Bekk module main page"""

    bekks = Bekk.query.all()

    promos = []
    [promos.append(bekk.promo) for bekk in bekks if bekk.promo not in promos]

    return flask.render_template(
        "bekk/main.html",
        title = _("Page du Bekk ESPCI"),
        bekk=bekks[0],
        promos=promos
    )

@bp.route("/promo", methods=["GET", "POST"])
#@context.permission_only(PermissionType.read, PermissionScope.bekk)
def list_promo() -> typing.RouteReturn:
    """Bekk module main page"""

    bekks = Bekk.query.all()

    promos = []
    [promos.append(bekk.promo) for bekk in bekks if bekk.promo not in promos]

    return flask.render_template(
        "bekk/list_promo.html",
        title = _("Page du Bekk ESPCI"),
        bekk=bekks[0],
        promos=promos
    )


