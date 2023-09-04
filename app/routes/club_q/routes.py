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
from app.utils.validators import Optional, DataRequired
from datetime import datetime

import wtforms

from app.routes.club_q.utils import (
    pdf_client,
    pdf_spectacle,
    excel_spectacle,
    pceen_sum_places_demandees,
    pceen_sum_places_attribuees,
    pceen_prix_total,
    spectacles_sum_places_attribuees,
    spectacles_sum_places_demandees,
    spectacles_sum_places
)

from app.routes.club_q.algorithm import attribution

from app.email import send_email


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
                voeu.places_minimum = form[f"nb_places_minimum_{spect.id}"].data or 0
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
        title=_("Page de réservation pour le Club Q"),
        form=form,
        spectacles=spectacles,
        season_id=season_id,
        user=context.g.pceen,
    )


@bp.route("/pceens", methods=["GET", "POST"])
@context.permission_only(PermissionType.all, PermissionScope.club_q)
def pceens() -> typing.RouteReturn:
    """Administration page for Club Q."""

    season_id = flask.request.args.get("season_id")
    if season_id == None:
        season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    season_id=int(season_id)

    showed_season = ClubQSeason.query.filter_by(id=season_id).one_or_none()
    saisons = ClubQSeason.query.all()
    subquery = ClubQVoeu.query.filter_by(_season_id=season_id).filter(ClubQVoeu._pceen_id == PCeen.id).exists()
    pceens = (
        PCeen.query.join(PCeen.roles)
        .join(Role.permissions)
        .filter(Permission.type == PermissionType.read, Permission.scope == PermissionScope.club_q)
        .filter(subquery)
    )

    sum_places_attribuees = []
    sum_places_demandees = []
    pceens_a_payer = []
    total_payement=0

    for pceen in pceens:
        voeux = ClubQVoeu.query.filter_by(_season_id=season_id).filter_by(_pceen_id=pceen.id).all()
        sum_places_demandees.append(pceen_sum_places_demandees(pceen, voeux))
        sum_places_attribuees.append(pceen_sum_places_attribuees(pceen, voeux))
        pceens_a_payer.append(pceen_prix_total(pceen, voeux))
        total_payement = sum(pceens_a_payer)

    form_discontent = forms.EditDiscontent()

    if form_discontent.validate_on_submit():
        pceen = PCeen.query.filter_by(id=form_discontent["id"].data).one()
        pceen.discontent = form_discontent["discontent"].data

        db.session.commit()
        flask.flash(_("Mécontentement édité."))
        return flask.redirect(flask.url_for("club_q.pceens", season_id=season_id))

    return flask.render_template(
        "club_q/pceens.html",
        view="pceens",
        pceens=pceens,
        saisons=saisons,
        season_id=season_id,
        redirect="club_q.pceens",
        user=context.g.pceen,
        showed_season=showed_season,
        size=range(pceens.count()),
        sum_places_demandees=sum_places_demandees,
        sum_places_attribuees=sum_places_attribuees,
        pceens_a_payer=pceens_a_payer,
        total_payement=total_payement,
        form_discontent=form_discontent
    )


