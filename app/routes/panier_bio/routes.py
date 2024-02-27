"""PC est magique - Panier Bio Routes"""

import flask
from flask_babel import _

from app import context, db
from app.routes.panier_bio import bp, forms
from app.utils import typing, captcha
from app.models import (
    OrderPanierBio,
    PermissionScope,
    PermissionType,
    GlobalSetting,
)

import os
import datetime
from app.routes.panier_bio.utils import command_open, what_is_next_day

app = flask.Flask(__name__)

@bp.route("", methods=["GET", "POST"])
@bp.route("/", methods=["GET", "POST"])
def main() -> typing.RouteReturn:
    """Panier Bio module main page"""

    connected = context.g.logged_in
    

    can_edit = context.has_permission(PermissionType.write, PermissionScope.panier_bio)

    visibility = GlobalSetting.query.filter_by(key="ACCESS_PANIER_BIO").one().value
    if can_edit:
        visibility = 1

    panier_bio_day = visibility = GlobalSetting.query.filter_by(key="PANIER_BIO_DAY").one().value


    folder = "panier_bio"
    filename = "introduction.html"
    filepath = os.path.join(flask.current_app.config["PANIER_BIO_BASE_PATH"], filename)
    if not os.path.exists(filepath):
        open(filepath, "w").close()
    with open(filepath, "r") as f:
        html_file = f.read()

    #Dates questions answered
    date = datetime.datetime.today()

    can_command = command_open(panier_bio_day, date) #Is the command page open?
    next_day = what_is_next_day(panier_bio_day, date.date()) #But tell me, what is the next day of Panier Bio ?

    #forms handling
    form = forms.PanierBio()

    if connected:
        #Previous orders query
        user = context.g.pceen
        all_orders = OrderPanierBio.query.filter_by(_pceen_id=user.id).order_by(OrderPanierBio.date.desc()).all()
        if len(all_orders) > 0:
            app.logger.info(f"{all_orders[0].date} {next_day}")
            next_order = all_orders[0] if all_orders[0].date == next_day else None
        else:
            next_order=None

        #Pre-writing the form
        form.nom.data = user.nom
        form.prenom.data = user.prenom
    else:
        user=None
        next_order=None
        all_orders=None

    

    form.date.data = next_day
    
    if form.validate_on_submit():
        if not connected and not captcha.verify_captcha():
                flask.flash(
                    _("Le captcha n'a pas pu être vérifié. Veuillez réessayer."),
                    "danger",
                )
        else:
            add = form["add"].data
            if add:
                if not form["consent"].data:
                    flask.flash(_("Vous devez vous engagez à payer et venir chercher le panier"), "danger")
                else:
                    order = OrderPanierBio()

                    db.session.add(order)

                    order._pceen_id = user.id if connected else None
                    order.phone_number = form["phone"].data
                    order.payment_method = form["payment_method"].data
                    order.date = form["date"].data
                    order.comment = form["comment"].data

                    db.session.commit()
                    flask.flash(_("Votre panier a été commandé avec succès !"))
                    return flask.redirect(flask.url_for("panier_bio.main"))

    return flask.render_template(
        "panier_bio/main.html",
        title=_("Page du Panier Bio"),
        next_day=next_day.strftime('%A %d %B %Y'),
        user=user,
        date=date,
        visibility=visibility,
        can_edit=can_edit,
        can_command=can_command,
        folder=folder,
        html_file=html_file,
        form=form,
        all_orders=all_orders,
        next_order=next_order,
        connected=connected
    )


@bp.route("/admin", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.panier_bio)
def admin() -> typing.RouteReturn:
    """Panier Bio module admin page"""

    if not context.g.pceen.has_permission(PermissionType.write, PermissionScope.panier_bio):
        flask.abort(404)

    date = datetime.datetime.today()

    all_orders = OrderPanierBio.query.filter_by(date.date()-date < datetime.timedelta(months=2)).all()
    date_list = sorted({order.date for order in all_orders}, reverse=True)

    visibility = GlobalSetting.query.filter_by(key="ACCESS_PANIER_BIO").one().value
    panier_bio_day = GlobalSetting.query.filter_by(key="PANIER_BIO_DAY").one().value

    show_date = flask.request.args.get("show_date")
    if show_date == None:
        show_date = 0
    orders = OrderPanierBio.query.filter_by(date == date_list[show_date]).all()


    #forms handling
    form = forms.PanierBio()

    if form.validate_on_submit() and context.g.pceen.has_permission(PermissionType.read, PermissionScope.panier_bio):
        add = form["add"].data

        if add:
            if not form["consent"].data:
                flask.flash(_("Vous devez vous engagez à payer et venir chercher le panier"), "danger")
            else:
                order = OrderPanierBio()

                db.session.add(order)

                order._pceen_id = form["user_id"].data
                order.payment_method = form["payment_method"].data
                order.date = form["date"].data
                order.payed = form["payed"].data
                order.comment = form["comment"].data

                db.session.commit()
                flask.flash(_("Votre panier a été commandé avec succès !"))
                return flask.redirect(flask.url_for("panier_bio.main"))

        if not add and context.g.pceen.has_permission(PermissionType.write, PermissionScope.panier_bio):
            delete = form["delete"].data
            order = OrderPanierBio.query.filter_by(id=form["id"].data).one()

            if delete:
                db.session.delete(order)
                db.session.commit()

                flask.flash(_("Commande supprimée."))
                return flask.redirect(flask.url_for("panier_bio.main"))

            else:
                order._pceen_id = form["_pceen_id"].data
                order.payment_method = form["payment_method"].data
                order.date = form["date"].data
                order.payed = form["payed"].data
                order.comment = form["comment"].data

                db.session.commit()
                flask.flash(_("Commande éditée."))
                return flask.redirect(flask.url_for("panier_bio.main"))


    return flask.render_template(
        "panier_bio/main.html",
        title=_("Page du Panier Bio"),
        visibility=visibility,
        form=form,
        orders=orders,
        show_date=show_date,
        date_list=date_list
    )



@bp.route("/edit_text", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.panier_bio)
def edit_text():
    content = flask.request.form.get("content")  # Retrieve the content from the POST request
    path = os.path.join(flask.current_app.config["PANIER_BIO_BASE_PATH"], "introduction.html")
    with open(path, "w") as file:
        file.write(content)

    flask.flash(_("Introduction mise à jour."))
    return flask.redirect(flask.url_for("panier_bio.main"))
