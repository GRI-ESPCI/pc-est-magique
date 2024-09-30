"""PC est magique - Panier Bio Routes"""

import flask
from flask_babel import _

from app import context, db
from app.routes.panier_bio import bp, forms
from app.utils import typing, captcha
from app.models import (
    OrderPanierBio,
    PeriodPanierBio,
    PermissionScope,
    PermissionType,
    GlobalSetting,
)

import os
import datetime
import wtforms
from app.routes.panier_bio.utils import command_open, what_are_next_days, export_excel, get_period_id, validPeriodDates

app = flask.Flask(__name__)


@bp.route("", methods=["GET", "POST"])
@bp.route("/", methods=["GET", "POST"])
def main() -> typing.RouteReturn:
    """Panier Bio module main page"""

    connected = context.g.logged_in
    can_edit = context.has_permission(PermissionType.write, PermissionScope.panier_bio)

    today = datetime.date.today()

    if connected:
        # Previous orders query
        user = context.g.pceen
        all_orders = OrderPanierBio.query.filter_by(_pceen_id=user.id).filter(OrderPanierBio.date>=today).order_by(OrderPanierBio.date.asc()).all()
    else:
        all_orders = None
        user = None

    visibility = GlobalSetting.query.filter_by(key="ACCESS_PANIER_BIO").one().value
    if can_edit:
        visibility = 1

    panier_bio_day = GlobalSetting.query.filter_by(key="PANIER_BIO_DAY").one().value
    all_periods = PeriodPanierBio.query.filter_by(active=True).filter(PeriodPanierBio.end_date>=today).order_by(PeriodPanierBio.start_date.asc()).all()


    folder = "panier_bio"
    filename = "introduction.html"
    filepath = os.path.join(flask.current_app.config["PANIER_BIO_BASE_PATH"], filename)
    if not os.path.exists(filepath):
        open(filepath, "w").close()
    with open(filepath, "r") as f:
        html_file = f.read()

    # forms handling
    form = forms.PanierBio()

    can_command_next_day = False
    next_day = None
    form_visibility = 1

    if all_periods is None:
        visibility = 0

    else:
        next_days = what_are_next_days(
            panier_bio_day, today, all_periods
        )  # But tell me, what are the next days of Panier Bio ?
        if len(next_days) == 0:
            visibility = 0
        else:
            next_day = next_days[0]

            #Removing the next panier bio day if too close to day
            can_command_next_day = command_open(panier_bio_day, datetime.datetime.today(), next_day) #Are we the day before after the time limit ?
            if not can_command_next_day:
                next_days.pop(0)

            #Removing days where reservations where made
            if connected:
                i=0
                while i < len(next_days):
                    for order in all_orders:
                        if next_days[i] == order.date:
                            next_days.pop(i)
                            i=-1
                            break
                    i += 1

                if len(next_days) == 0:
                    form_visibility = 0
                # Pre-writing the form
                form.nom.data = user.nom
                form.prenom.data = user.prenom
                form.service.data = str(user.promo)

            else:
                user = None
                next_order = None
                all_orders = None

            form.dates.choices = [(day.strftime("%A %d %B %Y"), day.strftime("%A %d %B %Y")) for day in next_days]
    
    form_visibility = 0 if not visibility else form_visibility

    if all_orders is not None and len(all_orders) > 0:
        next_order = all_orders[0]

        can_delete_orders = [False for i in range(len(all_orders))]
        if connected:
            for i, order in enumerate(all_orders):

                if command_open(panier_bio_day, datetime.datetime.today(), order.date):
                    can_delete_orders[i] = True
    else:
        next_order = None
        can_delete_orders = None

    
    if form.is_submitted():
        
        #For a user to delete is panier bio wish
        delete = form["delete"].data
        
        if delete:
            order_del = OrderPanierBio.query.filter_by(id=form["id"].data).one()
            if type(order_del._pceen_id) == int: #Only a user can delete a wish
                if order_del._pceen_id == user.id: #Only a given user can delete his wish
                    if command_open(panier_bio_day, datetime.datetime.today(), order_del.date): #Can only delete if not too close to panier bio day
                        db.session.delete(order_del)
                        db.session.commit()

                        flask.flash(_("Commande supprimée"), "danger")
                        return flask.redirect(flask.url_for("panier_bio.main"))


        flag = False
        if 0 and not connected and not captcha.verify_captcha():
            flask.flash(
                _("Le captcha n'a pas pu être vérifié. Veuillez réessayer."),
                "danger",
            )
            flag = True
        if not connected and form["phone"].data == "":
            flask.flash(
                _("Si non connecté, un numéro de téléphone est obligatoire"),
                "danger",
            )
            flag = True
        if connected:
            for order in all_orders:
                for date in form["dates"].data:
                    if datetime.datetime.strptime(date,"%A %d %B %Y").date() == order.date:
                        flask.flash(
                        _("Vous avez déjà commandé un panier bio pour le %s" % date),
                        "danger",
                        )
                        flag = True       
     
        if not flag:
            add = form["add"].data
            
            if add:
                if not form["consent"].data:
                    flask.flash(_("Vous devez vous engagez à payer et venir chercher le panier"), "danger")
                else:
                    #order = [OrderPanierBio() for i in range(len(form["dates"].data))]
                    for date in form["dates"].data:
                        order = OrderPanierBio()
                        db.session.add(order)
                        order.name = form["prenom"].data + " " + form["nom"].data
                        order.service = form["service"].data
                        order.date = date
                        order._pceen_id = user.id if connected else None
                        order.phone_number = form["phone"].data
                        order.payment_method = form["payment_method"].data
                        order.comment = form["comment"].data
                        order._period_id = get_period_id(date, all_periods)

                    db.session.commit()
                    flask.flash(_("Votre panier a été commandé avec succès !"))
                    return flask.redirect(flask.url_for("panier_bio.main"))
            
        


    return flask.render_template(
        "panier_bio/main.html",
        title=_("Page du Panier Bio"),
        next_day=next_day if next_day is not None else None,
        user=user,
        today=today,
        visibility=visibility,
        can_edit=can_edit,
        can_command_next_day=can_command_next_day,
        folder=folder,
        html_file=html_file,
        form=form,
        all_orders=all_orders,
        next_order=next_order,
        connected=connected,
        can_delete_orders=can_delete_orders,
        form_visibility=form_visibility
    )