@bp.route("/spectacles", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def spectacles() -> typing.RouteReturn:

    season_id = flask.request.args.get("season_id")
    if season_id == None:
        season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show

    saisons = ClubQSeason.query.all()
    salles = ClubQSalle.query.all()

    spectacles = ClubQSpectacle.query.filter_by(_season_id=season_id).order_by(ClubQSpectacle.date).all()

    setattr(
        forms.EditSpectacle,
        "salle_id",
        wtforms.SelectField("Salle", choices=[[salle.id, salle.nom] for salle in salles], validators=[DataRequired()]),
    )

    spect_sum_places = spectacles_sum_places(spectacles)
    spect_sum_places_demandees = spectacles_sum_places_demandees(spectacles)
    spect_sum_places_attribuees = spectacles_sum_places_attribuees(spectacles)

    form_spectacle = forms.EditSpectacle()

    if form_spectacle.validate_on_submit():
        add = form_spectacle["add"].data

        if add:
            spectacle = ClubQSpectacle()

            db.session.add(spectacle)

            spectacle.nom = form_spectacle["nom"].data
            spectacle._season_id = season_id
            spectacle._salle_id = form_spectacle["salle_id"].data
            spectacle.description = form_spectacle["description"].data
            spectacle.categorie = form_spectacle["categorie"].data
            spectacle.image_name = form_spectacle["image"].data
            spectacle.date = datetime.combine(form_spectacle["date"].data, form_spectacle["time"].data)
            spectacle.nb_tickets = form_spectacle["nb_tickets"].data
            spectacle.unit_price = form_spectacle["price"].data

            db.session.commit()
            flask.flash(_("Spectacle ajouté."))
            return flask.redirect(flask.url_for("club_q.spectacles", season_id=season_id))

        delete = form_spectacle["delete"].data
        spectacle = ClubQSpectacle.query.filter_by(id=form_spectacle["id"].data).one()

        if delete:
            db.session.delete(spectacle)
            db.session.commit()
            flask.flash(_("Spectacle supprimé."))
            return flask.redirect(flask.url_for("club_q.spectacles", season_id=season_id))

        else:
            spectacle.nom = form_spectacle["nom"].data
            spectacle._salle_id = form_spectacle["salle_id"].data
            spectacle.description = form_spectacle["description"].data
            spectacle.categorie = form_spectacle["categorie"].data
            spectacle.image_name = form_spectacle["image"].data
            spectacle.date = datetime.combine(form_spectacle["date"].data, form_spectacle["time"].data)
            spectacle.nb_tickets = form_spectacle["nb_tickets"].data
            spectacle.unit_price = form_spectacle["price"].data

            db.session.commit()
            flask.flash(_("Spectacle édité."))
            return flask.redirect(flask.url_for("club_q.spectacles", season_id=season_id))

    return flask.render_template(
        "club_q/spectacles.html",
        view="spectacles",
        spectacles=spectacles,
        season_id=int(season_id),
        saisons=saisons,
        redirect="club_q.spectacles",
        user=context.g.pceen,
        form_spectacle=form_spectacle,
        spect_sum_places=spect_sum_places,
        spect_sum_places_demandees=spect_sum_places_demandees,
        spect_sum_places_attribuees=spect_sum_places_attribuees
    )


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

    saisons = ClubQSeason.query.order_by(ClubQSeason.nom).all()

    form_salle = forms.EditSalle()

    if form_salle.validate_on_submit():
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
        salles=salles,
        season_id=int(season_id),
        saisons=saisons,
        redirect="club_q.salles",
        user=context.g.pceen,
        form_salle=form_salle,
    )


