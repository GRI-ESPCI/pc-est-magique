"""PC est magique - Club Q Pages Routes"""

import flask
import enum
import reportlab as rl
from reportlab.lib import units, pagesizes, styles
from reportlab.pdfgen import canvas
from reportlab.platypus import flowables
import io
import os

from flask_babel import _

from app import context, db
from app.models import ClubQSeason, ClubQSpectacle, ClubQVoeu, PermissionScope, PermissionType, GlobalSetting, PCeen, Role, Permission
from app.routes.club_q import bp, forms
from app.utils import typing
from app.utils.validators import Optional

import wtforms


class ClubQViewEnum(enum.Enum):
    active = enum.auto()
    attribution = enum.auto()
    options = enum.auto()
    voeux = enum.auto()
    
@bp.route("", methods=["GET", "POST"])
@bp.route("/", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
#@context.permission_condition(lambda: bool(GlobalSetting.query.filter_by(key='ACCESS_CLUB_Q').one().value))
def main() -> typing.RouteReturn:
    """PC est magique Club Q page."""

    "If the page visibility is set at 0 in the admin parameters, don't show it"
    if not GlobalSetting.query.filter_by(key="ACCESS_CLUB_Q").one().value and not context.g.pceen.has_permission(PermissionType.all, PermissionScope.club_q):
        flask.abort(404)
    
    # Ajout dynamique de 1 form par spectacle de la saison
    season_id =  GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
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
                default=voeu.priorite if voeu else None
            ),
        )
        setattr(
            forms.ClubQForm,
            f"nb_places_{spect.id}",
            wtforms.IntegerField(
                ("Nombre places demandées"),
                render_kw={"class": "form-control"},
                validators=[Optional()],
                default=voeu.places_demandees if voeu else None
            ),
        )
        setattr(
            forms.ClubQForm,
            f"nb_places_minimum_{spect.id}",
            wtforms.IntegerField(
                ("Nombre places minimum demandées"),
                render_kw={"class": "form-control"},
                validators=[Optional()],
                default=voeu.places_minimum if voeu else None
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
        user = context.g.pceen
    )






@bp.route("/admin", methods=['GET', 'POST'])
@bp.route("/admin/<view>", methods=["GET", "POST"])
@context.permission_only(PermissionType.all, PermissionScope.club_q)
def admin(view: str = "active") -> typing.RouteReturn:
    """Administration page for Club Q."""
    
    try:
        view = ClubQViewEnum[view]
    except KeyError:
        flask.abort(404)

    season_id =  GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    seasons = ClubQSeason.query.order_by(ClubQSeason.id).all()
    spectacles = ClubQSpectacle.query.filter_by(_season_id=season_id).order_by(ClubQSpectacle.date).all()
    voeux = ClubQVoeu.query.filter_by(_season_id=season_id).order_by(ClubQVoeu.id).all()

    pceens = PCeen.query.join(PCeen.roles).join(Role.permissions).filter(Permission.type == PermissionType.read, Permission.scope == PermissionScope.club_q)

    
    #Ajout du form pour le choix de la visibilité de la page
    setattr(
            forms.SettingClubQPage,
            "visibility",
            wtforms.BooleanField(default=bool(GlobalSetting.query.filter_by(key='ACCESS_CLUB_Q').one().value)),
        )

    #Ajout du form pour le choix de la saison à afficher
    setattr(
            forms.SettingClubQPage,
            "saison",
            wtforms.SelectField(choices = [(s.id, s.nom) for s in seasons], default = season_id)
        )

    form_setting = forms.SettingClubQPage()

    if form_setting.validate_on_submit():
        if form_setting.visibility.data:
            GlobalSetting.query.filter_by(key="ACCESS_CLUB_Q").one().value = 1

        else:
            GlobalSetting.query.filter_by(key="ACCESS_CLUB_Q").one().value = 0

        
        GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value = form_setting.saison.data

        db.session.commit()
        flask.flash(_("Mis à jour."))   


    return flask.render_template(
        "club_q/admin.html",
        title=_("Administration Club Q"), form_setting=form_setting,spectacles=spectacles,voeux=voeux,
        season_id=season_id, view=view.name, pceens = pceens
    )


@bp.route("/user/<username>", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def user(username: str):
    # Get user
    pceen: PCeen | None = PCeen.query.filter_by(username=username).one_or_none()
    if not pceen or (not context.g.pceen.has_permission(PermissionType.all, PermissionScope.club_q) and context.g.pceen != pceen):
        flask.abort(404)

    season_id =  GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    spectacles = ClubQSpectacle.query.filter_by(_season_id=season_id).order_by(ClubQSpectacle.date).all()
    voeux = ClubQVoeu.query.filter_by(_season_id=season_id).filter_by(_pceen_id=pceen.id).order_by(ClubQVoeu.id).all()

    return flask.render_template(
    "club_q/pceen.html",
    title=_(f"Récapitulatif Club Q - {pceen.full_name}"), spectacles=spectacles,voeux=voeux,
    season_id=season_id, pceen = pceen
    )


@bp.route('/user/<username>/generate_pdf', methods=['GET'])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def generate_pdf(username:str):
    """Receipt generation for Club Q as a PDF for the user"""
    # Get user
    pceen: PCeen | None = PCeen.query.filter_by(username=username).one_or_none()
    if not pceen or (not context.g.pceen.has_permission(PermissionType.all, PermissionScope.club_q) and context.g.pceen != pceen):
        flask.abort(404)

    season_id =  GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    season = ClubQSeason.query.filter_by(id=season_id).order_by(ClubQSeason.id).one()
    voeux = ClubQVoeu.query.filter_by(_season_id=season_id).filter_by(_pceen_id=pceen.id).filter(ClubQVoeu.places_attribuees != 0).order_by(ClubQVoeu.id).all()

    cm = rl.lib.units.cm

    # Create a PDF buffer
    buffer = io.BytesIO()

    #Code de génération de facture du Club Q originalement par Loïc Simon - Adapté aux besoin de pem
    canvas = rl.pdfgen.canvas.Canvas(buffer, pagesize=rl.lib.pagesizes.A4)
    canvas.setAuthor("Club Q ESPCI Paris - PSL")
    canvas.setTitle(f"Compte-rendu {pceen.full_name}")
    canvas.setSubject(f"Saison {season.nom}")

    styles = rl.lib.styles.getSampleStyleSheet()
    styleN = styles["Normal"]
    canvas.setFont("Times-Bold", 18)


    descr = [
        f"Nom : <b>{pceen.nom}</b>",
        f"Prénom : <b>{pceen.prenom}</b>",
        f"Promo : <b>{pceen.promo}</b>",
        f"Adresse e-mail : <b>{pceen.email}</b>"
    ]


    specs = [f"{voeu.spectacle.nom} - {voeu.places_attribuees} place(s) -\t\t {voeu.spectacle.unit_price} € /place"
                for voeu in voeux]

    specs.append("-"*158)
    specs.append(f"Total à payer : {pceen.total_price} €.")

    
    # Conversion en objets reportlab
    blocs_descr = []
    for txt in descr:
        blocs_descr.append(rl.platypus.Paragraph(txt, styleN))
        blocs_descr.append(rl.platypus.Spacer(1, 0.2*cm))

    blocs_specs = []
    for txt in specs:
        blocs_specs.append(rl.platypus.Paragraph(txt, styleN))
        blocs_specs.append(rl.platypus.Spacer(1, 0.2*cm))


    # IMPRESSION
    canvas.setFont("Times-Bold", 18)
    canvas.drawString(1*cm, 28*cm, f"Compte-rendu Club Q")

    canvas.setFont("Times-Bold", 12)
    canvas.drawString(1*cm, 27.2*cm, f"Saison {season.nom}")

    dX, dY = canvas.drawImage(os.path.join("app", "static", "img", "espci.png"), 14*cm, 27.22*cm, width=5.63*cm, height=1.2*cm, mask="auto")
    dX, dY = canvas.drawImage(os.path.join("app", "static", "img", "club_q.png"), 11.5*cm, 26.8*cm, width=2*cm, height=2*cm, mask="auto")

    frame_descr = rl.platypus.Frame(1*cm, 23.5*cm, 19*cm, 3*cm, showBoundary=True)
    frame_descr.addFromList(blocs_descr, canvas)

    frame_specs = rl.platypus.Frame(1*cm, 1*cm, 19*cm, 22*cm, showBoundary=True)
    frame_specs.addFromList(blocs_specs, canvas)

    canvas.showPage()


    # SAUVEGARDE
    canvas.save()

    # Reset the buffer's file pointer to the beginning
    buffer.seek(0)

    # Return the PDF as a response to the user
    response = flask.make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=club_q_{pceen.username}.pdf'
    return response



@bp.route("/spectacle/<id>", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def spectacle(id: str):
    # Get user
    spectacle: ClubQSpectacle | None = ClubQSpectacle.query.filter_by(id=id).one_or_none()
    if not spectacle or not context.g.pceen.has_permission(PermissionType.all, PermissionScope.club_q):
        flask.abort(404)

    season_id =  GlobalSetting.query.filter_by(key="SEASON_NUMBER_CLUB_Q").one().value  # ID of the season to show
    voeux = ClubQVoeu.query.filter_by(_season_id=season_id).filter_by(_spectacle_id=spectacle.id).order_by(ClubQVoeu.id).all()

    return flask.render_template(
    "club_q/spectacle.html",
    title=_(f"Résumé {spectacle.nom}"),
    season_id=season_id, spectacle=spectacle, voeux=voeux
    )