@bp.route("/admin", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.panier_bio)
def admin() -> typing.RouteReturn:
    """Panier Bio module admin page"""

    can_edit = context.has_permission(PermissionType.write, PermissionScope.panier_bio)

    if not can_edit:
        flask.abort(404)

    today = datetime.date.today()

    all_periods = PeriodPanierBio.query.order_by(PeriodPanierBio.start_date.asc()).all()
    all_orders = OrderPanierBio.query.filter(OrderPanierBio.date > today - datetime.timedelta(days=60)).all()
    date_list = sorted({order.date for order in all_orders}, reverse=True)

    visibility = GlobalSetting.query.filter_by(key="ACCESS_PANIER_BIO").one().value
    panier_bio_day = GlobalSetting.query.filter_by(key="PANIER_BIO_DAY").one().value

    next_days = what_are_next_days(panier_bio_day, today, all_periods)  # But tell me, what is the next day of Panier Bio ?
    if len(next_days) > 0:
        next_day = next_days[0]
    else:
        next_day = None

    show_date = flask.request.args.get("show_date") if not None else 0
    if show_date == None:
        show_date = 0
    else:
        show_date = int(show_date)

    if len(date_list) > 0:
        orders = (
            OrderPanierBio.query.filter(OrderPanierBio.date == date_list[show_date]).order_by(OrderPanierBio.name).all()
        )
    else:
        orders = []

    # Add Panier Bio settings
    setattr(
        forms.SettingsPanierBio,
        "visibility",
        wtforms.BooleanField(_("Visibilité de la page de réservation"), default=bool(visibility)),
    )
    setattr(
        forms.SettingsPanierBio,
        "day",
        wtforms.SelectField(
            _("Jour du panier bio"),
            choices=[
                ["1", "Lundi"],
                ["2", "Mardi"],
                ["3", "Mercredi"],
                ["4", "Jeudi"],
                ["5", "Vendredi"],
                ["6", "Samedi"],
                ["7", "Dimanche"],
            ],
            default=panier_bio_day,
        ),
    )

    # forms handling
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
            return flask.redirect(flask.url_for("panier_bio.admin", show_date=show_date))

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
            return flask.redirect(flask.url_for("panier_bio.admin", show_date=show_date))

        elif edit or delete:
            order = OrderPanierBio.query.filter_by(id=form["id"].data).one()

            if delete:
                db.session.delete(order)
                db.session.commit()

                flask.flash(_("Commande supprimée."))
                return flask.redirect(flask.url_for("panier_bio.admin", show_date=show_date))

            elif edit:
                order.payment_method = form["payment_method"].data
                order.date = form["date"].data
                order.payment_made = form["payed"].data
                order.treasurer_validate = form["treasurer_validate"].data
                order.taken = form["taken"].data
                order.comment = form["comment"].data

                db.session.commit()
                flask.flash(_("Commande éditée."))
                return flask.redirect(flask.url_for("panier_bio.admin", show_date=show_date))

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