@bp.route("/voeux", methods=["GET", "POST"])
@context.permission_only(PermissionType.all, PermissionScope.club_q)
def voeux() -> typing.RouteReturn:

    season_id = flask.request.args.get("season_id")
    if season_id == None:
        season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show

    saisons = ClubQSeason.query.all()
    spectacles = ClubQSpectacle.query.filter_by(_season_id=season_id).order_by(ClubQSpectacle.date).all()
    pceens = (
        PCeen.query.join(PCeen.roles)
        .join(Role.permissions)
        .filter(Permission.type == PermissionType.read, Permission.scope == PermissionScope.club_q)
    )
    voeux = ClubQVoeu.query.filter_by(_season_id=season_id).order_by(ClubQVoeu.id).all()

    # Add spectacle select choice for adding voeu
    setattr(
        forms.AddVoeu,
        "spectacle_add",
        wtforms.SelectField(
            "Spectacle", choices=[[spect.id, spect.nom] for spect in spectacles], validators=[DataRequired()]
        ),
    )

    # Add pceens select choice for adding voeu
    setattr(
        forms.AddVoeu,
        "pceen_add",
        wtforms.SelectField(
            "Pcéen", choices=[[pceen.id, pceen.full_name] for pceen in pceens], validators=[DataRequired()]
        ),
    )

    # Forms
    form_add_voeu = forms.AddVoeu()
    form_edit_voeu = forms.EditVoeu()

    # If a form is validated
    if form_add_voeu.is_submitted():
        submit = form_add_voeu["submit_add"].data
        if submit:
            if form_add_voeu.validate():
                voeu = ClubQVoeu()
                voeu._spectacle_id = form_add_voeu["spectacle_add"].data
                voeu._pceen_id = form_add_voeu["pceen_add"].data
                voeu._season_id = season_id
                voeu.priorite = form_add_voeu["priorite_add"].data
                voeu.places_demandees = form_add_voeu["places_demandees_add"].data
                voeu.places_minimum = form_add_voeu["places_minimum_add"].data or 0
                voeu.places_attribuees = form_add_voeu["places_attribuees_add"].data

                db.session.add(voeu)
                db.session.commit()
                flask.flash(_("Voeu ajouté."))
                return flask.redirect(flask.url_for("club_q.voeux", season_id=season_id))

    if form_edit_voeu.is_submitted():
        delete = form_edit_voeu["delete_edit"].data
        if delete:
            voeu = ClubQVoeu.query.filter_by(id=form_edit_voeu["id_edit"].data).one()
            db.session.delete(voeu)

            db.session.commit()
            flask.flash(_("Voeu supprimé."))
            return flask.redirect(flask.url_for("club_q.voeux", season_id=season_id))

        if form_edit_voeu.validate():
            voeu = ClubQVoeu.query.filter_by(id=form_edit_voeu["id_edit"].data).one()

            voeu.priorite = form_edit_voeu["priorite_edit"].data
            voeu.places_demandees = form_edit_voeu["places_demandees_edit"].data
            voeu.places_minimum = form_edit_voeu["places_minimum_edit"].data or 0
            voeu.places_attribuees = form_edit_voeu["places_attribuees_edit"].data

            db.session.commit()
            flask.flash(_("Voeu édité."))
            return flask.redirect(flask.url_for("club_q.voeux", season_id=season_id))

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
@context.permission_only(PermissionType.all, PermissionScope.club_q)
def saisons() -> typing.RouteReturn:

    saisons = ClubQSeason.query.all()

    form_saison = forms.EditSaison()

    if form_saison.validate_on_submit():
        add = form_saison["add"].data

        if add:
            saison = ClubQSeason()

            db.session.add(saison)

            saison.nom = form_saison["nom"].data
            saison.promo_orga = form_saison["promo"].data
            saison.debut = form_saison["debut"].data
            saison.fin = form_saison["fin"].data
            saison.fin_inscription = form_saison["fin_inscription"].data

            db.session.add(saison)
            db.session.commit()
            flask.flash(_("Saison ajoutée."))
            return flask.redirect(flask.url_for("club_q.saisons"))

        delete = form_saison["delete"].data
        saison = ClubQSeason.query.filter_by(id=form_saison["id"].data).one()

        if delete:
            db.session.delete(saison)
            db.session.commit()
            flask.flash(_("Saison supprimée."))
            return flask.redirect(flask.url_for("club_q.saisons"))

        else:
            saison.nom = form_saison["nom"].data
            saison.promo_orga = form_saison["promo"].data
            saison.debut = form_saison["debut"].data
            saison.fin = form_saison["fin"].data
            saison.fin_inscription = form_saison["fin_inscription"].data

            db.session.commit()
            flask.flash(_("Saison éditée."))
            return flask.redirect(flask.url_for("club_q.saisons"))

    return flask.render_template(
        "club_q/saisons.html", saisons=saisons, view="saisons", user=context.g.pceen, form_saison=form_saison
    )


