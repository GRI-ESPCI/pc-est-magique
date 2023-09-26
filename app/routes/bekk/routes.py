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

@bp.route("", methods=["GET", "POST"])
@bp.route("/", methods=["GET", "POST"])
#@context.permission_only(PermissionType.read, PermissionScope.bekk)
def main() -> typing.RouteReturn:
    """Bekk module main page"""

    bekks = Bekk.query.order_by(Bekk.date).all()
    promos = []
    [promos.append(bekk.promo) for bekk in bekks if bekk.promo not in promos]


    promo = flask.request.args.get("promo")
    if promo == None:
        promo = GlobalSetting.query.filter_by(key="PROMO_1A").one().value  # ID of the season to show
        if promo not in promos:
            promo=promo-1
    promo=int(promo)
    if promo!=0:
        bekks = Bekk.query.filter_by(promo=promo).order_by(Bekk.date).all()
        
    filepath = flask.current_app.config["BEKKS_BASE_PATH"]

    form = forms.Bekk()

    if form.validate_on_submit():
        add = form["add"].data

        if add:
            bekk = Bekk()

            db.session.add(bekk)

            bekk.name = form["bekk_name"].data
            bekk.promo = form["promo"].data
            bekk.date = form["date"].data


            if not os.path.exists(os.path.join(filepath,form["promo"].data)):
                os.mkdir(os.path.join(filepath,form["promo"].data))

            if not os.path.exists(os.path.join(filepath,form["promo"].data, form["bekk_name"].data)):
                os.mkdir(os.path.join(filepath,form["promo"].data, form["bekk_name"].data))

            form["pdf_file"].data.save(os.path.join(filepath,form["promo"].data, form["bekk_name"].data, form["bekk_name"].data + "_" + form["promo"].data + ".pdf"))
            
            pdf = fitz.open(os.path.join(filepath,form["promo"].data, form["bekk_name"].data, form["bekk_name"].data + "_" + form["promo"].data + ".pdf"))
            for page in pdf:
                pix = page.get_pixmap() 
                pix.save(form["bekk_name"].data + "_" + form["promo"].data + "-%i.png" % page.number) 

            db.session.commit()
            flask.flash(_("Bekk ajouté."))
            return flask.redirect(flask.url_for("bekk.main", promo=promo))

        delete = form["delete"].data
        bekk = Bekk.query.filter_by(id=form["id"].data).one()

        if delete:
            db.session.delete(bekk)
            db.session.commit()
            flask.flash(_("Bekk supprimé."))
            return flask.redirect(flask.url_for("bekk.main", promo=promo))

        else:
            bekk.name = form["bekk_name"].data
            bekk.promo = form["promo"].data
            bekk.date = form["date"].data

            db.session.commit()
            flask.flash(_("Bekk édité."))
            return flask.redirect(flask.url_for("bekk.main", promo=promo))

    return flask.render_template(
        "bekk/main.html",
        title = _("Page du Bekk ESPCI"),
        bekks=bekks,
        view_promo=promo,
        promos=promos,
        filepath=filepath,
        form=form
    )


@bp.route("/reader/<int:id>", methods=["GET"])
#@context.permission_only(PermissionType.read, PermissionScope.bekk)
def reader(id : int) -> typing.RouteReturn:
    """Bekk module main page"""

    bekk = Bekk.query.filter_by(id=id).one_or_none()

    filepath = os.path.join(
        flask.current_app.config["BEKKS_BASE_PATH"],
        str(bekk.promo),
        bekk.name,
    )

    return flask.render_template(
        "bekk/reader.html",
        title = _(bekk.name),
        bekk=bekk,
        filepath=filepath
    )
