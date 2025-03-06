"""PC est magique - Club Q Pages Routes"""

import flask
import os
from flask_babel import _
from sqlalchemy import desc

app = flask.Flask(__name__)

from app import context, db
from app.models import (
    ClubQSeason,
    ClubQSpectacle,
    ClubQSalle,
    ClubQVoeu,
    ClubQBrochure,
    PermissionScope,
    PermissionType,
    GlobalSetting,
    PCeen,
    Role,
    Permission,
)
from app.routes.club_q import bp, forms
from app.utils import typing
from app.utils.validators import Optional, DataRequired
from app.utils.nginx import get_nginx_access_token

import wtforms
import PyPDF2

from app.routes.club_q.utils import (
    pdf_client,
    pdf_spectacle,
    excel_spectacle,
    pceen_sum_places_demandees,
    pceen_sum_places_attribuees,
    pceen_prix_total,
    spectacles_sum_places_attribuees,
    spectacles_sum_places_demandees,
    spectacles_sum_places,
    voeu_form,
    spectacle_form,
    export_pdf_spectacles,
    export_excel_spectacles,
    exporter_excel_prix,
    sum_object,
)

from app.routes.club_q.algorithm import attribution

from app.email import send_email


@bp.route("", methods=["GET", "POST"])
@bp.route("/", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def main() -> typing.RouteReturn:
    """PC est magique Club Q page."""

    visibility = GlobalSetting.query.filter_by(key="ACCESS_CLUB_Q").one().value

    "If the page visibility is set at 0 in the admin parameters, don't show it"
    if not context.g.pceen.has_permission(PermissionType.read, PermissionScope.club_q):
        flask.abort(404)

    if context.g.pceen.has_permission(PermissionType.all, PermissionScope.club_q):
        visibility = 1

    can_edit = context.has_permission(PermissionType.write, PermissionScope.club_q)

    # Ajout dynamique de 1 form par spectacle de la saison
    season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    spectacles = ClubQSpectacle.query.filter_by(_season_id=season_id).order_by(ClubQSpectacle.date).all()

    saison = ClubQSeason.query.filter_by(id=season_id).first()
    brochure = ClubQBrochure.query.filter_by(_season_id=season_id).one_or_none()

    for spect in spectacles:
        voeu = ClubQVoeu.query.filter_by(
            _spectacle_id=spect.id,
            _pceen_id=context.g.pceen.id,
            _season_id=spect._season_id,
        ).first()

        setattr(
            forms.ClubQForm,
            f"priorite_{spect.id}",
            wtforms.IntegerField(
                (_("Priorité")),
                render_kw={"class": "form-control"},
                validators=[Optional()],
                default=voeu.priorite if voeu else None,
            ),
        )
        setattr(
            forms.ClubQForm,
            f"nb_places_{spect.id}",
            wtforms.IntegerField(
                (_("Nombre places demandées")),
                render_kw={"class": "form-control"},
                validators=[Optional()],
                default=voeu.places_demandees if voeu else None,
            ),
        )
        setattr(
            forms.ClubQForm,
            f"nb_places_minimum_{spect.id}",
            wtforms.IntegerField(
                (_("Nombre places minimum demandées")),
                render_kw={"class": "form-control"},
                validators=[Optional()],
                default=voeu.places_minimum if voeu else None,
            ),
        )

    compact = flask.request.args.get("compact")
    if compact is None:
        compact = 0
    compact = int(compact)

    folder = "club_q"
    filename = "introduction.html"
    filepath = os.path.join(flask.current_app.config["CLUB_Q_BASE_PATH"], filename)
    if not os.path.exists(filepath):
        open(filepath, "w").close()
    with open(filepath, "r") as f:
        html_file = f.read()

    # Gestion des requêtes
    form = forms.ClubQForm()

    if form.validate_on_submit():
        flag = False  # Flag to say if the form results are not following the rules

        # Checking if form rules are respected. Not twice the same number, and start from 1 to the i-e wish. One form field must be empty or have both (at minima) priority and number of places defined
        # Checking if one wish has a priority, then a number of places is defined and vice-versa
        for spect in spectacles:
            if form[f"priorite_{spect.id}"].data != None:
                if form[f"nb_places_{spect.id}"].data == None:
                    flask.flash(_("Un voeu a été défini avec une priorité mais sans un nombre de places."), "danger")
                    flag = True  # RAISE THE FLAG!
                    break
            if form[f"nb_places_{spect.id}"].data != None:
                if form[f"priorite_{spect.id}"].data == None:
                    flask.flash(_("Un voeu a été défini avec un nombre de places mais sans priorité."), "danger")
                    flag = True  # RAISE THE FLAG!
                    break

        # Cheking if the minimum number of places is not superior to the number of asked places
        for spect in spectacles:
            if form[f"nb_places_{spect.id}"].data != None:
                if form[f"nb_places_minimum_{spect.id}"].data != None:
                    if form[f"nb_places_minimum_{spect.id}"].data > form[f"nb_places_{spect.id}"].data:
                        flask.flash(
                            _(
                                "Un voeu a été défini avec un nombre de places minimum supérieur au nombre de places demandées."
                            ),
                            "danger",
                        )
                        flag = True  # RAISE THE FLAG!
                        break

        priority_list = []
        # Checking if every priority is different
        for spect in spectacles:
            priority = form[f"priorite_{spect.id}"].data
            if priority:
                if priority in priority_list:
                    flask.flash(_("Deux voeux ne peuvent avoir la même priorité."), "danger")
                    flag = True  # RAISE THE FLAG!
                    break
                priority_list.append(form[f"priorite_{spect.id}"].data)

        # Cheking if priority increase one by one from one.
        if sum(priority_list) != len(priority_list) * (len(priority_list) + 1) / 2:
            flask.flash(_("Les priorités doivent être croissantes de 1 en 1 en partant de 1."), "danger")
            flag = True  # RAISE THE FLAG!

        if not flag:  # If the form is correctly definied, save the results
            for spect in spectacles:
                if form[f"priorite_{spect.id}"].data != None:
                    voeu = ClubQVoeu.query.filter_by(
                        _spectacle_id=spect.id,
                        _pceen_id=context.g.pceen.id,
                        _season_id=spect._season_id,
                    ).first()
                    if not voeu:
                        voeu = ClubQVoeu(
                            _spectacle_id=spect.id,
                            _pceen_id=context.g.pceen.id,
                            _season_id=spect._season_id,
                        )
                        db.session.add(voeu)

                    voeu.priorite = form[f"priorite_{spect.id}"].data
                    voeu.places_demandees = form[f"nb_places_{spect.id}"].data
                    voeu.places_minimum = form[f"nb_places_minimum_{spect.id}"].data if form[f"nb_places_minimum_{spect.id}"].data != None else form[f"nb_places_{spect.id}"].data
                    voeu.places_attribuees = 0

                else:
                    voeu = ClubQVoeu.query.filter_by(
                        _spectacle_id=spect.id,
                        _pceen_id=context.g.pceen.id,
                        _season_id=spect._season_id,
                    ).first()
                    if voeu != None:
                        db.session.delete(voeu)

            db.session.commit()
            flask.flash(_("Vos choix ont été enregistrés."))

    return flask.render_template(
        "club_q/main.html",
        view="reservations",
        title=_(f"Page de réservation pour le Club Q"),
        form=form,
        spectacles=spectacles,
        season_id=season_id,
        user=context.g.pceen,
        visibility=visibility,
        saison=saison,
        compact=compact,
        brochure=brochure,
        can_edit=can_edit,
        folder=folder,
        html_file=html_file,
    )


@bp.route("/pceens", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def pceens() -> typing.RouteReturn:
    """Administration page for Club Q."""

    season_id = flask.request.args.get("season_id")
    if season_id == None:
        season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    season_id = int(season_id)

    showed_season = ClubQSeason.query.filter_by(id=season_id).one_or_none()
    saisons = ClubQSeason.query.order_by(desc(ClubQSeason.debut)).all()
    subquery = ClubQVoeu.query.filter_by(_season_id=season_id).filter(ClubQVoeu._pceen_id == PCeen.id).exists()
    pceens = PCeen.query.filter(subquery)

    sum_places_attribuees = []
    sum_places_demandees = []
    pceens_a_payer = []
    total_payement = 0
    nb_voeux = []

    for pceen in pceens:
        voeux = ClubQVoeu.query.filter_by(_season_id=season_id).filter_by(_pceen_id=pceen.id)
        sum_places_demandees.append(pceen_sum_places_demandees(pceen, voeux))
        sum_places_attribuees.append(pceen_sum_places_attribuees(pceen, voeux))
        pceens_a_payer.append(pceen_prix_total(pceen, voeux))
        total_payement = sum(pceens_a_payer)
        nb_voeux.append(sum_object(pceen, voeux))

    can_edit = context.has_permission(PermissionType.write, PermissionScope.club_q)

    form_discontent = forms.EditDiscontent()

    if form_discontent.validate_on_submit() and can_edit:
        pceen = PCeen.query.filter_by(id=form_discontent["id"].data).one()
        pceen.discontent = form_discontent["discontent"].data

        db.session.commit()
        flask.flash(_("Mécontentement édité."))
        return flask.redirect(flask.url_for("club_q.pceens", season_id=season_id))

    return flask.render_template(
        "club_q/pceens.html",
        view="pceens",
        size=range(pceens.count()),
        nb_pceens=pceens.count(),
        pceens=pceens,
        saisons=saisons,
        season_id=season_id,
        redirect="club_q.pceens",
        user=context.g.pceen,
        showed_season=showed_season,
        sum_places_demandees=sum_places_demandees,
        sum_places_attribuees=sum_places_attribuees,
        pceens_a_payer=pceens_a_payer,
        total_payement=total_payement,
        form_discontent=form_discontent,
        nb_voeux=nb_voeux,
        total_nb_voeux=sum(nb_voeux),
    )


@bp.route("/pceens/generate_excel", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def pceens_generate_excel():
    """Generate the resume of required payements from PCeens to the Club Q"""

    season_id = flask.request.args.get("season_id")
    if season_id == None:
        season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    season = ClubQSeason.query.filter_by(id=season_id).order_by(ClubQSeason.id).one()
    spectacles = ClubQSpectacle.query.filter_by(_season_id=season_id).order_by(ClubQSpectacle.date).all()
    subquery = ClubQVoeu.query.filter_by(_season_id=season_id).filter(ClubQVoeu._pceen_id == PCeen.id).exists()
    pceens = PCeen.query.filter(subquery)
    voeux = ClubQVoeu.query.filter_by(_season_id=season_id)

    # Create a response object to serve the Excel file
    response = flask.make_response()

    # Set the appropriate headers for the response
    response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    response.headers["Content-Disposition"] = f"attachment; filename=club_q_payements_{season.nom}.xlsx"

    # Write the Excel data from the BytesIO buffer to the response
    response.data = exporter_excel_prix(season, pceens, spectacles, voeux).getvalue()
    return response


@bp.route("/spectacles", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def spectacles() -> typing.RouteReturn:

    season_id = flask.request.args.get("season_id")
    if season_id == None:
        season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show

    saisons = ClubQSeason.query.order_by(desc(ClubQSeason.debut)).all()
    saison = ClubQSeason.query.filter_by(id=season_id).one()
    salles = ClubQSalle.query.all()

    spectacles = ClubQSpectacle.query.filter_by(_season_id=season_id).order_by(ClubQSpectacle.date)
    voeux = ClubQVoeu.query.filter_by(_season_id=season_id)

    spect_sum_places = spectacles_sum_places(spectacles)
    spect_sum_places_demandees = spectacles_sum_places_demandees(spectacles)
    spect_sum_places_attribuees = spectacles_sum_places_attribuees(spectacles)

    spect_nb_voeux = []

    for spectacle in spectacles:
        spect_sum_voeux = sum_object(spectacle, voeux)
        spect_nb_voeux.append(spect_sum_voeux)

    redirect = flask.url_for("club_q.spectacles", season_id=season_id)

    if spectacles.count() > 0:
        salle = salles[0]
    else:
        salle = None

    can_edit = context.has_permission(PermissionType.write, PermissionScope.club_q)

    spectacle_form(salles, salle, season_id, redirect, can_edit)

    form_spectacle = forms.EditSpectacle()

    return flask.render_template(
        "club_q/spectacles.html",
        view="spectacles",
        spectacles=spectacles.all(),
        season_id=int(season_id),
        saisons=saisons,
        redirect="club_q.spectacles",
        user=context.g.pceen,
        form_spectacle=form_spectacle,
        spect_sum_places=spect_sum_places,
        spect_sum_places_demandees=spect_sum_places_demandees,
        spect_sum_places_attribuees=spect_sum_places_attribuees,
        spect_nb_voeux=spect_nb_voeux,
        nb_spectacles=sum_object(saison, spectacles),
        size=range(spectacles.count()),
        total_nb_voeux=sum(spect_nb_voeux),
    )


@bp.route("/spectacles/<int:id>/export_pdfs", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def spect_export_pdfs(id: int):
    """Export the PDF spectacle resume for the given id season (or the actual one in the db)"""

    season_id = id
    if season_id == None:
        season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    season = ClubQSeason.query.filter_by(id=season_id).order_by(ClubQSeason.id).one()

    spectacles = ClubQSpectacle.query.filter_by(_season_id=season_id).order_by(ClubQSpectacle.date).all()

    voeux_attrib_list = []
    voeux_nan_attrib_list = []

    for spectacle in spectacles:
        voeux_attrib_list.append(
            ClubQVoeu.query.filter_by(_season_id=season_id)
            .filter_by(_spectacle_id=spectacle.id)
            .filter(ClubQVoeu.places_attribuees != 0)
            .order_by(ClubQVoeu.priorite)
            .all()
        )
        voeux_nan_attrib_list.append(
            ClubQVoeu.query.filter_by(_season_id=season_id)
            .filter_by(_spectacle_id=spectacle.id)
            .filter(ClubQVoeu.places_attribuees == 0)
            .order_by(ClubQVoeu.priorite)
            .all()
        )

    # Return the PDF as a response to the user
    response = flask.make_response(
        export_pdf_spectacles(spectacles, season, voeux_attrib_list, voeux_nan_attrib_list).read()
    )
    response.headers["Content-Type"] = "application/zip"
    response.headers["Content-Disposition"] = f"attachment; filename=pdf_spectacles_{season.nom}.zip"
    return response


@bp.route("/spectacles/<int:id>/generate_excels", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def spect_export_excels(id: int):
    """Export the excel spectacle resume for the given id season (or the actual one in the db)"""

    season_id = id
    if season_id == None:
        season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    season = ClubQSeason.query.filter_by(id=season_id).order_by(ClubQSeason.id).one()

    spectacles = ClubQSpectacle.query.filter_by(_season_id=season_id).order_by(ClubQSpectacle.date).all()

    voeux_attrib_list = []
    voeux_nan_attrib_list = []

    for spectacle in spectacles:
        voeux_attrib_list.append(
            ClubQVoeu.query.filter_by(_season_id=season_id)
            .filter_by(_spectacle_id=spectacle.id)
            .filter(ClubQVoeu.places_attribuees != 0)
            .order_by(ClubQVoeu.priorite)
            .all()
        )
        voeux_nan_attrib_list.append(
            ClubQVoeu.query.filter_by(_season_id=season_id)
            .filter_by(_spectacle_id=spectacle.id)
            .filter(ClubQVoeu.places_attribuees == 0)
            .order_by(ClubQVoeu.priorite)
            .all()
        )

    # Return the PDF as a response to the user
    response = flask.make_response(
        export_excel_spectacles(spectacles, season, voeux_attrib_list, voeux_nan_attrib_list).read()
    )
    response.headers["Content-Type"] = "application/zip"
    response.headers["Content-Disposition"] = f"attachment; filename=excel_spectacles_{season.nom}.zip"
    return response


@bp.route("/salles", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def salles() -> typing.RouteReturn:
    season_id = flask.request.args.get("season_id")

    if season_id == None:
        # season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
        season_id = -1
        salles = ClubQSalle.query.order_by(ClubQSalle.nom)

    else:
        subquery = (
            ClubQSpectacle.query.filter_by(_season_id=season_id)
            .filter(ClubQSpectacle._salle_id == ClubQSalle.id)
            .exists()
        )
        salles = ClubQSalle.query.filter(subquery).order_by(ClubQSalle.nom)

    saisons = ClubQSeason.query.order_by(desc(ClubQSeason.debut)).all()

    nb_spectacles = []

    for salle in salles:
        if season_id == -1:
            spectacles = ClubQSpectacle.query.filter_by(_salle_id=salle.id)
        else:
            spectacles = ClubQSpectacle.query.filter_by(_season_id=season_id).filter_by(_salle_id=salle.id)
        nb_spectacles.append(sum_object(salle, spectacles))

    can_edit = context.has_permission(PermissionType.write, PermissionScope.club_q)

    form_salle = forms.EditSalle()

    if form_salle.validate_on_submit() and can_edit:
        add = form_salle["add"].data

        if add:
            salle = ClubQSalle()

            db.session.add(salle)

            salle.nom = form_salle["nom"].data
            salle.description = form_salle["description"].data
            salle.url = form_salle["url"].data
            salle.adresse = form_salle["adresse"].data
            salle.latitude = form_salle["latitude"].data
            salle.longitude = form_salle["longitude"].data

            db.session.commit()
            flask.flash(_("Salle ajoutée."))
            return flask.redirect(flask.url_for("club_q.salles"))

        delete = form_salle["delete"].data
        salle = ClubQSalle.query.filter_by(id=form_salle["id"].data).one()

        if delete:
            db.session.delete(salle)
            db.session.commit()
            flask.flash(_("Salle supprimée."))
            return flask.redirect(flask.url_for("club_q.salles"))

        else:
            salle.nom = form_salle["nom"].data
            salle.description = form_salle["description"].data
            salle.url = form_salle["url"].data
            salle.adresse = form_salle["adresse"].data
            salle.latitude = form_salle["latitude"].data
            salle.longitude = form_salle["longitude"].data

            db.session.commit()
            flask.flash(_("Salle éditée."))
            return flask.redirect(flask.url_for("club_q.salles"))

    return flask.render_template(
        "club_q/salles.html",
        view="salles",
        salles=salles.all(),
        size=range(salles.count()),
        season_id=int(season_id),
        saisons=saisons,
        redirect="club_q.salles",
        user=context.g.pceen,
        form_salle=form_salle,
        nb_spectacles=nb_spectacles,
    )


@bp.route("/voeux", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def voeux() -> typing.RouteReturn:

    season_id = flask.request.args.get("season_id")
    if season_id == None:
        season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show

    saisons = ClubQSeason.query.order_by(desc(ClubQSeason.debut)).all()
    spectacles = ClubQSpectacle.query.filter_by(_season_id=season_id).order_by(ClubQSpectacle.date).all()
    pceens = (
        PCeen.query.join(PCeen.roles)
        .join(Role.permissions)
        .filter(Permission.type == PermissionType.read, Permission.scope == PermissionScope.club_q)
    )
    voeux = ClubQVoeu.query.filter_by(_season_id=season_id).order_by(ClubQVoeu.id).all()

    redirect = flask.url_for("club_q.voeux", season_id=season_id)

    if len(spectacles) > 0:
        spectacle = spectacles[0]
    else:
        spectacle = None

    can_edit = context.has_permission(PermissionType.write, PermissionScope.club_q)

    voeu_form(spectacles, spectacle, pceens, pceens[0], season_id, redirect, can_edit)

    # Forms
    form_add_voeu = forms.AddVoeu()
    form_edit_voeu = forms.EditVoeu()

    return flask.render_template(
        "club_q/voeux.html",
        view="voeux",
        voeux=voeux,
        form_add_voeu=form_add_voeu,
        form_edit_voeu=form_edit_voeu,
        season_id=int(season_id),
        saisons=saisons,
        redirect="club_q.voeux",
        user=context.g.pceen,
    )


@bp.route("/saisons", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def saisons() -> typing.RouteReturn:

    saisons = ClubQSeason.query.order_by(desc(ClubQSeason.debut))
    spectacles = ClubQSpectacle.query.filter_by().order_by(ClubQSpectacle.date)
    voeux = ClubQVoeu.query.filter_by()

    saison_nb_voeux = []
    saison_nb_spectacles = []
    saison_nb_pceens = []

    for saison in saisons:
        subquery = ClubQVoeu.query.filter_by(_season_id=saison.id).filter(ClubQVoeu._pceen_id == PCeen.id).exists()
        pceens = PCeen.query.filter(subquery)

        saison_nb_voeux.append(sum_object(saison, voeux))
        saison_nb_spectacles.append(sum_object(saison, spectacles))
        saison_nb_pceens.append(pceens.count())

    can_edit = context.has_permission(PermissionType.write, PermissionScope.club_q)

    form_saison = forms.EditSaison()

    if form_saison.validate_on_submit() and can_edit:
        add = form_saison["add"].data

        if add:
            saison = ClubQSeason()

            db.session.add(saison)

            saison.nom = form_saison["nom"].data
            saison.promo_orga = form_saison["promo"].data
            saison.debut = form_saison["debut"].data
            saison.fin = form_saison["fin"].data
            saison.fin_inscription = form_saison["fin_inscription"].data
            saison.attributions_visible = form_saison["attributions_visible"].data


            db.session.add(saison)
            db.session.commit()
            flask.flash(_("Saison ajoutée."))
            return flask.redirect(flask.url_for("club_q.saisons"))

        delete = form_saison["delete"].data
        saison = ClubQSeason.query.filter_by(id=form_saison["id"].data).one()

        if delete:
            db.session.delete(saison)

            path = os.path.join(flask.current_app.config["CLUB_Q_BASE_PATH"], str(saison.id))
            os.rmdir(path)

            db.session.commit()
            flask.flash(_("Saison supprimée."))
            return flask.redirect(flask.url_for("club_q.saisons"))

        else:
            saison.nom = form_saison["nom"].data
            saison.promo_orga = form_saison["promo"].data
            saison.debut = form_saison["debut"].data
            saison.fin = form_saison["fin"].data
            saison.fin_inscription = form_saison["fin_inscription"].data
            saison.attributions_visible = form_saison["attributions_visible"].data

            db.session.commit()
            flask.flash(_("Saison éditée."))
            return flask.redirect(flask.url_for("club_q.saisons"))

    return flask.render_template(
        "club_q/saisons.html",
        saisons=saisons.all(),
        view="saisons",
        user=context.g.pceen,
        form_saison=form_saison,
        saison_nb_pceens=saison_nb_pceens,
        saison_nb_voeux=saison_nb_voeux,
        saison_nb_spectacles=saison_nb_spectacles,
        size=range(saisons.count()),
    )


@bp.route("/attribution", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def attribution_manager() -> typing.RouteReturn:
    season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    subquery = ClubQVoeu.query.filter_by(_season_id=season_id).filter(ClubQVoeu._pceen_id == PCeen.id).exists()

    voeux = ClubQVoeu.query.filter_by(_season_id=season_id).order_by(ClubQVoeu.priorite).all()
    pceens = PCeen.query.filter(subquery).all()
    spectacles = ClubQSpectacle.query.filter_by(_season_id=season_id).order_by(ClubQSpectacle.date).all()

    # Ajout des forms pour choisir les mécontentements bonus
    discontent_bonus = [
        ("m1A", "DISCONTENT_BONUS_1A"),
        ("m2A", "DISCONTENT_BONUS_2A"),
        ("m3A", "DISCONTENT_BONUS_3A"),
        ("m4A", "DISCONTENT_BONUS_4A"),
    ]
    for i in range(4):
        setattr(
            forms.SettingAlgoClubQPage,
            discontent_bonus[i][0],
            wtforms.IntegerField(default=GlobalSetting.query.filter_by(key=discontent_bonus[i][1]).one().value),
        )

    # Ajout du form pour savoir promotion actuelle
    setattr(
        forms.SettingAlgoClubQPage,
        "promo",
        wtforms.IntegerField(default=GlobalSetting.query.filter_by(key="PROMO_1A").one().value),
    )

    form_algo_setting = forms.SettingAlgoClubQPage()

    try:
        # Get the last log file of algorithm attribution
        with open(os.path.join("logs", "club_q", "algorithm.log"), "r") as log_file:
            log_algo = log_file.read()
    except:
        log_algo = "error"

    can_edit = context.has_permission(PermissionType.write, PermissionScope.club_q)

    if form_algo_setting.is_submitted() and can_edit:
        submit = form_algo_setting["submit"].data
        if submit and form_algo_setting.validate_on_submit():
            GlobalSetting.query.filter_by(key="DISCONTENT_BONUS_1A").one().value = form_algo_setting.m1A.data
            GlobalSetting.query.filter_by(key="DISCONTENT_BONUS_2A").one().value = form_algo_setting.m2A.data
            GlobalSetting.query.filter_by(key="DISCONTENT_BONUS_3A").one().value = form_algo_setting.m3A.data
            GlobalSetting.query.filter_by(key="DISCONTENT_BONUS_4A").one().value = form_algo_setting.m4A.data

            GlobalSetting.query.filter_by(key="PROMO_1A").one().value = form_algo_setting.promo.data

            db.session.commit()
            flask.flash(_("Mis à jour."))

        launch = form_algo_setting["launch_algorithm"].data
        if launch:

            promo_1A = GlobalSetting.query.filter_by(key="PROMO_1A").one().value  # ID of the season to show
            bonus = [
                GlobalSetting.query.filter_by(key="DISCONTENT_BONUS_1A").one().value,
                GlobalSetting.query.filter_by(key="DISCONTENT_BONUS_2A").one().value,
                GlobalSetting.query.filter_by(key="DISCONTENT_BONUS_3A").one().value,
                GlobalSetting.query.filter_by(key="DISCONTENT_BONUS_4A").one().value,
            ]

            save_results = form_algo_setting["save_attribution"].data
            corruption = form_algo_setting["corruption"].data

            # Place attribution

            voeux_update, pceens = attribution(voeux, pceens, spectacles, promo_1A, bonus, corruption)
            #voeux = ClubQVoeu.query.filter_by(_season_id=season_id).order_by(ClubQVoeu.priorite).all()
            if save_results:  # Save algorithm results in database ?
                """
                app.logger.info("\n\n\n\n\n\n\n\n\n\n")
                app.logger.info(voeux)
                #Rollbacking to previous priorities
                for voeu_update in voeux_update:
                    for voeu in voeux:
                        if voeu.id == voeu_update.id:
                            app.logger.info(f"Before {voeu.priorite}, {voeu_update.priorite}")
                            voeu.priorite = voeu_update.priorite
                            app.logger.info(f"After {voeu.priorite}, {voeu_update.priorite}")
                """
                # Commit the changes to the database
                db.session.commit()
                flask.flash(_("Algorithme exécuté et résultats sauvegardés."))
            else:
                # Rollback any changes proposed to the database
                db.session.rollback()
                flask.flash(_("Algorithme exécuté."))

            try:
                # Get the last log file of algorithm attribution
                with open(os.path.join("logs", "club_q", "algorithm.log"), "r") as log_file:
                    log_algo = log_file.read()
            except:
                log_algo = "error"

            flask.redirect(flask.url_for("club_q.attribution_manager"))

    return flask.render_template(
        "club_q/attribution.html",
        view="attribution",
        form_algo_setting=form_algo_setting,
        season_id=season_id,
        log_algo=log_algo,
        user=context.g.pceen,
    )


@bp.route("/mails", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def mails() -> typing.RouteReturn:

    season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    saison = ClubQSeason.query.filter_by(id=season_id).one()
    subquery = ClubQVoeu.query.filter_by(_season_id=season_id).filter(ClubQVoeu._pceen_id == PCeen.id).exists()
    pceens = (
        PCeen.query.join(PCeen.roles)
        .join(Role.permissions)
        .filter(Permission.type == PermissionType.read, Permission.scope == PermissionScope.club_q)
        .filter(subquery)
    )

    voeux = ClubQVoeu.query.filter_by(_season_id=season_id).filter(ClubQVoeu.places_attribuees > 0)
    spectacles = ClubQSpectacle.query.filter_by(_season_id=season_id).order_by(ClubQSpectacle.date)
    salles = ClubQSalle.query.order_by(ClubQSalle.nom)

    can_edit = context.has_permission(PermissionType.write, PermissionScope.club_q)
    form_mail = forms.Mail()

    # Get access to Club Q RIB
    src_rib = os.path.join(flask.current_app.config["CLUB_Q_BASE_PATH"], "RIB_Club_Q.jpg")
    ip = flask.request.headers.get("X-Real-Ip") or flask.current_app.config["FORCE_IP"]
    token_args = get_nginx_access_token(src_rib, ip)
    rib = f"{src_rib}?{token_args}"

    if form_mail.validate_on_submit() and can_edit:
        date = form_mail["date"].data
        subject = f"Attribution Club Q {saison.nom}"
        for pceen in pceens:
            
            voeux_pceen = voeux.filter_by(_pceen_id=pceen.id).all()
            spectacles_list = []
            
            for voeu in voeux_pceen:
                spectacle = spectacles.filter_by(id=voeu._spectacle_id).one()
                salle = salles.filter_by(id=spectacle._salle_id).one()
                spectacles_list.append([f"{spectacle.nom} - {spectacle.date} - {salle.nom} : {voeu.places_attribuees} places attribuée(s), pour {spectacle.unit_price*voeu.places_attribuees} €"])

            if spectacles_list == []:
                spectacles_list = None

            html_body = flask.render_template(
                "club_q/mails/reservation.html", saison=saison, pceen=pceen, date=date, rib=rib, spectacles_list=spectacles_list
            )

            send_email(
                "club_q/mails",
                sender="CLUB_Q",
                subject=f"[PC est magique - Club - Q] {subject}",
                recipients={pceen.email: pceen.full_name},
                html_body=html_body,
                reply_to=form_mail["reply_to"].data,
            )

    return flask.render_template("club_q/mails.html", view="mails", form_mail=form_mail, user=context.g.pceen)


@bp.route("/options", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def options() -> typing.RouteReturn:
    season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    seasons = ClubQSeason.query.order_by(ClubQSeason.id).all()

    # Ajout du form pour le choix de la visibilité de la page pour les options du Club Q
    setattr(
        forms.SettingClubQPage,
        "visibility",
        wtforms.BooleanField(
            _("Visibilité de la page de réservation"),
            default=bool(GlobalSetting.query.filter_by(key="ACCESS_CLUB_Q").one().value),
        ),
    )

    setattr(
        forms.SettingClubQPage,
        "saison",
        wtforms.SelectField(_("Saison actuelle"), choices=[(s.id, s.nom) for s in seasons], default=season_id),
    )

    can_edit = context.has_permission(PermissionType.write, PermissionScope.club_q)

    form_setting = forms.SettingClubQPage()

    # Cheking if something changed in forms
    if form_setting.validate_on_submit() and can_edit:
        if form_setting.visibility.data:
            GlobalSetting.query.filter_by(key="ACCESS_CLUB_Q").one().value = 1

        else:
            GlobalSetting.query.filter_by(key="ACCESS_CLUB_Q").one().value = 0

        GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value = form_setting.saison.data

        db.session.commit()
        flask.flash(_("Mis à jour."))

    return flask.render_template("club_q/options.html", view="options", form_setting=form_setting, user=context.g.pceen)


@bp.route("/pceens/<id>", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def pceen_id(id: int):
    """Sum up of informations about users regarding Club Q"""

    # Get user
    pceen: PCeen | None = PCeen.query.filter_by(id=id).one_or_none()
    if not pceen or (
        not context.g.pceen.has_permission(PermissionType.all, PermissionScope.club_q) and context.g.pceen != pceen
    ):
        flask.abort(404)

    season_id = flask.request.args.get("season_id")
    if season_id == None:
        season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show

    spectacles = ClubQSpectacle.query.filter_by(_season_id=season_id).order_by(ClubQSpectacle.date).all()
    voeux = ClubQVoeu.query.filter_by(_season_id=season_id).filter_by(_pceen_id=pceen.id).order_by(ClubQVoeu.priorite)

    pceens = (
        PCeen.query.join(PCeen.roles)
        .join(Role.permissions)
        .filter(Permission.type == PermissionType.read, Permission.scope == PermissionScope.club_q)
    )

    saisons = ClubQSeason.query.order_by(desc(ClubQSeason.debut)).all()

    user = context.g.pceen
    if user == pceen:
        view = "pceen_reservations"
    else:
        view = "pceen_view"

    redirect = flask.url_for("club_q.pceen_id", id=id, season_id=season_id)

    if len(spectacles) > 0:
        spectacle = spectacles[0]
    else:
        spectacle = None

    can_edit = context.has_permission(PermissionType.write, PermissionScope.club_q)

    voeu_form(spectacles, spectacle, pceens, pceen, season_id, redirect, can_edit)

    # Forms
    form_add_voeu = forms.AddVoeu()
    form_edit_voeu = forms.EditVoeu()

    total_places_demandees = pceen_sum_places_demandees(pceen, voeux)
    total_places_attribuees = pceen_sum_places_attribuees(pceen, voeux)
    prix_total = pceen_prix_total(pceen, voeux)

    return flask.render_template(
        "club_q/id/pceen.html",
        title=_("Récapitulatif - ") + pceen.full_name,
        view=view,
        spectacles=spectacles,
        voeux=voeux,
        season_id=int(season_id),
        saisons=saisons,
        pceen=pceen,
        user=context.g.pceen,
        total_places_demandees=total_places_demandees,
        total_places_attribuees=total_places_attribuees,
        prix_total=prix_total,
        form_add_voeu=form_add_voeu,
        form_edit_voeu=form_edit_voeu,
        nb_voeux=voeux.count(),
    )


@bp.route("/pceens/<id>/generate_pdf", methods=["GET"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def user_generate_pdf(id: int):
    """Receipt generation for Club Q as a PDF for the user"""
    # Get user
    pceen: PCeen | None = PCeen.query.filter_by(id=id).one_or_none()
    if not pceen or (
        not context.g.pceen.has_permission(PermissionType.all, PermissionScope.club_q) and context.g.pceen != pceen
    ):
        flask.abort(404)

    season_id = flask.request.args.get("season_id")
    if season_id == None:
        season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show

    season = ClubQSeason.query.filter_by(id=season_id).order_by(ClubQSeason.id).one()
    voeux = (
        ClubQVoeu.query.filter_by(_season_id=season_id)
        .filter_by(_pceen_id=pceen.id)
        .filter(ClubQVoeu.places_attribuees != 0)
        .order_by(ClubQVoeu.priorite)
    )
    # Return the PDF as a response to the user
    response = flask.make_response(pdf_client(pceen, season, voeux).read())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename=club_q_{pceen.username}.pdf"
    return response


@bp.route("/spectacles/<int:id>", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def spectacle_id(id: int):
    """Sum up of informations concerning the club Q spectacle of the given id"""
    # Get spectacle
    spectacle: ClubQSpectacle | None = ClubQSpectacle.query.filter_by(id=id).one_or_none()
    if not spectacle or not context.g.pceen.has_permission(PermissionType.read, PermissionScope.club_q):
        flask.abort(404)

    season_id = spectacle._season_id
    voeux = (
        ClubQVoeu.query.filter_by(_season_id=season_id)
        .filter_by(_spectacle_id=spectacle.id)
        .order_by(ClubQVoeu.id)
        .all()
    )
    spectacles = ClubQSpectacle.query.filter_by(_season_id=season_id).order_by(ClubQSpectacle.date).all()

    pceens = (
        PCeen.query.join(PCeen.roles)
        .join(Role.permissions)
        .filter(Permission.type == PermissionType.read, Permission.scope == PermissionScope.club_q)
    )

    redirect = flask.url_for("club_q.spectacle_id", id=id, season_id=season_id)

    can_edit = context.has_permission(PermissionType.write, PermissionScope.club_q)

    voeu_form(spectacles, spectacle, pceens, pceens[0], season_id, redirect, can_edit)

    # Forms
    form_add_voeu = forms.AddVoeu()
    form_edit_voeu = forms.EditVoeu()

    return flask.render_template(
        "club_q/id/spectacle.html",
        title=spectacle.nom,
        season_id=season_id,
        spectacle=spectacle,
        voeux=voeux,
        user=context.g.pceen,
        view="spectacles",
        form_add_voeu=form_add_voeu,
        form_edit_voeu=form_edit_voeu,
        nb_total_voeux=len(voeux),
    )


@bp.route("/spectacles/<int:id>/generate_pdf", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def spect_generate_pdf(id: int):
    """Sum up of informations concerning the club Q spectacle of the given id"""
    # Get spectacle
    spectacle: ClubQSpectacle | None = ClubQSpectacle.query.filter_by(id=id).one_or_none()
    if not spectacle or not context.g.pceen.has_permission(PermissionType.all, PermissionScope.club_q):
        flask.abort(404)

    season_id = spectacle._season_id
    season = ClubQSeason.query.filter_by(id=season_id).order_by(ClubQSeason.id).one()

    voeux_attrib = (
        ClubQVoeu.query.filter_by(_season_id=season_id)
        .filter_by(_spectacle_id=spectacle.id)
        .filter(ClubQVoeu.places_attribuees != 0)
        .order_by(ClubQVoeu.priorite)
        .all()
    )
    voeux_nan_attrib = (
        ClubQVoeu.query.filter_by(_season_id=season_id)
        .filter_by(_spectacle_id=spectacle.id)
        .filter(ClubQVoeu.places_attribuees == 0)
        .order_by(ClubQVoeu.priorite)
        .all()
    )

    # Return the PDF as a response to the user
    response = flask.make_response(pdf_spectacle(spectacle, season, voeux_attrib, voeux_nan_attrib).read())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename=club_q_{spectacle.nom}.pdf"
    return response


@bp.route("/spectacles/<int:id>/generate_excel", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def spect_generate_excel(id: int):
    """Sum up of informations concerning the club Q spectacle of the given id"""
    # Get spectacle
    spectacle: ClubQSpectacle | None = ClubQSpectacle.query.filter_by(id=id).one_or_none()
    if not spectacle or not context.g.pceen.has_permission(PermissionType.write, PermissionScope.club_q):
        flask.abort(404)

    season_id = spectacle._season_id
    season = ClubQSeason.query.filter_by(id=season_id).order_by(ClubQSeason.id).one()

    voeux_attrib = (
        ClubQVoeu.query.filter_by(_season_id=season_id)
        .filter_by(_spectacle_id=spectacle.id)
        .filter(ClubQVoeu.places_attribuees != 0)
        .order_by(ClubQVoeu.priorite)
        .all()
    )
    voeux_nan_attrib = (
        ClubQVoeu.query.filter_by(_season_id=season_id)
        .filter_by(_spectacle_id=spectacle.id)
        .filter(ClubQVoeu.places_attribuees == 0)
        .order_by(ClubQVoeu.priorite)
        .all()
    )

    # Create a response object to serve the Excel file
    response = flask.make_response()

    # Set the appropriate headers for the response
    response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    response.headers["Content-Disposition"] = f"inline; filename=club_q_{spectacle.nom}.xlsx"

    # Write the Excel data from the BytesIO buffer to the response
    response.data = excel_spectacle(spectacle, season, voeux_attrib, voeux_nan_attrib).getvalue()
    return response


@bp.route("/salles/<int:id>", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def salle_id(id: int):
    """Sum up of informations concerning the club Q salle of the given id"""

    salle = ClubQSalle.query.filter_by(id=id).one()
    if not salle or not context.g.pceen.has_permission(PermissionType.read, PermissionScope.club_q):
        flask.abort(404)

    season_id = flask.request.args.get("season_id")
    if season_id == None:
        season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show

    saisons = ClubQSeason.query.order_by(desc(ClubQSeason.debut)).all()
    spectacles = (
        ClubQSpectacle.query.filter_by(_season_id=season_id)
        .filter_by(_salle_id=salle.id)
        .order_by(ClubQSpectacle.date)
        .all()
    )

    pceens = (
        PCeen.query.join(PCeen.roles)
        .join(Role.permissions)
        .filter(Permission.type == PermissionType.read, Permission.scope == PermissionScope.club_q)
    )
    salles = ClubQSalle.query.order_by(ClubQSalle.nom)

    spect_sum_places = spectacles_sum_places(spectacles)
    spect_sum_places_demandees = spectacles_sum_places_demandees(spectacles)
    spect_sum_places_attribuees = spectacles_sum_places_attribuees(spectacles)

    redirect = flask.url_for("club_q.salle_id", id=id, season_id=season_id)

    can_edit = context.has_permission(PermissionType.write, PermissionScope.club_q)

    spectacle_form(salles, salle, season_id, redirect, can_edit)

    form_spectacle = forms.EditSpectacle()

    return flask.render_template(
        "club_q/id/salle.html",
        title=_(salle.nom),
        user=context.g.pceen,
        view="salle",
        salle=salle,
        saisons=saisons,
        redirect="club_q.salle_id",
        season_id=int(season_id),
        spectacles=spectacles,
        spect_sum_places=spect_sum_places,
        spect_sum_places_demandees=spect_sum_places_demandees,
        spect_sum_places_attribuees=spect_sum_places_attribuees,
        form_spectacle=form_spectacle,
        nb_total_spectacles=len(spectacles),
    )


@bp.route("/plaquettes", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def brochures() -> typing.RouteReturn:
    """Club Q Brochure page"""

    brochures = ClubQBrochure.query.join(ClubQBrochure.season).order_by(ClubQSeason.debut.desc()).all()
    saisons = ClubQSeason.query.order_by(ClubQSeason.debut.desc()).all()

    forms.Brochure.season_id = wtforms.SelectField(
        _("Saison"),
        choices=[[saison.id, saison.nom] for saison in saisons],
        default=GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value,
        validators=[DataRequired()],
    )

    form = forms.Brochure()

    if form.validate_on_submit() and context.g.pceen.has_permission(PermissionType.write, PermissionScope.club_q):
        add = form["add"].data

        if add:
            flag = False
            if form["pdf_file"].data is None:
                flask.flash(_("Aucun fichier choisi."), "danger")
                flag = True

            for brochure in brochures:
                if brochure._season_id == int(form["season_id"].data):
                    flask.flash(_("Il y a déjà une plaquette associée à cette saison."), "danger")
                    flag = True

            if not flag:
                brochure = ClubQBrochure()

                brochure._season_id = form["season_id"].data

                db.session.add(brochure)
                db.session.commit()
                path = os.path.join(
                    flask.current_app.config["CLUB_Q_BASE_PATH"], "plaquettes", str(brochure.id) + ".pdf"
                )
                form["pdf_file"].data.save(path)

                flask.flash(_("Plaquette ajoutée."))
                return flask.redirect(flask.url_for("club_q.brochures"))

    brochure_id_list = [brochure.id for brochure in brochures]

    can_edit = context.has_permission(PermissionType.write, PermissionScope.club_q)

    return flask.render_template(
        "club_q/brochures.html",
        title=_("Plaquettes Club Q"),
        brochures=brochures,
        view="plaquettes",
        form=form,
        brochure_id_list=brochure_id_list,
        can_edit=can_edit,
        user=context.g.pceen,
    )


@bp.route("/reader/<int:id>", methods=["GET"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def brochure_reader(id: int) -> typing.RouteReturn:
    """Club Q module to reader brochures"""

    brochure = ClubQBrochure.query.filter_by(id=id).one_or_none()
    if brochure is None:
        flask.abort(404)

    filepath = os.path.join(flask.current_app.config["CLUB_Q_BASE_PATH"], "plaquettes", str(brochure.id) + ".pdf")

    redirect = flask.url_for("club_q.brochures")
    url = brochure.pdf_src_with_token
    download_name = brochure.id

    with open(filepath, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        nb_pages = len(reader.pages)
        height = reader.pages[0].mediabox.height
        width = reader.pages[0].mediabox.width
        dim = [width, height]

    return flask.render_template(
        "reader.html",
        brochure=brochure,
        nb_pages=nb_pages,
        dim=dim,
        redirect=redirect,
        url=url,
        download_name=download_name,
    )


@bp.route("/reader/delete/<int:id>", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def brochure_delete(id: int) -> typing.RouteReturn:

    brochure = ClubQBrochure.query.filter_by(id=id).one_or_none()
    if brochure is None:
        flask.abort(404)

    path = os.path.join(flask.current_app.config["CLUB_Q_BASE_PATH"], "plaquettes", str(brochure.id) + ".pdf")

    db.session.delete(brochure)
    db.session.commit()

    os.remove(path)

    flask.flash(_("Plaquette supprimée."))
    return flask.redirect(flask.url_for("club_q.brochures"))


@bp.route("/edit_text", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def edit_text():

    content = flask.request.form.get("content")  # Retrieve the content from the POST request
    path = os.path.join(flask.current_app.config["CLUB_Q_BASE_PATH"], "introduction.html")
    with open(path, "w") as file:
        file.write(content)

    flask.flash(_("Introduction mise à jour."))
    return flask.redirect(flask.url_for("club_q.main"))



@bp.route("/saisons/attrib_visible/<int:id>", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def visible(id):
    """
    Change the boolean variable to show/hide attributions for all wishes in a Club Q season
    """
    season = ClubQSeason.query.get_or_404(id)
    season.attributions_visible = False if season.attributions_visible else True
    db.session.commit()
    
    return flask.redirect(flask.url_for("club_q.saisons"))