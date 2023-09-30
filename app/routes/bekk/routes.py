"""PC est magique - Bekk Gallery Routes"""

import flask
from flask_babel import _

from app import context, db
from app.routes.bekk import bp, forms
from app.utils import typing
from app.models import (
    Bekk,
    PermissionScope,
    PermissionType,
    GlobalSetting,
)

import PyPDF2
import os


@bp.route("", methods=["GET", "POST"])
@bp.route("/", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.bekk)
def main() -> typing.RouteReturn:
    """Bekk module main page"""

    bekks = Bekk.query.order_by(Bekk.date.desc()).all()
    promos = sorted({bekk.promo for bekk in bekks}, reverse=True)

    promo = flask.request.args.get("promo")
    if promo is None:
        promo = GlobalSetting.query.filter_by(key="PROMO_1A").one().value
        while promo not in promos:
            promo = promo - 1
            if promo == 0:
                break
    promo = int(promo)
    if promo != 0:
        bekks = Bekk.query.filter_by(promo=promo).order_by(Bekk.date.desc()).all()

    form = forms.Bekk()

    if form.validate_on_submit() and context.g.pceen.has_permission(PermissionType.write, PermissionScope.bekk):
        add = form["add"].data

        if add:
            flag = False
            if form["pdf_file"].data is None:
                flask.flash(_("Aucun fichier choisi."), "danger")
                flag = True

            if not flag:
                bekk = Bekk()

                db.session.add(bekk)

                bekk.name = form["bekk_name"].data
                bekk.promo = form["promo"].data
                bekk.date = form["date"].data

                db.session.commit()

                bekk_path = os.path.join(flask.current_app.config["BEKKS_BASE_PATH"], str(bekk.id) + ".pdf")
                form["pdf_file"].data.save(bekk_path)

                flask.flash(_("Bekk ajouté."))
                return flask.redirect(flask.url_for("bekk.main", promo=promo))

        if not add:
            delete = form["delete"].data
            bekk = Bekk.query.filter_by(id=form["id"].data).one()

            bekk_path = os.path.join(flask.current_app.config["BEKKS_BASE_PATH"], str(bekk.id) + ".pdf")

            if delete:
                db.session.delete(bekk)
                db.session.commit()

                os.remove(bekk_path)

                flask.flash(_("Bekk supprimé."))
                return flask.redirect(flask.url_for("bekk.main", promo=promo))

            else:
                bekk.name = form["bekk_name"].data
                bekk.promo = form["promo"].data
                bekk.date = form["date"].data

                db.session.commit()
                flask.flash(_("Bekk édité."))
                return flask.redirect(flask.url_for("bekk.main", promo=promo))

    bekk_id_list = []
    for bekk in bekks:
        bekk_id_list.append(bekk.id)

    can_edit = context.has_permission(PermissionType.write, PermissionScope.bekk)

    return flask.render_template(
        "bekk/main.html",
        title=_("Page du Bekk ESPCI"),
        bekks=bekks,
        view_promo=promo,
        promos=promos,
        form=form,
        bekk_id_list=bekk_id_list,
        can_edit=can_edit,
    )


@bp.route("/reader/<int:id>", methods=["GET"])
@context.permission_only(PermissionType.read, PermissionScope.bekk)
def reader(id: int) -> typing.RouteReturn:
    """Bekk module bekk reading page"""

    bekk = Bekk.query.filter_by(id=id).one_or_none()

    filepath = os.path.join(flask.current_app.config["BEKKS_BASE_PATH"], str(id) + ".pdf")

    with open(filepath, "rb") as file:
        nb_pages = len(PyPDF2.PdfReader(file).pages)

    return flask.render_template("bekk/reader.html", title=bekk.name, bekk=bekk, nb_pages=nb_pages)
