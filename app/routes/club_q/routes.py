"""PC est magique - Club Q Pages Routes"""

import flask
import os
from flask_babel import _

from app import context, db
from app.models import (
    ClubQSeason,
    ClubQSpectacle,
    ClubQSalle,
    ClubQVoeu,
    PermissionScope,
    PermissionType,
    GlobalSetting,
    PCeen,
    Role,
    Permission,
)
from app.routes.club_q import bp, forms
from app.utils import typing
from app.utils.validators import Optional

import wtforms

from app.routes.club_q.utils import pdf_client, pdf_spectacle, excel_spectacle

from app.routes.club_q.algorithm import attribution




@bp.route("", methods=["GET", "POST"])
@bp.route("/", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
# @context.permission_condition(lambda: bool(GlobalSetting.query.filter_by(key='ACCESS_CLUB_Q').one().value))
def main() -> typing.RouteReturn:
    """PC est magique Club Q page."""

    "If the page visibility is set at 0 in the admin parameters, don't show it"
    if not GlobalSetting.query.filter_by(key="ACCESS_CLUB_Q").one().value and not context.g.pceen.has_permission(
        PermissionType.all, PermissionScope.club_q
    ):
        flask.abort(404)

    # Ajout dynamique de 1 form par spectacle de la saison
    season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    spectacles = ClubQSpectacle.query.filter_by(_season_id=season_id).order_by(ClubQSpectacle.date).all()
    
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
                ("Priorité"),
                render_kw={"class": "form-control"},
                validators=[Optional()],
                default=voeu.priorite if voeu else None,
            ),
        )
        setattr(
            forms.ClubQForm,
            f"nb_places_{spect.id}",
            wtforms.IntegerField(
                ("Nombre places demandées"),
                render_kw={"class": "form-control"},
                validators=[Optional()],
                default=voeu.places_demandees if voeu else None,
            ),
        )
        setattr(
            forms.ClubQForm,
            f"nb_places_minimum_{spect.id}",
            wtforms.IntegerField(
                ("Nombre places minimum demandées"),
                render_kw={"class": "form-control"},
                validators=[Optional()],
                default=voeu.places_minimum if voeu else None,
            ),
        )

    # Gestion des requêtes
    form = forms.ClubQForm()

    if form.validate_on_submit():
        for spect in spectacles:
            if form[f"priorite_{spect.id}"].data:
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
                voeu.places_minimum = form[f"nb_places_minimum_{spect.id}"].data or None
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
        title=_("Page de réservation pour le Club Q"),
        form=form,
        spectacles=spectacles,
        season_id=season_id,
        user=context.g.pceen,
    )


@bp.route("/admin", methods=["GET", "POST"])
@bp.route("/admin/pceen", methods=["GET", "POST"])
@context.permission_only(PermissionType.all, PermissionScope.club_q)
def pceens() -> typing.RouteReturn:
    """Administration page for Club Q."""


    season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show

    subquery = ClubQVoeu.query.filter_by(_season_id = season_id).filter(ClubQVoeu._pceen_id == PCeen.id).exists()
    pceens = (
        PCeen.query.join(PCeen.roles)
        .join(Role.permissions)
        .filter(Permission.type == PermissionType.read, Permission.scope == PermissionScope.club_q).filter(subquery)
    )

    return flask.render_template(
        "club_q/admin/pceens.html",
        view="pceens",
        pceens=pceens,

    )

@bp.route("/admin/spectacles", methods=["GET", "POST"])
@context.permission_only(PermissionType.all, PermissionScope.club_q)
def spectacles() -> typing.RouteReturn:

    season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    spectacles = ClubQSpectacle.query.filter_by(_season_id=season_id).order_by(ClubQSpectacle.date).all()

    return flask.render_template(
        "club_q/admin/spectacles.html",
        view = "spectacles",
        spectacles=spectacles,
        season_id=season_id
        )

