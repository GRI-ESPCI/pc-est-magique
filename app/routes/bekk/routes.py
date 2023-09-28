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
    PCeen,
    Role,
    Permission,
)

import fitz
import os
import shutil


@bp.route("", methods=["GET", "POST"])
@bp.route("/", methods=["GET", "POST"])
# @context.permission_only(PermissionType.read, PermissionScope.bekk)
def main() -> typing.RouteReturn:
    """Bekk module main page"""

    bekks = Bekk.query.order_by(Bekk.date.desc()).all()
    promos = sorted({bekk.promo for bekk in bekks}, reverse=True)

    promo = flask.request.args.get("promo")
    if promo is None:
        promo = GlobalSetting.query.filter_by(key="PROMO_1A").one().value  # ID of the season to show
        if promo not in promos:
            promo = promo - 1
    promo = int(promo)
    if promo != 0:
        bekks = Bekk.query.filter_by(promo=promo).order_by(Bekk.date.desc()).all()

    bekk_path = flask.current_app.config["BEKKS_BASE_PATH"]

    form = forms.Bekk()

    if form.validate_on_submit():
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

                if not os.path.exists(os.path.join(bekk_path, form["promo"].data)):
                    os.mkdir(os.path.join(bekk_path, form["promo"].data))

                if not os.path.exists(os.path.join(bekk_path, form["promo"].data, form["bekk_name"].data)):
                    os.mkdir(os.path.join(bekk_path, form["promo"].data, form["bekk_name"].data))

                form["pdf_file"].data.save(
                    os.path.join(
                        bekk_path,
                        form["promo"].data,
                        form["bekk_name"].data,
                        form["bekk_name"].data + "_" + form["promo"].data + ".pdf",
                    )
                )

                pdf = fitz.open(
                    os.path.join(
                        bekk_path,
                        form["promo"].data,
                        form["bekk_name"].data,
                        form["bekk_name"].data + "_" + form["promo"].data + ".pdf",
                    )
                )
                for page in pdf:
                    pix = page.get_pixmap()
                    pix.save(
                        os.path.join(
                            bekk_path,
                            form["promo"].data,
                            form["bekk_name"].data,
                            form["bekk_name"].data + "_" + form["promo"].data + "_%i.png" % page.number,
                        )
                    )

                db.session.commit()
                flask.flash(_("Bekk ajouté."))
                return flask.redirect(flask.url_for("bekk.main", promo=promo))

        if not add:
            delete = form["delete"].data
            bekk = Bekk.query.filter_by(id=form["id"].data).one()

            if delete:
                db.session.delete(bekk)
                db.session.commit()

                shutil.rmtree(os.path.join(bekk_path, form["promo"].data, form["bekk_name"].data))

                flask.flash(_("Bekk supprimé."))
                return flask.redirect(flask.url_for("bekk.main", promo=promo))

            else:
                old_name = bekk.name
                old_promo = str(bekk.promo)

                bekk.name = form["bekk_name"].data
                bekk.promo = form["promo"].data
                bekk.date = form["date"].data

                if old_name != bekk.name or old_promo != bekk.promo:
                    old_path = os.path.join(bekk_path, old_promo, old_name)
                    files = os.listdir(os.path.join(bekk_path, old_promo, old_name))
                    for file in files:
                        if file.split(".")[-1] == "png":
                            os.rename(
                                os.path.join(old_path, file),
                                os.path.join(old_path, bekk.name + "_" + bekk.promo + "_" + file.split("_")[-1]),
                            )
                        else:
                            os.rename(
                                os.path.join(old_path, file),
                                os.path.join(old_path, bekk.name + "_" + bekk.promo + ".pdf"),
                            )

                    if old_name != bekk.name:
                        os.rename(old_path, os.path.join(bekk_path, old_promo, bekk.name))

                    if old_promo != bekk.promo:
                        if not os.path.exists(os.path.join(bekk_path, bekk.promo)):
                            os.mkdir(os.path.join(bekk_path, bekk.promo))
                        shutil.move(os.path.join(bekk_path, old_promo, bekk.name), os.path.join(bekk_path, bekk.promo))

                db.session.commit()
                flask.flash(_("Bekk édité."))
                return flask.redirect(flask.url_for("bekk.main", promo=promo))

    return flask.render_template(
        "bekk/main.html",
        title=_("Page du Bekk ESPCI"),
        bekks=bekks,
        view_promo=promo,
        promos=promos,
        bekk_path=bekk_path,
        form=form,
    )


@bp.route("/reader/<int:id>", methods=["GET"])
# @context.permission_only(PermissionType.read, PermissionScope.bekk)
def reader(id: int) -> typing.RouteReturn:
    """Bekk module main page"""

    bekk = Bekk.query.filter_by(id=id).one_or_none()

    filepath = os.path.join(
        flask.current_app.config["BEKKS_BASE_PATH"],
        str(bekk.promo),
        bekk.name,
    )
    pages = range(len(os.listdir(filepath)) - 1)

    return flask.render_template("bekk/reader.html", title=bekk.name, bekk=bekk, pages=pages)
