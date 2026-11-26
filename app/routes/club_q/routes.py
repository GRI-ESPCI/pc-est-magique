"""PC est magique - Club Q Pages Routes"""

from collections import Counter
from decimal import Decimal
import flask
import os
from flask_babel import _
from flask_wtf.csrf import validate_csrf
import sqlalchemy

from app import context, db
from app.models import (
    ClubQSeason,
    ClubQSpectacle,
    ClubQSalle,
    ClubQVoeu,
    ClubQBrochure,
    ClubQPayment,
    ClubQSalleRespo,
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
import PyPDF2

from app.routes.club_q.utils import (
    pdf_client,
    pdf_spectacle,
    excel_spectacle,
    spectacles_sum_places_attribuees,
    spectacles_sum_places_demandees,
    spectacles_sum_places,
    voeu_form,
    spectacle_form,
    export_pdf_spectacles,
    export_excel_spectacles,
    exporter_excel_prix,
    pceen_sort_key,
    voeux_total_price,
    voeux_sum_attribuees,
    voeux_sum_demandees,
    group_by,
    count_by,
)

from app.routes.club_q.algorithm import attribution

from app.email import send_email


def _active_season_id() -> int:
    """Return the currently configured active Club Q season ID."""
    return int(GlobalSetting.get_value("SEASON_NUMBER_CLUB_Q"))


def _season_spectacles(season_id: int) -> list[ClubQSpectacle]:
    """Return the spectacles of a season, ordered by date."""
    return db.session.scalars(
        db.select(ClubQSpectacle).filter_by(_season_id=season_id).order_by(ClubQSpectacle.date)
    ).all()


def _has_voeu_in_season(season_id: int):
    """Returns True if the PCeen has at least one vœu in the given season."""
    return db.select(ClubQVoeu).filter_by(_season_id=season_id).filter(ClubQVoeu._pceen_id == PCeen.id).exists()


def _season_voeux_pceens(season_id: int) -> list[PCeen]:
    """Return the PCeens with at least one vœu in the given season."""
    return db.session.scalars(db.select(PCeen).filter(_has_voeu_in_season(season_id))).all()


def _split_voeux_by_attribution(voeux) -> tuple[list[ClubQVoeu], list[ClubQVoeu]]:
    """Split vœux into (attributed, not attributed), preserving order."""
    attrib = [v for v in voeux if (v.places_attribuees or 0) > 0]
    nan_attrib = [v for v in voeux if (v.places_attribuees or 0) == 0]
    return attrib, nan_attrib


def _spectacle_voeux_split(spectacle: ClubQSpectacle) -> tuple[list[ClubQVoeu], list[ClubQVoeu]]:
    """Return (attributed, not attributed) vœux of a spectacle, ordered by priority."""
    voeux = db.session.scalars(
        db.select(ClubQVoeu)
        .filter_by(_season_id=spectacle._season_id, _spectacle_id=spectacle.id)
        .order_by(ClubQVoeu.priorite)
    ).all()
    return _split_voeux_by_attribution(voeux)


def _season_export_data(season_id: int):
    """Return (season, spectacles, attributed vœux lists, non-attributed vœux lists) for season exports."""
    season = db.get_or_404(ClubQSeason, season_id)
    spectacles = _season_spectacles(season_id)
    voeux_by_spectacle = group_by(
        db.session.scalars(db.select(ClubQVoeu).filter_by(_season_id=season_id).order_by(ClubQVoeu.priorite)).all(),
        "_spectacle_id",
    )
    splits = [_split_voeux_by_attribution(voeux_by_spectacle.get(spect.id, [])) for spect in spectacles]
    return season, spectacles, [a for a, _n in splits], [n for _a, n in splits]


def _voeu_forms(spectacles, spectacle, pceen, season_id: int, redirect: str):
    """Initialize and process the (add, edit) vœu admin forms; returns (form_add, form_edit, redirect_response)."""
    pceens = _club_q_pceens()
    if pceen is None and pceens:
        pceen = pceens[0]
    return voeu_form(spectacles, spectacle, pceens, pceen, season_id, redirect, True)


def _can_respo_view(pceen_id: int, salle_id: int, season: ClubQSeason) -> bool:
    """Whether a Respo salle may see the lists of a salle for a season (only once attributions are visible)."""
    return bool(season.attributions_visible) and ClubQSalleRespo.is_respo_for(pceen_id, salle_id, season.id)


def _parse_season_id(raw: str | None = None, *, default_to_active: bool = True) -> int | None:
    """Parse a season_id string into an int (returns 400 if malformed), optionally defaulting to active season."""
    if raw is None:
        return _active_season_id() if default_to_active else None
    try:
        return int(raw)
    except (TypeError, ValueError):
        flask.abort(400)


def _all_seasons() -> list[ClubQSeason]:
    """Return all Club Q seasons in consistent reverse-chronological order."""
    return db.session.scalars(db.select(ClubQSeason).order_by(*ClubQSeason.default_order())).all()


def _respo_visible_season_ids() -> set[int]:
    """Attribution-visible season IDs where the current user is a Respo salle (computed once per request)."""
    if "club_q_respo_season_ids" not in flask.g:
        flask.g.club_q_respo_season_ids = ClubQSalleRespo.season_ids_for(context.g.pceen.id, visible_only=True)
    return flask.g.club_q_respo_season_ids


@bp.context_processor
def inject_club_q_respo() -> dict[str, object]:
    """Expose admin & respo salle state to all Club Q templates."""
    pceen = getattr(context.g, "pceen", None)
    is_admin = bool(pceen) and context.has_permission(PermissionType.write, PermissionScope.club_q)
    if not pceen or is_admin:
        return {"is_admin": is_admin, "respo_season_ids": set(), "is_respo_salle": False}
    season_ids = _respo_visible_season_ids()
    return {"is_admin": False, "respo_season_ids": season_ids, "is_respo_salle": bool(season_ids)}


def _club_q_pceens_query():
    """Return a Select of PCeens with Club Q read access."""
    return db.select(PCeen).filter(
        PCeen.roles.any(
            Role.permissions.any(
                sqlalchemy.and_(
                    Permission.type.in_([PermissionType.read, PermissionType.all]),
                    Permission.scope == PermissionScope.club_q,
                )
            )
        )
    )


def _club_q_pceens() -> list[PCeen]:
    """Return all distinct PCeens with Club Q read access, ordered by (nom, prenom)."""
    pceens = db.session.scalars(_club_q_pceens_query()).all()
    return sorted(pceens, key=pceen_sort_key)


def _validate_csrf_or_abort() -> None:
    if flask.current_app.config.get("WTF_CSRF_ENABLED", True):
        token = flask.request.headers.get("X-CSRFToken") or flask.request.form.get("csrf_token")
        try:
            validate_csrf(token)
        except wtforms.ValidationError:
            flask.abort(400)


@bp.route("", methods=["GET", "POST"])
@bp.route("/", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def main() -> typing.RouteReturn:
    """PC est magique Club Q page."""

    visibility = GlobalSetting.get_value("ACCESS_CLUB_Q")

    "If the page visibility is set at 0 in the admin parameters, don't show it"
    if not context.g.pceen.has_permission(PermissionType.read, PermissionScope.club_q):
        flask.abort(404)

    if context.g.pceen.has_permission(PermissionType.all, PermissionScope.club_q):
        visibility = 1

    can_edit = context.has_permission(PermissionType.write, PermissionScope.club_q)

    # Ajout dynamique de 1 form par spectacle de la saison
    season_id = _active_season_id()
    spectacles = _season_spectacles(season_id)

    saison = db.session.get(ClubQSeason, season_id)
    brochure = db.session.scalars(db.select(ClubQBrochure).filter_by(_season_id=season_id)).one_or_none()

    class DynamicClubQForm(forms.ClubQForm):
        pass

    # (pceen, spectacle) is unique in DB, so at most one vœu per spectacle
    voeux_by_spectacle: dict[int, ClubQVoeu] = {
        voeu._spectacle_id: voeu
        for voeu in db.session.scalars(
            db.select(ClubQVoeu).filter_by(_pceen_id=context.g.pceen.id, _season_id=season_id)
        )
    }

    for spect in spectacles:
        voeu = voeux_by_spectacle.get(spect.id)

        setattr(
            DynamicClubQForm,
            f"priorite_{spect.id}",
            wtforms.IntegerField(
                (_("Priorité")),
                render_kw={"class": "form-control"},
                validators=[Optional()],
                default=voeu.priorite if voeu else None,
            ),
        )
        setattr(
            DynamicClubQForm,
            f"nb_places_{spect.id}",
            wtforms.IntegerField(
                (_("Nombre places demandées")),
                render_kw={"class": "form-control"},
                validators=[Optional()],
                default=voeu.places_demandees if voeu else None,
            ),
        )
        setattr(
            DynamicClubQForm,
            f"nb_places_minimum_{spect.id}",
            wtforms.IntegerField(
                (_("Nombre places minimum demandées")),
                render_kw={"class": "form-control"},
                validators=[Optional()],
                default=voeu.places_minimum if voeu else None,
            ),
        )

    folder = "club_q"
    filename = "introduction.html"
    filepath = os.path.join(flask.current_app.config["CLUB_Q_BASE_PATH"], filename)
    if not os.path.exists(filepath):
        open(filepath, "w").close()
    with open(filepath, "r") as f:
        html_file = f.read()

    # Gestion des requêtes
    form = DynamicClubQForm()
    server_errors: list[str] = []

    if form.is_submitted():
        if int(visibility or 0) != 1 or saison is None:
            flask.abort(403)

        invalid_numbers_msg = _("Les priorités et nombres de places doivent être des entiers supérieurs ou égaux à 1.")
        if not form.validate():
            if getattr(form, "csrf_token", None) and form.csrf_token.errors:
                flask.abort(400)
            server_errors.append(invalid_numbers_msg)
        else:
            def add_error(msg: str) -> None:
                if msg not in server_errors:
                    server_errors.append(msg)

            submitted = [
                (
                    spect,
                    form[f"priorite_{spect.id}"].data,
                    form[f"nb_places_{spect.id}"].data,
                    form[f"nb_places_minimum_{spect.id}"].data,
                )
                for spect in spectacles
            ]

            priority_list: list[int] = []
            for _spect, prio, nb_places, nb_min in submitted:
                if any(v is not None and v <= 0 for v in (prio, nb_places, nb_min)):
                    add_error(invalid_numbers_msg)
                if prio is not None and nb_places is None:
                    add_error(_("Un vœu a été défini avec une priorité mais sans nombre de places."))
                if nb_places is not None and prio is None:
                    add_error(_("Un vœu a été défini avec un nombre de places mais sans priorité."))
                if nb_min is not None and nb_places is None:
                    add_error(_("Un vœu a été défini avec un nombre de places minimum sans nombre de places demandées."))
                if nb_places is not None and nb_min is not None and nb_min > nb_places:
                    add_error(_("Un vœu a été défini avec un nombre de places minimum supérieur au nombre de places demandées."))
                if prio is not None and prio > 0:
                    priority_list.append(prio)

            duplicates = sorted(p for p, count in Counter(priority_list).items() if count > 1)
            if duplicates:
                add_error(
                    _("Égalité dans le classement : plusieurs vœux ont la même priorité (%(dups)s).", dups=", ".join(f"#{p}" for p in duplicates))
                )

            if priority_list:
                missing = sorted(set(range(1, max(priority_list) + 1)) - set(priority_list))
                if missing:
                    add_error(
                        _("Trou dans le classement : priorité(s) manquante(s) (%(missing)s). Les priorités doivent se suivre de 1 en 1.", missing=", ".join(f"#{p}" for p in missing))
                    )

            if not server_errors:
                for spect, prio, nb_places, nb_min in submitted:
                    voeu = voeux_by_spectacle.get(spect.id)
                    if prio is None:
                        if voeu is not None:
                            db.session.delete(voeu)
                        continue
                    if voeu is None:
                        voeu = ClubQVoeu(_spectacle_id=spect.id, _pceen_id=context.g.pceen.id, _season_id=spect._season_id)
                        db.session.add(voeu)
                    voeu.priorite = prio
                    voeu.places_demandees = nb_places
                    voeu.places_minimum = nb_min if nb_min is not None else nb_places
                    voeu.places_attribuees = 0

                db.session.commit()
                flask.flash(_("Vos choix ont été enregistrés."), "success")
                return flask.redirect(flask.url_for("club_q.main"))

    spectacles_demandes = sorted(
        [spect for spect in spectacles if spect.id in voeux_by_spectacle],
        key=lambda spect: (voeux_by_spectacle[spect.id].priorite, spect.date),
    )
    spectacles_non_classes = [spect for spect in spectacles if spect.id not in voeux_by_spectacle]

    return flask.render_template(
        "club_q/main.html",
        view="reservations",
        title=_("Page de réservation pour le Club Q"),
        form=form,
        spectacles=spectacles,
        spectacles_demandes=spectacles_demandes,
        spectacles_non_classes=spectacles_non_classes,
        server_errors=server_errors,
        season_id=season_id,
        user=context.g.pceen,
        visibility=visibility,
        saison=saison,
        brochure=brochure,
        can_edit=can_edit,
        folder=folder,
        html_file=html_file,
    )


@bp.route("/pceens", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def pceens() -> typing.RouteReturn:
    """Administration page for Club Q."""

    season_id = _parse_season_id(flask.request.args.get("season_id"))

    saisons = _all_seasons()
    pceens = sorted(_season_voeux_pceens(season_id), key=pceen_sort_key)
    paid_pceen_ids = ClubQPayment.paid_pceen_ids(season_id)

    voeux_by_pceen = group_by(
        db.session.scalars(
            db.select(ClubQVoeu)
            .options(sqlalchemy.orm.selectinload(ClubQVoeu.spectacle))
            .filter_by(_season_id=season_id)
        ).all(),
        "_pceen_id",
    )
    # (pceen, nb vœux, places demandées, places attribuées, prix)
    pceen_rows = []
    for pceen in pceens:
        pceen_voeux = voeux_by_pceen.get(pceen.id, [])
        pceen_rows.append((
            pceen,
            len(pceen_voeux),
            voeux_sum_demandees(pceen_voeux),
            voeux_sum_attribuees(pceen_voeux),
            voeux_total_price(pceen_voeux),
        ))
    total_nb_voeux = sum(cnt for _, cnt, _, _, _ in pceen_rows)
    total_places_demandees = sum(dem for _, _, dem, _, _ in pceen_rows)
    total_places_attribuees = sum(attr for _, _, _, attr, _ in pceen_rows)
    total_payement = sum((cost for _, _, _, _, cost in pceen_rows), Decimal("0.00"))
    total_restant = sum(
        (cost for pceen, _, _, _, cost in pceen_rows if pceen.id not in paid_pceen_ids),
        Decimal("0.00"),
    )

    can_edit = context.has_permission(PermissionType.write, PermissionScope.club_q)

    form_discontent = forms.EditDiscontent()

    if form_discontent.validate_on_submit() and can_edit:
        pceen = db.session.scalars(db.select(PCeen).filter_by(id=form_discontent["id"].data)).one()
        pceen.discontent = form_discontent["discontent"].data

        db.session.commit()
        flask.flash(_("Mécontentement édité."), "success")
        return flask.redirect(flask.url_for("club_q.pceens", season_id=season_id))

    return flask.render_template(
        "club_q/pceens.html",
        view="pceens",
        pceen_rows=pceen_rows,
        saisons=saisons,
        season_id=season_id,
        redirect="club_q.pceens",
        user=context.g.pceen,
        total_places_demandees=total_places_demandees,
        total_places_attribuees=total_places_attribuees,
        paid_pceen_ids=paid_pceen_ids,
        total_payement=total_payement,
        total_restant=total_restant,
        form_discontent=form_discontent,
        total_nb_voeux=total_nb_voeux,
    )


@bp.route("/pceens/<int:id>/paid", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def set_paid(id: int) -> typing.RouteReturn:
    """Set the payment status of a PCeen for a Club Q season.

    Expects ``?season_id=<id>`` (mandatory, never defaults to the active season) and a JSON body ``{"paid": bool}``.
    """
    _validate_csrf_or_abort()

    db.get_or_404(PCeen, id)
    season_id = _parse_season_id(flask.request.args.get("season_id"), default_to_active=False)
    if season_id is None:
        flask.abort(400)
    db.get_or_404(ClubQSeason, season_id)

    paid = (flask.request.get_json(silent=True) or {}).get("paid")
    if not isinstance(paid, bool):
        flask.abort(400)

    ClubQPayment.set_paid(id, season_id, paid)
    db.session.commit()
    return flask.jsonify({"paid": paid})


@bp.route("/pceens/generate_excel", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def pceens_generate_excel():
    """Generate the resume of required payements from PCeens to the Club Q"""

    season_id = _parse_season_id(flask.request.args.get("season_id"))
    season = db.get_or_404(ClubQSeason, season_id)
    spectacles = _season_spectacles(season_id)
    pceens = _season_voeux_pceens(season_id)
    voeux = db.select(ClubQVoeu).filter_by(_season_id=season_id)
    paid_pceen_ids = ClubQPayment.paid_pceen_ids(season_id)

    # Create a response object to serve the Excel file
    response = flask.make_response()

    # Set the appropriate headers for the response
    response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    response.headers["Content-Disposition"] = f"attachment; filename=club_q_payements_{season.nom}.xlsx"

    # Write the Excel data from the BytesIO buffer to the response
    response.data = exporter_excel_prix(season, pceens, spectacles, voeux, paid_pceen_ids).getvalue()
    return response


@bp.route("/spectacles", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def spectacles() -> typing.RouteReturn:
    can_edit = context.has_permission(PermissionType.write, PermissionScope.club_q)
    respo_season_ids = _respo_visible_season_ids() if not can_edit else set()
    if not can_edit and not respo_season_ids:
        flask.abort(403)

    saisons = _all_seasons()
    raw_season_id = flask.request.args.get("season_id")
    season_id = _parse_season_id(raw_season_id)
    if raw_season_id is None and not can_edit and season_id not in respo_season_ids:
        season_id = next((s.id for s in saisons if s.id in respo_season_ids), season_id)

    db.get_or_404(ClubQSeason, season_id)
    if not can_edit and season_id not in respo_season_ids:
        flask.abort(403)

    spectacles_stmt = db.select(ClubQSpectacle).filter_by(_season_id=season_id).order_by(ClubQSpectacle.date)
    if not can_edit:
        respo_salle_ids = ClubQSalleRespo.salle_ids_for(context.g.pceen.id, season_id)
        spectacles_stmt = spectacles_stmt.filter(ClubQSpectacle._salle_id.in_(respo_salle_ids))

    spectacles_list = db.session.scalars(spectacles_stmt).all()

    spect_sum_places = spectacles_sum_places(spectacles_list)
    spect_sum_places_demandees = spectacles_sum_places_demandees(spectacles_list)
    spect_sum_places_attribuees = spectacles_sum_places_attribuees(spectacles_list)
    nb_voeux_by_spectacle = count_by(ClubQVoeu._spectacle_id, ClubQVoeu._season_id == season_id)
    spect_nb_voeux = [nb_voeux_by_spectacle.get(spectacle.id, 0) for spectacle in spectacles_list]

    form_spectacle = None
    if can_edit:
        salles = db.session.scalars(db.select(ClubQSalle).order_by(ClubQSalle.nom)).all()
        salle = salles[0] if spectacles_list and salles else None
        redirect = flask.url_for("club_q.spectacles", season_id=season_id)
        form_spectacle, resp = spectacle_form(salles, salle, season_id, redirect, can_edit)
        if resp is not None:
            return resp

    return flask.render_template(
        "club_q/spectacles.html",
        view="spectacles",
        spectacles=spectacles_list,
        season_id=season_id,
        saisons=saisons,
        is_respo_view=not can_edit,
        redirect="club_q.spectacles",
        user=context.g.pceen,
        form_spectacle=form_spectacle,
        spect_sum_places=spect_sum_places,
        spect_sum_places_demandees=spect_sum_places_demandees,
        spect_sum_places_attribuees=spect_sum_places_attribuees,
        spect_nb_voeux=spect_nb_voeux,
        nb_spectacles=len(spectacles_list),
        size=range(len(spectacles_list)),
        total_nb_voeux=sum(spect_nb_voeux),
    )

@bp.route("/spectacles/<int:id>/export_pdfs", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def spect_export_pdfs(id: int):
    """Export the PDF spectacle resume for the given season ID."""

    season, spectacles, voeux_attrib_list, voeux_nan_attrib_list = _season_export_data(id)

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
    """Export the excel spectacle resume for the given season ID."""

    season, spectacles, voeux_attrib_list, voeux_nan_attrib_list = _season_export_data(id)

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
    season_id = _parse_season_id(flask.request.args.get("season_id"), default_to_active=False)
    all_seasons = season_id is None

    if all_seasons:
        salles = db.session.scalars(db.select(ClubQSalle).order_by(ClubQSalle.nom)).all()
    else:
        subquery = (
            db.select(ClubQSpectacle).filter_by(_season_id=season_id)
            .filter(ClubQSpectacle._salle_id == ClubQSalle.id)
            .exists()
        )
        salles = db.session.scalars(db.select(ClubQSalle).filter(subquery).order_by(ClubQSalle.nom)).all()

    saisons = _all_seasons()
    respo_season_id = _active_season_id() if all_seasons else season_id
    respo_season = db.session.get(ClubQSeason, respo_season_id)

    season_filter = () if all_seasons else (ClubQSpectacle._season_id == season_id,)
    nb_spectacles_by_salle = count_by(ClubQSpectacle._salle_id, *season_filter)
    nb_spectacles = [nb_spectacles_by_salle.get(salle.id, 0) for salle in salles]

    can_edit = context.has_permission(PermissionType.write, PermissionScope.club_q)
    respos_by_salle = ClubQSalleRespo.respos_by_salle(respo_season_id) if can_edit else {}
    eligible_pceens = _club_q_pceens() if can_edit else []

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
            flask.flash(_("Salle ajoutée."), "success")
            return flask.redirect(flask.url_for("club_q.salles"))

        delete = form_salle["delete"].data
        salle = db.session.scalars(db.select(ClubQSalle).filter_by(id=form_salle["id"].data)).one()

        if delete:
            db.session.delete(salle)
            db.session.commit()
            flask.flash(_("Salle supprimée."), "success")
            return flask.redirect(flask.url_for("club_q.salles"))

        else:
            salle.nom = form_salle["nom"].data
            salle.description = form_salle["description"].data
            salle.url = form_salle["url"].data
            salle.adresse = form_salle["adresse"].data
            salle.latitude = form_salle["latitude"].data
            salle.longitude = form_salle["longitude"].data

            db.session.commit()
            flask.flash(_("Salle éditée."), "success")
            return flask.redirect(flask.url_for("club_q.salles"))

    return flask.render_template(
        "club_q/salles.html",
        view="salles",
        salles=salles,
        size=range(len(salles)),
        season_id=season_id,
        all_seasons=all_seasons,
        saisons=saisons,
        respo_season=respo_season,
        respos_by_salle=respos_by_salle,
        eligible_pceens=eligible_pceens,
        redirect="club_q.salles",
        user=context.g.pceen,
        form_salle=form_salle,
        nb_spectacles=nb_spectacles,
    )


@bp.route("/salles/<int:id>/respo", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def set_salle_respo(id: int) -> typing.RouteReturn:
    """Assign or remove the Respos salle for a given (salle, season)."""
    _validate_csrf_or_abort()

    salle = db.get_or_404(ClubQSalle, id)
    season_id = _parse_season_id(flask.request.form.get("season_id"), default_to_active=False)
    if season_id is None:
        flask.abort(400)
    season = db.get_or_404(ClubQSeason, season_id)

    def _redirect_back() -> typing.RouteReturn:
        return_to = flask.request.form.get("return_to")
        if return_to == "salle":
            return flask.redirect(flask.url_for("club_q.salle_id", id=salle.id, season_id=season.id))
        return_sid = _parse_season_id(flask.request.form.get("return_season_id") or None, default_to_active=False)
        return flask.redirect(flask.url_for("club_q.salles", season_id=return_sid))

    try:
        pceen_ids = {int(v) for v in flask.request.form.getlist("pceen_ids") if v.strip()}
    except ValueError:
        flask.abort(400)

    pceens = [db.get_or_404(PCeen, pid) for pid in pceen_ids]
    for pceen in pceens:
        if not pceen.has_permission(PermissionType.read, PermissionScope.club_q):
            flask.flash(_("%(nom)s n'a pas accès au Club Q.", nom=pceen.full_name), "danger")
            return _redirect_back()

    if ClubQSalleRespo.set_respos(salle.id, season.id, pceen_ids):
        db.session.commit()
        if not pceens:
            flask.flash(_("Respo(s) salle retiré·e(s) pour %(salle)s (%(saison)s).", salle=salle.nom, saison=season.nom), "success")
        else:
            noms = ", ".join(p.full_name for p in sorted(pceens, key=pceen_sort_key))
            flask.flash(_("Respo(s) de %(salle)s (%(saison)s) : %(noms)s.", salle=salle.nom, saison=season.nom, noms=noms), "success")

    return _redirect_back()


@bp.route("/voeux", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def voeux() -> typing.RouteReturn:

    season_id = _parse_season_id(flask.request.args.get("season_id"))

    saisons = _all_seasons()
    spectacles = _season_spectacles(season_id)
    voeux = db.session.scalars(db.select(ClubQVoeu).filter_by(_season_id=season_id).order_by(ClubQVoeu.id)).all()

    form_add_voeu, form_edit_voeu, resp = _voeu_forms(
        spectacles,
        spectacles[0] if spectacles else None,
        None,
        season_id,
        flask.url_for("club_q.voeux", season_id=season_id),
    )
    if resp is not None:
        return resp

    return flask.render_template(
        "club_q/voeux.html",
        view="voeux",
        voeux=voeux,
        form_add_voeu=form_add_voeu,
        form_edit_voeu=form_edit_voeu,
        season_id=season_id,
        saisons=saisons,
        redirect="club_q.voeux",
        user=context.g.pceen,
    )


@bp.route("/saisons", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def saisons() -> typing.RouteReturn:

    saisons = _all_seasons()

    nb_voeux_by_season = count_by(ClubQVoeu._season_id)
    nb_spectacles_by_season = count_by(ClubQSpectacle._season_id)
    nb_pceens_by_season = dict(
        db.session.execute(
            db.select(ClubQVoeu._season_id, sqlalchemy.func.count(sqlalchemy.distinct(ClubQVoeu._pceen_id)))
            .group_by(ClubQVoeu._season_id)
        ).all()
    )
    saison_nb_voeux = [nb_voeux_by_season.get(saison.id, 0) for saison in saisons]
    saison_nb_spectacles = [nb_spectacles_by_season.get(saison.id, 0) for saison in saisons]
    saison_nb_pceens = [nb_pceens_by_season.get(saison.id, 0) for saison in saisons]

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
            saison.attributions_visible = False

            db.session.add(saison)
            db.session.commit()
            flask.flash(_("Saison ajoutée."), "success")
            return flask.redirect(flask.url_for("club_q.saisons"))

        delete = form_saison["delete"].data
        saison = db.session.scalars(db.select(ClubQSeason).filter_by(id=form_saison["id"].data)).one()

        if delete:
            db.session.delete(saison)

            path = os.path.join(flask.current_app.config["CLUB_Q_BASE_PATH"], str(saison.id))
            if os.path.exists(path):
                os.rmdir(path)

            db.session.commit()
            flask.flash(_("Saison supprimée."), "success")
            return flask.redirect(flask.url_for("club_q.saisons"))

        else:
            saison.nom = form_saison["nom"].data
            saison.promo_orga = form_saison["promo"].data
            saison.debut = form_saison["debut"].data
            saison.fin = form_saison["fin"].data
            saison.fin_inscription = form_saison["fin_inscription"].data

            db.session.commit()
            flask.flash(_("Saison éditée."), "success")
            return flask.redirect(flask.url_for("club_q.saisons"))

    return flask.render_template(
        "club_q/saisons.html",
        saisons=saisons,
        view="saisons",
        user=context.g.pceen,
        form_saison=form_saison,
        saison_nb_pceens=saison_nb_pceens,
        saison_nb_voeux=saison_nb_voeux,
        saison_nb_spectacles=saison_nb_spectacles,
        size=range(len(saisons)),
    )


@bp.route("/attribution", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def attribution_manager() -> typing.RouteReturn:
    season_id = _active_season_id()

    voeux = db.session.scalars(db.select(ClubQVoeu).filter_by(_season_id=season_id).order_by(ClubQVoeu.priorite)).all()
    pceens = _season_voeux_pceens(season_id)
    spectacles = _season_spectacles(season_id)

    # Mécontentements bonus
    discontent_bonus = [
        ("m1A", "DISCONTENT_BONUS_1A"),
        ("m2A", "DISCONTENT_BONUS_2A"),
        ("m3A", "DISCONTENT_BONUS_3A"),
        ("m4A", "DISCONTENT_BONUS_4A"),
    ]
    form_algo_setting = forms.SettingAlgoClubQPage(
        **{attr: GlobalSetting.get_value(key) for attr, key in discontent_bonus},
        promo=GlobalSetting.get_value("PROMO_1A"),
    )

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
            for attr_name, setting_key in discontent_bonus:
                GlobalSetting.get(setting_key).value = form_algo_setting[attr_name].data
            GlobalSetting.get("PROMO_1A").value = form_algo_setting.promo.data

            db.session.commit()
            flask.flash(_("Mis à jour."), "success")

        launch = form_algo_setting["launch_algorithm"].data
        if launch:

            promo_1A = GlobalSetting.get_value("PROMO_1A")
            bonus = [GlobalSetting.get_value(setting_key) for _attr, setting_key in discontent_bonus]

            save_results = form_algo_setting["save_attribution"].data
            corruption = form_algo_setting["corruption"].data

            # Place attribution

            voeux_update, pceens = attribution(voeux, pceens, spectacles, promo_1A, bonus, corruption)
            #voeux = db.session.scalars(db.select(ClubQVoeu).filter_by(_season_id=season_id).order_by(ClubQVoeu.priorite)).all()
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
                flask.flash(_("Algorithme exécuté et résultats sauvegardés."), "success")
            else:
                # Rollback any changes proposed to the database
                db.session.rollback()
                flask.flash(_("Algorithme exécuté."), "success")

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

    season_id = _active_season_id()
    saison = db.get_or_404(ClubQSeason, season_id)
    pceens = _club_q_pceens_query().filter(_has_voeu_in_season(season_id))

    voeux = db.select(ClubQVoeu).filter_by(_season_id=season_id).filter(ClubQVoeu.places_attribuees > 0)
    spectacles_stmt = db.select(ClubQSpectacle).filter_by(_season_id=season_id).order_by(ClubQSpectacle.date)
    salles_stmt = db.select(ClubQSalle).order_by(ClubQSalle.nom)

    can_edit = context.has_permission(PermissionType.write, PermissionScope.club_q)
    form_mail = forms.Mail()


    if form_mail.validate_on_submit() and can_edit:

        #Informations from the Mail form
        date_payement = form_mail["date_payement"].data
        date_SAV = form_mail["date_SAV"].data
        link_SAV = form_mail["link_SAV"].data

        #If there is a problem, send email from the x-th email
        threshold = form_mail["threshold"].data
        x = 0
        
        subject = f"Attribution Club Q {saison.nom}"
        for pceen in db.session.scalars(pceens).all():
          
            #Sending email according to the x-th one
            if threshold != 0 and x < threshold:
                x+=1
                continue
            
            voeux_pceen = db.session.scalars(voeux.filter_by(_pceen_id=pceen.id)).all()
            spectacles_list = []
            
            for voeu in voeux_pceen:
                spectacle = db.session.scalars(spectacles_stmt.filter_by(id=voeu._spectacle_id)).one()
                salle = db.session.scalars(salles_stmt.filter_by(id=spectacle._salle_id)).one()
                spectacles_list.append([f"{spectacle.nom} - {spectacle.date} - {salle.nom} : {voeu.places_attribuees} places attribuée(s), pour {spectacle.unit_price*voeu.places_attribuees} €"])

            if spectacles_list == []:
                spectacles_list = None

            html_body = flask.render_template(
                "club_q/mails/reservation.html", saison=saison, pceen=pceen, date_payement=date_payement, date_SAV=date_SAV, link_SAV=link_SAV, spectacles_list=spectacles_list
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
    season_id = _active_season_id()
    seasons = _all_seasons()

    can_edit = context.has_permission(PermissionType.write, PermissionScope.club_q)

    form_setting = forms.SettingClubQPage(
        visibility=bool(GlobalSetting.get_value("ACCESS_CLUB_Q")),
        saison=season_id,
    )
    form_setting.saison.choices = [(s.id, s.nom) for s in seasons]

    # Cheking if something changed in forms
    if form_setting.validate_on_submit() and can_edit:
        GlobalSetting.get("ACCESS_CLUB_Q").value = 1 if form_setting.visibility.data else 0
        GlobalSetting.get("SEASON_NUMBER_CLUB_Q").value = form_setting.saison.data

        db.session.commit()
        flask.flash(_("Mis à jour."), "success")

    return flask.render_template("club_q/options.html", view="options", form_setting=form_setting, user=context.g.pceen)


@bp.route("/pceens/<int:id>", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def pceen_id(id: int):
    """Sum up of informations about users regarding Club Q"""

    # Get user
    pceen: PCeen | None = db.session.scalars(db.select(PCeen).filter_by(id=id)).one_or_none()
    if not pceen or (
        not context.g.pceen.has_permission(PermissionType.all, PermissionScope.club_q) and context.g.pceen != pceen
    ):
        flask.abort(404)

    season_id = _parse_season_id(flask.request.args.get("season_id"))
    saison = db.get_or_404(ClubQSeason, season_id)
    saisons = _all_seasons()

    can_edit = context.has_permission(PermissionType.write, PermissionScope.club_q)
    show_attribution = bool(saison.attributions_visible or can_edit)

    user = context.g.pceen
    view = "pceen_reservations" if user == pceen else "pceen_view"

    form_add_voeu = None
    form_edit_voeu = None
    if can_edit:
        spectacles = _season_spectacles(season_id)
        form_add_voeu, form_edit_voeu, resp = _voeu_forms(
            spectacles,
            spectacles[0] if spectacles else None,
            pceen,
            season_id,
            flask.url_for("club_q.pceen_id", id=id, season_id=season_id),
        )
        if resp is not None:
            return resp

    voeux_list = db.session.scalars(
        db.select(ClubQVoeu)
        .options(sqlalchemy.orm.selectinload(ClubQVoeu.spectacle))
        .filter_by(_season_id=season_id, _pceen_id=pceen.id)
        .order_by(ClubQVoeu.priorite)
    ).all()
    obtained_voeux = sorted(_split_voeux_by_attribution(voeux_list)[0], key=lambda v: v.spectacle.date)
    total_places_demandees = voeux_sum_demandees(voeux_list)
    total_places_attribuees = voeux_sum_attribuees(voeux_list)
    prix_total = voeux_total_price(voeux_list)
    is_paid = ClubQPayment.is_paid(pceen.id, season_id)
    montant_a_payer = Decimal("0.00") if is_paid else prix_total

    spectacle_attrib_by_id: dict[int, int] = {}
    if can_edit and voeux_list:
        spect_ids = {v._spectacle_id for v in voeux_list}
        rows = db.session.execute(
            db.select(
                ClubQVoeu._spectacle_id,
                sqlalchemy.func.coalesce(sqlalchemy.func.sum(ClubQVoeu.places_attribuees), 0),
            )
            .where(ClubQVoeu._season_id == season_id, ClubQVoeu._spectacle_id.in_(spect_ids))
            .group_by(ClubQVoeu._spectacle_id)
        ).all()
        spectacle_attrib_by_id = {sid: int(total) for sid, total in rows}

    return flask.render_template(
        "club_q/id/pceen.html",
        title=_("Récapitulatif - ") + pceen.full_name,
        view=view,
        voeux=voeux_list,
        obtained_voeux=obtained_voeux,
        spectacle_attrib_by_id=spectacle_attrib_by_id,
        season_id=season_id,
        saisons=saisons,
        pceen=pceen,
        user=context.g.pceen,
        total_places_demandees=total_places_demandees,
        total_places_attribuees=total_places_attribuees,
        prix_total=prix_total,
        montant_a_payer=montant_a_payer,
        is_paid=is_paid,
        form_add_voeu=form_add_voeu,
        form_edit_voeu=form_edit_voeu,
        nb_voeux=len(voeux_list),
        show_attribution=show_attribution,
    )


@bp.route("/pceens/<int:id>/generate_pdf", methods=["GET"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def user_generate_pdf(id: int):
    """Receipt generation for Club Q as a PDF for the user"""
    # Get user
    pceen: PCeen | None = db.session.scalars(db.select(PCeen).filter_by(id=id)).one_or_none()
    if not pceen or (
        not context.g.pceen.has_permission(PermissionType.all, PermissionScope.club_q) and context.g.pceen != pceen
    ):
        flask.abort(404)

    season_id = _parse_season_id(flask.request.args.get("season_id"))
    season = db.get_or_404(ClubQSeason, season_id)
    if not season.attributions_visible and not context.has_permission(PermissionType.write, PermissionScope.club_q):
        flask.abort(403)

    voeux = (
        db.select(ClubQVoeu)
        .options(sqlalchemy.orm.selectinload(ClubQVoeu.spectacle))
        .filter_by(_season_id=season_id, _pceen_id=pceen.id)
        .filter(ClubQVoeu.places_attribuees != 0)
        .order_by(ClubQVoeu.priorite)
    )
    is_paid = ClubQPayment.is_paid(pceen.id, season_id)
    # Return the PDF as a response to the user
    response = flask.make_response(pdf_client(pceen, season, voeux, is_paid=is_paid).read())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename=club_q_{pceen.username}.pdf"
    return response


@bp.route("/spectacles/<int:id>", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def spectacle_id(id: int):
    """Sum up of informations concerning the club Q spectacle of the given id"""
    # Get spectacle
    spectacle = db.get_or_404(ClubQSpectacle, id)

    season_id = spectacle._season_id
    can_edit = context.has_permission(PermissionType.write, PermissionScope.club_q)
    can_view_lists = can_edit or _can_respo_view(context.g.pceen.id, spectacle._salle_id, spectacle.season)

    voeux = (
        db.session.scalars(
            db.select(ClubQVoeu)
            .options(sqlalchemy.orm.selectinload(ClubQVoeu.pceen))
            .filter_by(_season_id=season_id, _spectacle_id=spectacle.id)
            .order_by(ClubQVoeu.id)
        ).all()
        if can_view_lists
        else []
    )

    form_add_voeu = None
    form_edit_voeu = None
    if can_edit:
        form_add_voeu, form_edit_voeu, resp = _voeu_forms(
            _season_spectacles(season_id),
            spectacle,
            None,
            season_id,
            flask.url_for("club_q.spectacle_id", id=id, season_id=season_id),
        )
        if resp is not None:
            return resp

    attribues, attente = _split_voeux_by_attribution(voeux)
    voeux_attribues = sorted(attribues, key=lambda v: pceen_sort_key(v.pceen))
    voeux_attente = sorted(attente, key=lambda v: (-(v.pceen.discontent or 0), v.priorite))
    paid_pceen_ids = ClubQPayment.paid_pceen_ids(season_id) if voeux_attribues else set()
    # The full (editable) vœux list is admin-only; Respo salle only get the two lists above
    admin_voeux = voeux if can_edit else []

    return flask.render_template(
        "club_q/id/spectacle.html",
        title=spectacle.nom,
        season_id=season_id,
        spectacle=spectacle,
        voeux=admin_voeux,
        voeux_attribues=voeux_attribues,
        voeux_attente=voeux_attente,
        paid_pceen_ids=paid_pceen_ids,
        sum_places_demandees=voeux_sum_demandees(voeux),
        sum_places_attribuees=voeux_sum_attribuees(voeux),
        can_view_lists=can_view_lists,
        user=context.g.pceen,
        view="spectacles",
        form_add_voeu=form_add_voeu,
        form_edit_voeu=form_edit_voeu,
        nb_total_voeux=len(admin_voeux),
    )


@bp.route("/spectacles/<int:id>/generate_pdf", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def spect_generate_pdf(id: int):
    """Sum up of informations concerning the club Q spectacle of the given id"""
    # Get spectacle
    spectacle = db.get_or_404(ClubQSpectacle, id)
    if not context.g.pceen.has_permission(PermissionType.all, PermissionScope.club_q):
        flask.abort(404)

    season = spectacle.season
    voeux_attrib, voeux_nan_attrib = _spectacle_voeux_split(spectacle)

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
    spectacle = db.get_or_404(ClubQSpectacle, id)
    if not context.g.pceen.has_permission(PermissionType.write, PermissionScope.club_q):
        flask.abort(404)

    season = spectacle.season
    voeux_attrib, voeux_nan_attrib = _spectacle_voeux_split(spectacle)

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

    salle = db.get_or_404(ClubQSalle, id)

    season_id = _parse_season_id(flask.request.args.get("season_id"))

    saisons = _all_seasons()
    spectacles = [spect for spect in _season_spectacles(season_id) if spect._salle_id == salle.id]

    spect_sum_places = spectacles_sum_places(spectacles)
    spect_sum_places_demandees = spectacles_sum_places_demandees(spectacles)
    spect_sum_places_attribuees = spectacles_sum_places_attribuees(spectacles)

    can_edit = context.has_permission(PermissionType.write, PermissionScope.club_q)
    respo_season = db.session.get(ClubQSeason, season_id)
    current_respos = ClubQSalleRespo.get_for_salle(salle.id, season_id) if can_edit else []
    eligible_pceens = _club_q_pceens() if can_edit else []

    form_spectacle = None
    if can_edit:
        salles = db.session.scalars(db.select(ClubQSalle).order_by(ClubQSalle.nom)).all()
        redirect = flask.url_for("club_q.salle_id", id=id, season_id=season_id)
        form_spectacle, resp = spectacle_form(salles, salle, season_id, redirect, can_edit)
        if resp is not None:
            return resp

    return flask.render_template(
        "club_q/id/salle.html",
        title=_(salle.nom),
        user=context.g.pceen,
        view="salle",
        salle=salle,
        saisons=saisons,
        respo_season=respo_season,
        current_respos=current_respos,
        eligible_pceens=eligible_pceens,
        redirect="club_q.salle_id",
        season_id=season_id,
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

    brochures = db.session.scalars(
        db.select(ClubQBrochure).join(ClubQBrochure.season).order_by(*ClubQSeason.default_order())
    ).all()
    saisons = _all_seasons()

    form = forms.Brochure(season_id=_active_season_id())
    form.season_id.choices = [(saison.id, saison.nom) for saison in saisons]

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

                flask.flash(_("Plaquette ajoutée."), "success")
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

    brochure = db.session.scalars(db.select(ClubQBrochure).filter_by(id=id)).one_or_none()
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

    brochure = db.session.scalars(db.select(ClubQBrochure).filter_by(id=id)).one_or_none()
    if brochure is None:
        flask.abort(404)

    path = os.path.join(flask.current_app.config["CLUB_Q_BASE_PATH"], "plaquettes", str(brochure.id) + ".pdf")

    db.session.delete(brochure)
    db.session.commit()

    os.remove(path)

    flask.flash(_("Plaquette supprimée."), "success")
    return flask.redirect(flask.url_for("club_q.brochures"))


@bp.route("/edit_text", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def edit_text():

    content = flask.request.form.get("content")  # Retrieve the content from the POST request
    path = os.path.join(flask.current_app.config["CLUB_Q_BASE_PATH"], "introduction.html")
    with open(path, "w") as file:
        file.write(content)

    flask.flash(_("Introduction mise à jour."), "success")
    return flask.redirect(flask.url_for("club_q.main"))



@bp.route("/saisons/attrib_visible/<int:id>", methods=["GET", "POST"])
@context.permission_only(PermissionType.write, PermissionScope.club_q)
def visible(id):
    """
    Change the boolean variable to show/hide attributions for all wishes in a Club Q season
    """
    season = db.get_or_404(ClubQSeason, id)
    season.attributions_visible = False if season.attributions_visible else True
    db.session.commit()
    
    return flask.redirect(flask.url_for("club_q.saisons"))