@bp.route("/admin/periods", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.panier_bio)
def period() -> typing.RouteReturn:
    """Panier Bio module admin page"""

    can_edit = context.has_permission(PermissionType.write, PermissionScope.panier_bio)

    if not can_edit:
        flask.abort(404)

    periods = PeriodPanierBio.query.order_by(PeriodPanierBio.start_date.desc()).all()


    # forms handling
    form = forms.Period()

    if form.is_submitted() and can_edit:
        add = form["add"].data
        delete = form["delete"].data
        edit = form["edit"].data

        #Check if starting and ending dates of periods adding/modification does not overlap with existing orders bio period
        if not(validPeriodDates(form, periods)):
            flask.flash(_("Les dates de la période chevauchent sur une période existante."), "danger")

        else:
            if add:
                period = PeriodPanierBio()
                db.session.add(period)

                period.start_date = form["start_date"].data
                period.end_date = form["end_date"].data
                period.active = form["activate"].data
                period.disabled_days = form["disabled_days"].data

                db.session.commit()
                flask.flash(_("Periode ajoutée."))
                return flask.redirect(flask.url_for("panier_bio.period"))

            elif edit or delete:
                period = PeriodPanierBio.query.filter_by(id=form["id"].data).one()

                if delete:
                    db.session.delete(period)
                    db.session.commit()

                    flask.flash(_("Période supprimée."))
                    return flask.redirect(flask.url_for("panier_bio.period"))

                elif edit:
                    period.start_date = form["start_date"].data
                    period.end_date = form["end_date"].data
                    period.active = form["activate"].data
                    period.disabled_days = form["disabled_days"].data

                    db.session.commit()
                    flask.flash(_("Période éditée."))
                    return flask.redirect(flask.url_for("panier_bio.period"))

    return flask.render_template(
        "panier_bio/period.html",
        title=_("Administration Périodes Panier Bio"),
        form=form,
        periods=periods
    )


@bp.route("/validate/<int:id>/<type>", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.panier_bio)
def validate(id, type):

    show = flask.request.args.get("show") if not None else 0
    if show == None:
        show = 0
    else:
        show = int(show)

    if type == "active":
        period = PeriodPanierBio.query.get_or_404(id)
        period.active = False if period.active else True
        db.session.commit()
        return flask.redirect(flask.url_for("panier_bio.period"))
    
    else:
        order = OrderPanierBio.query.get_or_404(id)
        if type == "payment":
            order.payment_made = False if order.payment_made else True
        elif type == "treasurer":
            order.treasurer_validate = False if order.treasurer_validate else True
        elif type == "taken":
            order.taken = False if order.taken else True
        db.session.commit()
        return flask.redirect(flask.url_for("panier_bio.admin", show_date=show))


@bp.route("/edit_text", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.panier_bio)
def edit_text():
    content = flask.request.form.get("content")  # Retrieve the content from the POST request
    path = os.path.join(flask.current_app.config["PANIER_BIO_BASE_PATH"], "introduction.html")
    with open(path, "w") as file:
        file.write(content)

    flask.flash(_("Introduction mise à jour."))
    return flask.redirect(flask.url_for("panier_bio.main"))


@bp.route("/admin/generate_excel/<date>", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.panier_bio)
def generate_excel(date):
    """Sum up of informations concerning panier orders for the given day"""
    # Get orders
    orders: OrderPanierBio | None = OrderPanierBio.query.filter_by(date=date).all()
    if not orders or not context.g.pceen.has_permission(PermissionType.write, PermissionScope.panier_bio):
        flask.abort(404)

    # Create a response object to serve the Excel file
    response = flask.make_response()

    # Set the appropriate headers for the response
    response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    response.headers["Content-Disposition"] = f"attachment; filename=panier_bio_{date}.xlsx"

    # Write the Excel data from the BytesIO buffer to the response
    response.data = export_excel(date, orders).getvalue()
    return response