@bp.route("/admin/salles", methods=["GET", "POST"])
@context.permission_only(PermissionType.all, PermissionScope.club_q)
def salles() -> typing.RouteReturn:

    season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show

    subquery = ClubQSpectacle.query.filter_by(_season_id = season_id).filter(ClubQSpectacle._salle_id == ClubQSalle.id).exists()
    salles = ClubQSalle.query.filter(subquery).order_by(ClubQSalle.nom)

    return flask.render_template(
        "club_q/admin/salles.html",
        view = "salles",
        salles = salles
        )

@bp.route("/admin/voeux", methods=["GET", "POST"])
@context.permission_only(PermissionType.all, PermissionScope.club_q)
def voeux() -> typing.RouteReturn:


    season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    voeux = ClubQVoeu.query.filter_by(_season_id=season_id).order_by(ClubQVoeu.id).all()

    form_edit_voeu = forms.EditVoeu()
    form_delete_voeu = forms.DeleteVoeu()


    if form_edit_voeu.validate_on_submit():
        voeu = ClubQVoeu.query.filter_by(id=form_edit_voeu["id"].data).one()

        voeu.priorite = form_edit_voeu["priorite"].data
        voeu.places_demandees = form_edit_voeu["places_demandees"].data
        voeu.places_minimum = form_edit_voeu["places_minimum"].data or None
        voeu.places_attribuees = form_edit_voeu["places_attribuees"].data

        db.session.commit()
        flask.flash(_("Mis à jour."))

    return flask.render_template(
        "club_q/admin/voeux.html",
        view = "voeux",
        voeux=voeux,
        form_edit_voeu=form_edit_voeu,
        form_delete_voeu=form_delete_voeu
        )

@bp.route("/admin/saisons", methods=["GET", "POST"])
@context.permission_only(PermissionType.all, PermissionScope.club_q)
def saisons() -> typing.RouteReturn:

    return flask.render_template(
        "club_q/admin/saisons.html",
        view = "saisons",
        )