@bp.route("/attribution", methods=["GET", "POST"])
@context.permission_only(PermissionType.all, PermissionScope.club_q)
def attribution_manager() -> typing.RouteReturn:
    season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show

    subquery = ClubQVoeu.query.filter(ClubQVoeu._pceen_id == PCeen.id).exists()

    voeux = ClubQVoeu.query.filter_by(_season_id=season_id).all()
    pceens = (
        PCeen.query.join(PCeen.roles)
        .join(Role.permissions)
        .filter(Permission.type == PermissionType.read, Permission.scope == PermissionScope.club_q)
        .filter(subquery)
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


    if form_algo_setting.is_submitted():
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
            voeux, pceens = attribution(voeux, pceens, promo_1A, bonus, corruption)

            if save_results:  # Save algorithm results in database ?
                # Commit the changes to the database
                db.session.commit()
                flask.flash(_("Algorithme exécuté et résultats sauvegardés."))
            else:
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
        user=context.g.pceen
    )


@bp.route("/mails", methods=["GET", "POST"])
@context.permission_only(PermissionType.all, PermissionScope.club_q)
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

    form_mail = forms.Mail()

    if form_mail.validate_on_submit():
        date = form_mail["date"].data
        subject = f"Attribution Club Q {saison.nom}"
        for pceen in pceens:
            html_body = flask.render_template(
                "club_q/mails/reservation.html",
                saison=saison,
                pceen=pceen,
                date=date,
            )

            send_email(
                "club_q/mails",
                subject=f"[PC est magique - Club - Q] {subject}",
                sender="club_q",
                recipients={pceen.email: pceen.full_name},
                html_body=html_body,
            )

    return flask.render_template("club_q/mails.html", view="mails", form_mail=form_mail, user=context.g.pceen)


