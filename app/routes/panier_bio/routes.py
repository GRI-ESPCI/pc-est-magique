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
import wtforms
from app.utils.validators import DataRequired
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

    panier_bio_day = GlobalSetting.query.filter_by(key="PANIER_BIO_DAY").one().value


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
            next_order = all_orders[0] if all_orders[0].date == next_day else None
        else:
            next_order=None

        #Pre-writing the form
        form.nom.data = user.nom
        form.prenom.data = user.prenom
        form.service.data = str(user.promo)
    else:
        user=None
        next_order=None
        all_orders=None

    

    form.date.data = next_day
    
    if form.validate_on_submit():
        if 0 and not connected and not captcha.verify_captcha():
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
                    order.name = form["prenom"].data + " " + form["nom"].data
                    order.service = form["service"].data
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

    can_edit = context.has_permission(PermissionType.write, PermissionScope.panier_bio)


    today = datetime.datetime.today()

    all_orders = OrderPanierBio.query.filter(OrderPanierBio.date > today - datetime.timedelta(days=60)).all()
    date_list = sorted({order.date for order in all_orders}, reverse=True)

    visibility = GlobalSetting.query.filter_by(key="ACCESS_PANIER_BIO").one().value
    panier_bio_day = GlobalSetting.query.filter_by(key="PANIER_BIO_DAY").one().value


    #Dates questions answered
    date = datetime.datetime.today()
    next_day = what_is_next_day(panier_bio_day, date.date()) #But tell me, what is the next day of Panier Bio ?

    show_date = flask.request.args.get("show_date") if not None else 0
    if show_date == None:
        show_date = 0
    else:
        show_date=int(show_date)
    orders = OrderPanierBio.query.filter(OrderPanierBio.date == date_list[show_date]).order_by(OrderPanierBio.name).all()

    # Add Panier Bio settings
    setattr(forms.SettingsPanierBio, "visibility", wtforms.BooleanField(_("Visibilité de la page de réservation"), default=bool(visibility)),)
    setattr(forms.SettingsPanierBio, "day", wtforms.SelectField(_("Jour du panier bio"), choices = [["1", "Lundi"], ["2", "Mardi"], ["3", "Mercredi"], ["4", "Jeudi"], ["5", "Vendredi"], ["6", "Samedi"], ["7", "Dimanche"]], default=panier_bio_day),)


    #forms handling
    form = forms.PanierBio()
    form_settings = forms.SettingsPanierBio()

    if form_settings.is_submitted() and can_edit:
        submit = form_settings["submit"].data
        if submit:
            app.logger.info(form_settings.visibility.data)
            if form_settings.visibility.data:
                GlobalSetting.query.filter_by(key="ACCESS_PANIER_BIO").one().value = 1
            else:
                GlobalSetting.query.filter_by(key="ACCESS_PANIER_BIO").one().value = 0

            GlobalSetting.query.filter_by(key="PANIER_BIO_DAY").one().value = form_settings["day"].data

            db.session.commit()
            flask.flash(_("Mis à jour."))
            return flask.redirect(flask.url_for("panier_bio.admin"))


    if form.is_submitted() and can_edit:
        add = form["add"].data
        delete = form["delete"].data
        edit = form["edit"].data

        if add:
            order = OrderPanierBio()
            db.session.add(order)

            order.name = form["prenom"].data + " " + form["nom"].data
            order.service = form["service"].data
            order.phone_number = form["phone"].data
            order.payment_made = form["payed"].data
            order.payment_method = form["payment_method"].data
            order.date = form["date"].data
            order.comment = form["comment"].data
            
            db.session.commit()
            flask.flash(_("Commande effectuée."))
            return flask.redirect(flask.url_for("panier_bio.admin"))

        elif edit or delete:
            order = OrderPanierBio.query.filter_by(id=form["id"].data).one()

            if delete:
                db.session.delete(order)
                db.session.commit()

                flask.flash(_("Commande supprimée."))
                return flask.redirect(flask.url_for("panier_bio.admin"))
                        
            elif edit:
                order.payment_method = form["payment_method"].data
                order.date = form["date"].data
                order.payment_made = form["payed"].data
                order.comment = form["comment"].data

                db.session.commit()
                flask.flash(_("Commande éditée."))
                return flask.redirect(flask.url_for("panier_bio.admin"))


    return flask.render_template(
        "panier_bio/admin.html",
        title=_("Administration Panier Bio"),
        visibility=visibility,
        panier_bio_day=panier_bio_day,
        form=form,
        form_settings=form_settings,
        orders=orders,
        show_date=show_date,
        date_list=date_list,
        next_day=next_day,
    )


@bp.route('/<int:order_id>/pay', methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.panier_bio)
def pay_order(order_id):
    order = OrderPanierBio.query.get_or_404(order_id)
    order.payment_made = False if order.payment_made else True
    db.session.commit()
    return flask.redirect(flask.url_for('panier_bio.admin'))



@bp.route("/edit_text", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.panier_bio)
def edit_text():
    content = flask.request.form.get("content")  # Retrieve the content from the POST request
    path = os.path.join(flask.current_app.config["PANIER_BIO_BASE_PATH"], "introduction.html")
    with open(path, "w") as file:
        file.write(content)

    flask.flash(_("Introduction mise à jour."))
    return flask.redirect(flask.url_for("panier_bio.main"))