@bp.route("/admin/attribution", methods=["GET", "POST"])
@context.permission_only(PermissionType.all, PermissionScope.club_q)
def attribution() -> typing.RouteReturn:

    season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    seasons = ClubQSeason.query.order_by(ClubQSeason.id).all()
    spectacles = ClubQSpectacle.query.filter_by(_season_id=season_id).order_by(ClubQSpectacle.date).all()
    salles = ClubQSalle.query.order_by(ClubQSalle.nom).all()
    voeux = ClubQVoeu.query.filter_by(_season_id=season_id).order_by(ClubQVoeu.id).all()


    subquery = ClubQVoeu.query.filter(ClubQVoeu._pceen_id == PCeen.id).exists()
    pceens = (
        PCeen.query.join(PCeen.roles)
        .join(Role.permissions)
        .filter(Permission.type == PermissionType.read, Permission.scope == PermissionScope.club_q).filter(subquery)
    )

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

    # Ajout du form pour savoir si sauvegarde des résultats de l'algorithme
    setattr(
        forms.SettingAlgoClubQPage,
        "save",
        wtforms.BooleanField(
            default=bool(GlobalSetting.query.filter_by(key="SAVE_CLUB_Q_ALGORITHM_RESULT").one().value)
        ),
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
        log_algo="error"

   

    if form_algo_setting.validate_on_submit():
        if form_algo_setting.save.data:
            GlobalSetting.query.filter_by(key="SAVE_CLUB_Q_ALGORITHM_RESULT").one().value = 1

        else:
            GlobalSetting.query.filter_by(key="SAVE_CLUB_Q_ALGORITHM_RESULT").one().value = 0

        GlobalSetting.query.filter_by(key="DISCONTENT_BONUS_1A").one().value = form_algo_setting.m1A.data
        GlobalSetting.query.filter_by(key="DISCONTENT_BONUS_2A").one().value = form_algo_setting.m2A.data
        GlobalSetting.query.filter_by(key="DISCONTENT_BONUS_3A").one().value = form_algo_setting.m3A.data
        GlobalSetting.query.filter_by(key="DISCONTENT_BONUS_4A").one().value = form_algo_setting.m4A.data

        GlobalSetting.query.filter_by(key="PROMO_1A").one().value = form_algo_setting.promo.data

        db.session.commit()
        flask.flash(_("Mis à jour."))

    return flask.render_template(
        "club_q/admin/attribution.html",
        view = "attribution",
        form_algo_setting=form_algo_setting,
        voeux=voeux,
        season_id=season_id,
        pceens=pceens,
        log_algo=log_algo,
        )


@bp.route("/admin/mails", methods=["GET", "POST"])
@context.permission_only(PermissionType.all, PermissionScope.club_q)
def mails() -> typing.RouteReturn:

    return flask.render_template(
        "club_q/admin/mails.html",
        view = "mails",
        
        )

@bp.route("/admin/options", methods=["GET", "POST"])
@context.permission_only(PermissionType.all, PermissionScope.club_q)
def options() -> typing.RouteReturn:


    season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    seasons = ClubQSeason.query.order_by(ClubQSeason.id).all()

        # Ajout du form pour le choix de la visibilité de la page pour les options du Club Q
    setattr(
        forms.SettingClubQPage,
        "visibility",
        wtforms.BooleanField(default=bool(GlobalSetting.query.filter_by(key="ACCESS_CLUB_Q").one().value)),
    )

    # Ajout du form pour le choix de la saison à afficher pour les options du Club Q
    setattr(
        forms.SettingClubQPage,
        "saison",
        wtforms.SelectField(choices=[(s.id, s.nom) for s in seasons], default=season_id),
    )

    form_setting = forms.SettingClubQPage()

     # Cheking if something changed in forms
    if form_setting.validate_on_submit():
        if form_setting.visibility.data:
            GlobalSetting.query.filter_by(key="ACCESS_CLUB_Q").one().value = 1

        else:
            GlobalSetting.query.filter_by(key="ACCESS_CLUB_Q").one().value = 0

        GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value = form_setting.saison.data

        db.session.commit()
        flask.flash(_("Mis à jour."))

    return flask.render_template(
        "club_q/admin/options.html",
        view = "options",
        form_setting=form_setting
        )

@bp.route("/algorithm", methods=["GET", "POST"])
@context.permission_only(PermissionType.all, PermissionScope.club_q)
def algorithm() -> typing.RouteReturn:
    season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    promo_1A = GlobalSetting.query.filter_by(key="PROMO_1A").one().value  # ID of the season to show
    bonus = [
        GlobalSetting.query.filter_by(key="DISCONTENT_BONUS_1A").one().value,
        GlobalSetting.query.filter_by(key="DISCONTENT_BONUS_2A").one().value,
        GlobalSetting.query.filter_by(key="DISCONTENT_BONUS_3A").one().value,
        GlobalSetting.query.filter_by(key="DISCONTENT_BONUS_4A").one().value,
    ]

    subquery = ClubQVoeu.query.filter(ClubQVoeu._pceen_id == PCeen.id).exists()

    voeux = ClubQVoeu.query.filter_by(_season_id=season_id).all()
    pceens = (
        PCeen.query.join(PCeen.roles)
        .join(Role.permissions)
        .filter(Permission.type == PermissionType.read, Permission.scope == PermissionScope.club_q)
        .filter(subquery)
    )
    # Place attribution
    voeux, pceens = attribution(voeux, pceens, promo_1A, bonus)

    if (
        GlobalSetting.query.filter_by(key="SAVE_CLUB_Q_ALGORITHM_RESULT").one().value
    ):  # Save algorithm results in database ?
        # Commit the changes to the database
        db.session.commit()
        flask.flash(_("Mis à jour."))

    return flask.redirect(flask.url_for("club_q.admin", view="attribution"))

@bp.route("/delete_voeu/<id>", methods=["GET", "DELETE"])
@context.permission_only(PermissionType.all, PermissionScope.club_q)
def delete_voeu(id):

    voeu = ClubQVoeu.query.get_or_404(id)
    db.session.delete(voeu)
    db.session.commit()
    flask.flash(_("Voeu supprimé."))

    return flask.redirect(flask.request.referrer)

@bp.route("/user/<username>", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def user(username: str):
    """Sum up of informations about users regarding Club Q"""
    # Get user
    pceen: PCeen | None = PCeen.query.filter_by(username=username).one_or_none()
    if not pceen or (
        not context.g.pceen.has_permission(PermissionType.all, PermissionScope.club_q) and context.g.pceen != pceen
    ):
        flask.abort(404)

    season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    spectacles = ClubQSpectacle.query.filter_by(_season_id=season_id).order_by(ClubQSpectacle.date).all()
    voeux = ClubQVoeu.query.filter_by(_season_id=season_id).filter_by(_pceen_id=pceen.id).order_by(ClubQVoeu.id).all()

    return flask.render_template(
        "club_q/pceen.html",
        title=_(f"Récapitulatif Club Q - {pceen.full_name}"),
        spectacles=spectacles,
        voeux=voeux,
        season_id=season_id,
        pceen=pceen,
    )


@bp.route("/user/<username>/generate_pdf", methods=["GET"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def user_generate_pdf(username: str):
    """Receipt generation for Club Q as a PDF for the user"""
    # Get user
    pceen: PCeen | None = PCeen.query.filter_by(username=username).one_or_none()
    if not pceen or (
        not context.g.pceen.has_permission(PermissionType.all, PermissionScope.club_q) and context.g.pceen != pceen
    ):
        flask.abort(404)

    season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    season = ClubQSeason.query.filter_by(id=season_id).order_by(ClubQSeason.id).one()
    voeux = (
        ClubQVoeu.query.filter_by(_season_id=season_id)
        .filter_by(_pceen_id=pceen.id)
        .filter(ClubQVoeu.places_attribuees != 0)
        .order_by(ClubQVoeu.priorite)
        .all()
    )

    # Return the PDF as a response to the user
    response = flask.make_response(pdf_client(pceen, season, voeux).read())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename=club_q_{pceen.username}.pdf"
    return response


@bp.route("/spectacle/<int:id>", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def spectacle(id: str):
    """Sum up of informations concerning the club Q spectacle of the given id"""
    # Get spectacle
    spectacle: ClubQSpectacle | None = ClubQSpectacle.query.filter_by(id=id).one_or_none()
    if not spectacle or not context.g.pceen.has_permission(PermissionType.all, PermissionScope.club_q):
        flask.abort(404)

    season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    voeux = (
        ClubQVoeu.query.filter_by(_season_id=season_id)
        .filter_by(_spectacle_id=spectacle.id)
        .order_by(ClubQVoeu.id)
        .all()
    )

    return flask.render_template(
        "club_q/spectacle.html",
        title=_(f"Résumé {spectacle.nom}"),
        season_id=season_id,
        spectacle=spectacle,
        voeux=voeux,
    )


@bp.route("/spectacle/<int:id>/generate_pdf", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def spect_generate_pdf(id: str):
    """Sum up of informations concerning the club Q spectacle of the given id"""
    # Get spectacle
    spectacle: ClubQSpectacle | None = ClubQSpectacle.query.filter_by(id=id).one_or_none()
    if not spectacle or not context.g.pceen.has_permission(PermissionType.all, PermissionScope.club_q):
        flask.abort(404)

    season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
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


@bp.route("/spectacle/<int:id>/generate_excel", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def spect_generate_excel(id: str):
    """Sum up of informations concerning the club Q spectacle of the given id"""
    # Get spectacle
    spectacle: ClubQSpectacle | None = ClubQSpectacle.query.filter_by(id=id).one_or_none()
    if not spectacle or not context.g.pceen.has_permission(PermissionType.all, PermissionScope.club_q):
        flask.abort(404)

    season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
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
    response.headers["Content-Disposition"] = f"attachment; filename=club_q_{spectacle.nom}.xlsx"

    # Write the Excel data from the BytesIO buffer to the response
    response.data = excel_spectacle(spectacle, season, voeux_attrib, voeux_nan_attrib).getvalue()
    return response

@bp.route("/salle/<int:id>", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def salle(id: str):
    """Sum up of informations concerning the club Q salle of the given id"""
    salle = ClubQSalle.query.filter_by(id=id).one()

    return flask.render_template(
        "club_q/salle.html",
        title=_(salle.nom),

    )