@bp.route("/options", methods=["GET", "POST"])
@context.permission_only(PermissionType.all, PermissionScope.club_q)
def options() -> typing.RouteReturn:
    season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    seasons = ClubQSeason.query.order_by(ClubQSeason.id).all()

    # Ajout du form pour le choix de la visibilité de la page pour les options du Club Q
    setattr(
        forms.SettingClubQPage,
        "visibility",
        wtforms.BooleanField(
            "Visibilité de la page de réservation",
            default=bool(GlobalSetting.query.filter_by(key="ACCESS_CLUB_Q").one().value),
        ),
    )

    setattr(
        forms.SettingClubQPage,
        "saison",
        wtforms.SelectField("Saison actuelle", choices=[(s.id, s.nom) for s in seasons], default=season_id),
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
    voeux = ClubQVoeu.query.filter_by(_season_id=season_id).filter_by(_pceen_id=pceen.id).order_by(ClubQVoeu.id).all()

    pceens = (
        PCeen.query.join(PCeen.roles)
        .join(Role.permissions)
        .filter(Permission.type == PermissionType.read, Permission.scope == PermissionScope.club_q)
    )

    saisons = ClubQSeason.query.all()

    user = context.g.pceen
    if user == pceen:
        view = "pceen_reservations"
    else:
        view = "pceen_view"


    # Add spectacle select choice for adding voeu
    setattr(
        forms.AddVoeu,
        "spectacle_add",
        wtforms.SelectField(
            "Spectacle", choices=[[spect.id, spect.nom] for spect in spectacles], validators=[DataRequired()]
        ),
    )

    # Add pceens select choice for adding voeu
    setattr(
        forms.AddVoeu,
        "pceen_add",
        wtforms.SelectField(
            "Pcéen", choices=[[pceen_.id, pceen_.full_name] for pceen_ in pceens], default = pceen.id, validators=[DataRequired()]
        ),
    )

    # Forms
    form_add_voeu = forms.AddVoeu()
    form_edit_voeu = forms.EditVoeu()

    # If a form is validated
    if form_add_voeu.is_submitted():
        submit = form_add_voeu["submit_add"].data
        if submit:
            if form_add_voeu.validate():
                voeu = ClubQVoeu()
                voeu._spectacle_id = form_add_voeu["spectacle_add"].data
                voeu._pceen_id = form_add_voeu["pceen_add"].data
                voeu._season_id = season_id
                voeu.priorite = form_add_voeu["priorite_add"].data
                voeu.places_demandees = form_add_voeu["places_demandees_add"].data
                voeu.places_minimum = form_add_voeu["places_minimum_add"].data or 0
                voeu.places_attribuees = form_add_voeu["places_attribuees_add"].data

                db.session.add(voeu)
                db.session.commit()
                flask.flash(_("Voeu ajouté."))
                return flask.redirect(flask.url_for("club_q.pceen_id", id=id, season_id=season_id))

    if form_edit_voeu.is_submitted():
        delete = form_edit_voeu["delete_edit"].data
        if delete:
            voeu = ClubQVoeu.query.filter_by(id=form_edit_voeu["id_edit"].data).one()
            db.session.delete(voeu)

            db.session.commit()
            flask.flash(_("Voeu supprimé."))
            return flask.redirect(flask.url_for("club_q.pceen_id", id=id, season_id=season_id))

        if form_edit_voeu.validate():
            voeu = ClubQVoeu.query.filter_by(id=form_edit_voeu["id_edit"].data).one()

            voeu.priorite = form_edit_voeu["priorite_edit"].data
            voeu.places_demandees = form_edit_voeu["places_demandees_edit"].data
            voeu.places_minimum = form_edit_voeu["places_minimum_edit"].data or 0
            voeu.places_attribuees = form_edit_voeu["places_attribuees_edit"].data

            db.session.commit()
            flask.flash(_("Voeu édité."))
            return flask.redirect(flask.url_for("club_q.pceen_id", id=id, season_id=season_id))

    

    total_places_demandees = pceen_sum_places_demandees(pceen, voeux)
    total_places_attribuees = pceen_sum_places_attribuees(pceen, voeux)
    prix_total = pceen_prix_total(pceen, voeux)

    return flask.render_template(
        "club_q/id/pceen.html",
        title=_(f"Récapitulatif - {pceen.full_name}"),
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
    )


@bp.route("/pceens/<id>/generate_pdf", methods=["GET"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def user_generate_pdf(username: str):
    """Receipt generation for Club Q as a PDF for the user"""
    # Get user
    pceen: PCeen | None = PCeen.query.filter_by(username=username).one_or_none()
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
        .all()
    )

    # Return the PDF as a response to the user
    response = flask.make_response(pdf_client(pceen, season, voeux).read())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename=club_q_{pceen.username}.pdf"
    return response


@bp.route("/spectacles/<int:id>", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def spectacle_id(id: str):
    """Sum up of informations concerning the club Q spectacle of the given id"""
    # Get spectacle
    spectacle: ClubQSpectacle | None = ClubQSpectacle.query.filter_by(id=id).one_or_none()
    if not spectacle or not context.g.pceen.has_permission(PermissionType.read, PermissionScope.club_q):
        flask.abort(404)

    season_id = GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    voeux = (
        ClubQVoeu.query.filter_by(_season_id=season_id)
        .filter_by(_spectacle_id=spectacle.id)
        .order_by(ClubQVoeu.id)
        .all()
    )

    return flask.render_template(
        "club_q/id/spectacle.html",
        title=_(f"{spectacle.nom}"),
        season_id=season_id,
        spectacle=spectacle,
        voeux=voeux,
        user=context.g.pceen,
        view="spectacles",
    )


@bp.route("/spectacles/<int:id>/generate_pdf", methods=["GET", "POST"])
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


@bp.route("/spectacles/<int:id>/generate_excel", methods=["GET", "POST"])
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


@bp.route("/salles/<int:id>", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def salle_id(id: str):
    """Sum up of informations concerning the club Q salle of the given id"""
    salle = ClubQSalle.query.filter_by(id=id).one()

    return flask.render_template(
        "club_q/id/salle.html", title=_(salle.nom), user=context.g.pceen, view="salle", salle=salle
    )
