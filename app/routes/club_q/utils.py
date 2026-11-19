import reportlab as rl
from reportlab.lib import units, pagesizes, styles
from reportlab.pdfgen import canvas
from reportlab.platypus import flowables
import io
import os
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
import openpyxl
import zipfile

from app import db
from app.models import ClubQSpectacle, ClubQVoeu, PCeen, ClubQSeason, ClubQSalle
import sqlalchemy
from sqlalchemy.exc import IntegrityError
import flask
from app.routes.club_q import forms
from flask_babel import _
from unidecode import unidecode
from datetime import datetime


cm = rl.lib.units.cm


def pceen_sort_key(pceen: PCeen) -> tuple[str, str]:
    """Case and accent-insensitive (last name, first name) sort key."""
    return (unidecode(pceen.nom or "").lower(), unidecode(pceen.prenom or "").lower())


def voeux_sum_attribuees(voeux_list) -> int:
    """Total number of attributed places for an iterable of ClubQVoeu objects."""
    return sum((voeu.places_attribuees or 0) for voeu in voeux_list)


def voeux_sum_demandees(voeux_list) -> int:
    """Total number of requested places for an iterable of ClubQVoeu objects."""
    return sum((voeu.places_demandees or 0) for voeu in voeux_list)


def voeux_total_price(voeux_list) -> Decimal:
    """Total cost of an iterable of ClubQVoeu objects (spectacle must be loaded)."""
    total = sum(
        (Decimal(voeu.places_attribuees or 0) * Decimal(str(voeu.spectacle.unit_price)) for voeu in voeux_list),
        Decimal(0),
    )
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def group_by(items, key: str) -> dict:
    """Group an iterable of objects into a dict of lists keyed by the given attribute."""
    grouped = defaultdict(list)
    for item in items:
        grouped[getattr(item, key)].append(item)
    return grouped


def count_by(group_column, *filters) -> dict[int, int]:
    """Return {group_column value: row count} in a single GROUP BY query."""
    rows = db.session.execute(
        db.select(group_column, sqlalchemy.func.count()).where(*filters).group_by(group_column)
    ).all()
    return {key: count for key, count in rows}


def pdf_client(pceen, season, voeux, is_paid=False):
    # Create a PDF buffer
    buffer = io.BytesIO()

    # Liste des voeux
    voeux_list = db.session.scalars(voeux).all()

    # Code de génération de facture du Club Q originalement par Loïc Simon - Adapté aux besoin de pem
    canvas = rl.pdfgen.canvas.Canvas(buffer, pagesize=rl.lib.pagesizes.A4)
    canvas.setAuthor("Club Q ESPCI Paris - PSL")
    canvas.setTitle(f"Compte-rendu {pceen.nom}")
    canvas.setSubject(f"Saison {season.nom}")

    styles = rl.lib.styles.getSampleStyleSheet()
    styleN = styles["Normal"]
    canvas.setFont("Times-Bold", 18)

    descr = [
        f"Nom : <b>{pceen.nom}</b>",
        f"Prénom : <b>{pceen.prenom}</b>",
        f"Promo : <b>{pceen.promo}</b>",
        f"Adresse e-mail : <b>{pceen.email}</b>",
    ]

    specs = [
        f"{voeu.spectacle.nom} - {voeu.places_attribuees} place(s) -\t\t {voeu.spectacle.unit_price} € /place"
        for voeu in voeux_list
    ]

    total_due = voeux_total_price(voeux_list)
    specs.append("-" * 158)
    if is_paid and total_due > 0:
        specs.append(f"Total : {total_due:.2f} € — Payé (reste à payer : 0.00 €).")
    else:
        specs.append(f"Total à payer : {total_due:.2f} €.")

    # Conversion en objets reportlab
    blocs_descr = []
    for txt in descr:
        blocs_descr.append(rl.platypus.Paragraph(txt, styleN))
        blocs_descr.append(rl.platypus.Spacer(1, 0.2 * cm))

    blocs_specs = []
    for txt in specs:
        blocs_specs.append(rl.platypus.Paragraph(txt, styleN))
        blocs_specs.append(rl.platypus.Spacer(1, 0.2 * cm))

    # IMPRESSION
    canvas.setFont("Times-Bold", 18)
    canvas.drawString(1 * cm, 28 * cm, f"Compte-rendu Club Q")

    canvas.setFont("Times-Bold", 12)
    canvas.drawString(1 * cm, 27.2 * cm, f"Saison {season.nom}")

    dX, dY = canvas.drawImage(
        os.path.join("app", "static", "img", "espci.png"),
        14 * cm,
        27.22 * cm,
        width=5.63 * cm,
        height=1.2 * cm,
        mask="auto",
    )
    dX, dY = canvas.drawImage(
        os.path.join("app", "static", "img", "club_q.png"),
        11.5 * cm,
        26.8 * cm,
        width=2 * cm,
        height=2 * cm,
        mask="auto",
    )

    frame_descr = rl.platypus.Frame(1 * cm, 23.5 * cm, 19 * cm, 3 * cm, showBoundary=True)
    frame_descr.addFromList(blocs_descr, canvas)

    frame_specs = rl.platypus.Frame(1 * cm, 1 * cm, 19 * cm, 22 * cm, showBoundary=True)
    frame_specs.addFromList(blocs_specs, canvas)

    canvas.showPage()

    # SAUVEGARDE
    canvas.save()

    # Reset the buffer's file pointer to the beginning
    buffer.seek(0)

    return buffer


def pdf_spectacle(spec, season, voeux_attrib, voeux_nan_attrib):
    # Create a PDF buffer
    buffer = io.BytesIO()

    # Code de génération de résumé d'un spectacle du Club Q originalement par Loïc Simon - Adapté aux besoin de pem
    canvas = rl.pdfgen.canvas.Canvas(buffer, pagesize=rl.lib.pagesizes.A4)
    styles = rl.lib.styles.getSampleStyleSheet()
    styleN = styles["Normal"]
    canvas.setFont("Times-Bold", 18)

    descr = [
        f"Titre : <b>{spec.nom}</b> ({spec.categorie or 'catégorie inconnue'})",
        f"Salle : <b>{spec.salle}</b>, {spec.salle.adresse or 'adresse inconnue'}",
        f"Date : <b>{spec.date or '(heure inconnue)'}</b>",
        f"Nombre de places : <b>{spec.nb_tickets}</b> – Demandées : <b>{spec.sum_places_demandees}</b> – Attribuées : <b>{spec.sum_places_attribuees}</b>",
    ]

    eleves = [
        f"{attrib.pceen.full_name}, {attrib.pceen.promo}, {attrib.pceen.email} - {attrib.places_attribuees} place(s)"
        for attrib in voeux_attrib
    ]

    # Conversion en objets reportlab

    blocs_descr = []
    for txt in descr:
        blocs_descr.append(rl.platypus.Paragraph(txt, styleN))
        blocs_descr.append(rl.platypus.Spacer(1, 0.2 * cm))

    blocs_eleves = []
    for txt in eleves:
        blocs_eleves.append(rl.platypus.Paragraph(txt, styleN))
        blocs_eleves.append(rl.platypus.Spacer(1, 0.2 * cm))

    # IMPRESSION PAGE 1
    canvas.setFont("Times-Bold", 18)
    canvas.drawString(1 * cm, 28 * cm, f"Compte-rendu {spec.nom}")

    canvas.setFont("Times-Bold", 12)
    canvas.drawString(1 * cm, 27.2 * cm, f"Saison {season.nom}")

    dX, dY = canvas.drawImage(
        os.path.join("app", "static", "img", "espci.png"),
        14 * cm,
        27.22 * cm,
        width=5.63 * cm,
        height=1.2 * cm,
        mask="auto",
    )
    dX, dY = canvas.drawImage(
        os.path.join("app", "static", "img", "club_q.png"),
        11.5 * cm,
        26.8 * cm,
        width=2 * cm,
        height=2 * cm,
        mask="auto",
    )

    frame_descr = rl.platypus.Frame(1 * cm, 23.5 * cm, 19 * cm, 3 * cm, showBoundary=1)
    frame_descr.addFromList(blocs_descr, canvas)

    frame_eleves = rl.platypus.Frame(1 * cm, 1 * cm, 19 * cm, 22 * cm, showBoundary=1)
    frame_eleves.addFromList(blocs_eleves, canvas)

    canvas.showPage()

    # PAGE 2 (liste d'attente)

    voeux = [voeu for voeu in voeux_nan_attrib]

    if voeux:
        voeux.sort(key=lambda a: a.pceen.discontent or 0, reverse=True)

        voeux_txt = ["Liste d'attente :"]
        for voeu in voeux:
            voeux_txt.append(
                f"M: {round(voeu.pceen.discontent or 0, 2)} - {voeu.pceen.full_name} - {voeu.places_demandees} place(s) ({voeu.places_minimum} min) - Voeu n°{voeu.priorite}"
            )

    else:
        voeux_txt = ["Pas de liste d'attente."]

    blocs_descr = []  # Détruits à la précédente impression...
    for txt in descr:
        blocs_descr.append(rl.platypus.Paragraph(txt, styleN))
        blocs_descr.append(rl.platypus.Spacer(1, 0.2 * cm))

    blocs_voeux = []
    for txt in voeux_txt:
        blocs_voeux.append(rl.platypus.Paragraph(txt, styleN))
        blocs_voeux.append(rl.platypus.Spacer(1, 0.2 * cm))

    # IMPRESSION PAGE 2
    canvas.setFont("Times-Bold", 18)
    canvas.drawString(1 * cm, 28 * cm, f"Liste d'attente {spec.nom}")

    canvas.setFont("Times-Bold", 12)
    canvas.drawString(1 * cm, 27.2 * cm, f"Saison {season.nom}")

    dX, dY = canvas.drawImage(
        os.path.join("app", "static", "img", "espci.png"),
        14 * cm,
        27.22 * cm,
        width=5.63 * cm,
        height=1.2 * cm,
        mask="auto",
    )
    dX, dY = canvas.drawImage(
        os.path.join("app", "static", "img", "club_q.png"),
        11.5 * cm,
        26.8 * cm,
        width=2 * cm,
        height=2 * cm,
        mask="auto",
    )

    frame_descr = rl.platypus.Frame(1 * cm, 23.5 * cm, 19 * cm, 3 * cm, showBoundary=1)
    frame_descr.addFromList(blocs_descr, canvas)

    frame_eleves = rl.platypus.Frame(1 * cm, 1 * cm, 19 * cm, 22 * cm, showBoundary=1)
    frame_eleves.addFromList(blocs_voeux, canvas)

    canvas.showPage()

    # SAUVEGARDE

    canvas.save()

    # Reset the buffer's file pointer to the beginning
    buffer.seek(0)

    return buffer


def excel_spectacle(spec, season, voeux_attrib, voeux_nan_attrib):
    # Code de génération de résumé de spectacle du Club Q originalement par Loïc Simon - Adapté aux besoin de pem
    # Code assez (très) moche, attention - il y a moyen de faire ça beaucoup mieux, mais bon...
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Élèves"

    sheet["A1"] = f"Club Q – Récapitulatif spectacle : {spec.nom}"
    sheet["A1"].font = openpyxl.styles.Font(bold=True)

    sheet["A2"] = "Saison :"
    sheet["B2"] = season.nom
    sheet["D2"] = "Prix du billet :"
    sheet["E2"] = spec.unit_price
    sheet["E2"].number_format = "#,##0.00 €_-"

    sheet["A3"] = "Date et heure :"
    sheet["B3"] = spec.date
    sheet["B3"].number_format = "dd/mm/yy hh:mm"
    sheet["D3"] = "Salle :"
    sheet["E3"] = spec.salle.nom

    sheet["A4"] = "Places proposées :"
    sheet["B4"] = spec.nb_tickets
    sheet["D4"] = "Places vendues :"
    sheet["E4"] = voeux_sum_attribuees(voeux_attrib)

    sheet["A6"] = "NOM"
    sheet["B6"] = "Prénom"
    sheet["C6"] = "Promo/autre"
    sheet["D6"] = "Adresse mail"
    sheet["E6"] = "Places"
    sheet["F6"] = "Montant"

    npa = 0
    tot = 0
    for i, voeu in enumerate(sorted(voeux_attrib, key=lambda v: v.pceen.full_name)):
        pceen = voeu.pceen
        sheet.cell(row=7 + i, column=1).value = pceen.nom
        sheet.cell(row=7 + i, column=2).value = pceen.prenom
        sheet.cell(row=7 + i, column=3).value = pceen.promo

        sheet.cell(row=7 + i, column=4).value = pceen.email
        if pceen.email and "@" in pceen.email:
            sheet.cell(row=7 + i, column=4).hyperlink = f"mailto:{pceen.email}"
            sheet.cell(row=7 + i, column=4).style = "Hyperlink"

        placesattr = voeu.places_attribuees or 0
        sheet.cell(row=7 + i, column=5).value = placesattr
        npa += placesattr

        apayer = placesattr * spec.unit_price
        sheet.cell(row=7 + i, column=6).value = apayer
        sheet.cell(row=7 + i, column=6).number_format = "#,##0.00 €_-"
        tot += apayer

    tab = openpyxl.worksheet.table.Table(displayName="Données", ref=f"A6:F{7 + i}")

    style = openpyxl.worksheet.table.TableStyleInfo(
        name="TableStyleLight1",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False,
    )
    tab.tableStyleInfo = style
    sheet.add_table(tab)

    sheet.cell(row=7 + i + 2, column=1).value = "Total"
    sheet.cell(row=7 + i + 2, column=1).font = openpyxl.styles.Font(bold=True)

    sheet.cell(row=7 + i + 2, column=5).value = npa
    sheet.cell(row=7 + i + 2, column=5).font = openpyxl.styles.Font(bold=True)

    sheet.cell(row=7 + i + 2, column=6).value = tot
    sheet.cell(row=7 + i + 2, column=6).font = openpyxl.styles.Font(bold=True)
    sheet.cell(row=7 + i + 2, column=6).number_format = "#,##0.00 €_-"

    sheet.column_dimensions["A"].width = 20
    sheet.column_dimensions["B"].width = 20
    sheet.column_dimensions["C"].width = 14
    sheet.column_dimensions["D"].width = 35
    sheet.column_dimensions["E"].width = 12
    sheet.column_dimensions["F"].width = 14

    # Save the Excel workbook to a BytesIO buffer
    excel_data = io.BytesIO()
    workbook.save(excel_data)

    return excel_data


def export_pdf_spectacles(spectacles, season, voeux_attrib_list, voeux_nan_attrib_list):

    # Create an in-memory zip file
    zip_buffer = io.BytesIO()

    # Create a ZipFile object
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add PDF files to the zip archive
        i = 0
        for spectacle in spectacles:  # Replace with your logic to get PDF files
            pdf_data = pdf_spectacle(spectacle, season, voeux_attrib_list[i], voeux_nan_attrib_list[i]).read()
            zipf.writestr(f"{spectacle.nom}.pdf", pdf_data)
            i += 1

    # Move the zip file's pointer to the beginning
    zip_buffer.seek(0)

    return zip_buffer


def export_excel_spectacles(spectacles, season, voeux_attrib_list, voeux_nan_attrib_list):

    # Create an in-memory zip file
    zip_buffer = io.BytesIO()

    # Create a ZipFile object
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add excel files to the zip archive
        i = 0
        for spectacle in spectacles:  # Replace with your logic to get excel files
            excel_data = excel_spectacle(spectacle, season, voeux_attrib_list[i], voeux_nan_attrib_list[i]).getvalue()
            zipf.writestr(f"{spectacle.nom}.xlsx", excel_data)
            i += 1

    # Move the zip file's pointer to the beginning
    zip_buffer.seek(0)

    return zip_buffer


def exporter_excel_prix(saison, pceens, spectacles, voeux, paid_pceen_ids=None):
    # Code de génération de résumé des payements au Club Q originalement par Loïc Simon - Adapté aux besoin de pem
    paid_pceen_ids = paid_pceen_ids or set()
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Récapitulatif"

    voeux_list = db.session.scalars(
        voeux.options(sqlalchemy.orm.selectinload(ClubQVoeu.spectacle))
    ).all()
    voeux_by_pceen = group_by(voeux_list, "_pceen_id")

    sheet["A1"] = f"Club Q – Récapitulatif saison {saison.nom}"
    sheet["A1"].font = openpyxl.styles.Font(bold=True)

    sheet["A2"] = "Début :"
    sheet["B2"] = saison.debut
    sheet["B2"].number_format = "dd/mm/yyyy"
    sheet["D2"] = "Fin :"
    sheet["E2"] = saison.fin
    sheet["E2"].number_format = "dd/mm/yyyy"

    sheet["A3"] = "Spectacles :"
    sheet["B3"] = len(spectacles)
    sheet["D3"] = "Inscrits :"
    sheet["E3"] = len(pceens)

    sheet["A4"] = "Places proposées :"
    sheet["B4"] = sum((spec.nb_tickets or 0) for spec in spectacles)
    sheet["D4"] = "Places vendues :"
    sheet["E4"] = voeux_sum_attribuees(voeux_list)

    sheet["A6"] = "NOM"
    sheet["B6"] = "Prénom"
    sheet["C6"] = "Promo/autre"
    sheet["D6"] = "Adresse mail"
    sheet["E6"] = "Places"
    sheet["F6"] = "Somme due"
    sheet["G6"] = "Payé ?"

    npa = 0
    tot = Decimal("0.00")
    sorted_pceens = sorted(pceens, key=pceen_sort_key)
    for i, client in enumerate(sorted_pceens):
        sheet.cell(row=7 + i, column=1).value = client.nom.upper()
        sheet.cell(row=7 + i, column=2).value = client.prenom.title()
        sheet.cell(row=7 + i, column=3).value = client.promo or ""

        sheet.cell(row=7 + i, column=4).value = client.email
        if client.email and "@" in client.email:
            sheet.cell(row=7 + i, column=4).hyperlink = f"mailto:{client.email}"
            sheet.cell(row=7 + i, column=4).style = "Hyperlink"

        client_voeux = voeux_by_pceen.get(client.id, [])
        placesattr = voeux_sum_attribuees(client_voeux)
        sheet.cell(row=7 + i, column=5).value = placesattr
        npa += placesattr
        apayer = voeux_total_price(client_voeux)
        sheet.cell(row=7 + i, column=6).value = apayer
        sheet.cell(row=7 + i, column=6).number_format = "#,##0.00 €_-"
        sheet.cell(row=7 + i, column=7).value = "Oui" if client.id in paid_pceen_ids else ("Non" if apayer > 0 else "")
        tot += apayer

    last_row = 6 + len(sorted_pceens)
    if sorted_pceens:
        tab = openpyxl.worksheet.table.Table(displayName="Données", ref=f"A6:G{last_row}")

        style = openpyxl.worksheet.table.TableStyleInfo(
            name="TableStyleLight1",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False,
        )
        tab.tableStyleInfo = style
        sheet.add_table(tab)

    total_row = last_row + 2
    sheet.cell(row=total_row, column=1).value = "Total"
    sheet.cell(row=total_row, column=1).font = openpyxl.styles.Font(bold=True)

    sheet.cell(row=total_row, column=5).value = npa
    sheet.cell(row=total_row, column=5).font = openpyxl.styles.Font(bold=True)

    sheet.cell(row=total_row, column=6).value = tot
    sheet.cell(row=total_row, column=6).font = openpyxl.styles.Font(bold=True)
    sheet.cell(row=total_row, column=6).number_format = "#,##0.00 €_-"

    sheet.column_dimensions["A"].width = 20
    sheet.column_dimensions["B"].width = 20
    sheet.column_dimensions["C"].width = 14
    sheet.column_dimensions["D"].width = 35
    sheet.column_dimensions["E"].width = 12
    sheet.column_dimensions["F"].width = 14
    sheet.column_dimensions["G"].width = 12

    # Save the Excel workbook to a BytesIO buffer
    excel_data = io.BytesIO()
    workbook.save(excel_data)

    return excel_data


def spectacles_sum_places_attribuees(spectacles) -> int:
    """Gives the number of given places for a saison of Club Q"""
    return sum(spectacle.sum_places_attribuees for spectacle in spectacles)


def spectacles_sum_places_demandees(spectacles) -> int:
    """Gives the number of wanted places for a saison of Club Q"""
    return sum(spectacle.sum_places_demandees for spectacle in spectacles)


def spectacles_sum_places(spectacles) -> int:
    """Gives the total numbers of tickets for the given saison of Club Q"""
    return sum(spectacle.nb_tickets for spectacle in spectacles)


def voeu_form(spectacles, spectacle, pceens, pceen, season_id, redirect, can_edit):
    """Initialize and process the add/edit vœu admin forms."""
    add_defaults = {}
    if spectacle is not None:
        add_defaults["spectacle_add"] = spectacle.id
    if pceen is not None:
        add_defaults["pceen_add"] = pceen.id

    form_add_voeu = forms.AddVoeu(**add_defaults)
    form_add_voeu.spectacle_add.choices = [(spect.id, spect.nom) for spect in spectacles]
    form_add_voeu.pceen_add.choices = [(pceen_.id, pceen_.full_name) for pceen_ in pceens]
    form_edit_voeu = forms.EditVoeu()

    # If a form is validated
    if form_add_voeu.is_submitted() and can_edit:
        submit = form_add_voeu["submit_add"].data
        if submit and form_add_voeu.validate():
            voeu = ClubQVoeu(
                _spectacle_id=form_add_voeu["spectacle_add"].data,
                _pceen_id=form_add_voeu["pceen_add"].data,
                _season_id=season_id,
                priorite=form_add_voeu["priorite_add"].data,
                places_demandees=form_add_voeu["places_demandees_add"].data,
                places_minimum=form_add_voeu["places_minimum_add"].data or 0,
                places_attribuees=form_add_voeu["places_attribuees_add"].data,
            )
            db.session.add(voeu)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flask.flash(_("Ce PCéen a déjà un vœu pour ce spectacle."), "danger")
                return form_add_voeu, form_edit_voeu, flask.redirect(redirect)
            flask.flash(_("Voeu ajouté."), "success")
            return form_add_voeu, form_edit_voeu, flask.redirect(redirect)

    if form_edit_voeu.is_submitted() and can_edit:
        delete = form_edit_voeu["delete_edit"].data
        if delete:
            voeu = db.session.scalars(db.select(ClubQVoeu).filter_by(id=form_edit_voeu["id_edit"].data)).one()
            db.session.delete(voeu)

            db.session.commit()
            flask.flash(_("Voeu supprimé."), "success")
            return form_add_voeu, form_edit_voeu, flask.redirect(redirect)

        if form_edit_voeu.validate():
            voeu = db.session.scalars(db.select(ClubQVoeu).filter_by(id=form_edit_voeu["id_edit"].data)).one()

            voeu.priorite = form_edit_voeu["priorite_edit"].data
            voeu.places_demandees = form_edit_voeu["places_demandees_edit"].data
            voeu.places_minimum = form_edit_voeu["places_minimum_edit"].data or 0
            voeu.places_attribuees = form_edit_voeu["places_attribuees_edit"].data

            db.session.commit()
            flask.flash(_("Voeu édité."), "success")
            return form_add_voeu, form_edit_voeu, flask.redirect(redirect)

    return form_add_voeu, form_edit_voeu, None


def spectacle_form(salles, salle, season_id, redirect, can_edit):
    """Initialize and process the add/edit spectacle admin form."""
    defaults = {"salle_id": salle.id} if salle is not None else {}
    form_spectacle = forms.EditSpectacle(**defaults)
    form_spectacle.salle_id.choices = [(s.id, s.nom) for s in salles]

    if form_spectacle.validate_on_submit() and can_edit:
        add = form_spectacle["add"].data

        if add:
            spectacle = ClubQSpectacle()

            db.session.add(spectacle)

            spectacle.nom = form_spectacle["nom"].data
            spectacle._season_id = season_id
            spectacle._salle_id = form_spectacle["salle_id"].data
            spectacle.description = form_spectacle["description"].data
            spectacle.categorie = form_spectacle["categorie"].data
            spectacle.date = datetime.combine(form_spectacle["date"].data, form_spectacle["time"].data)
            spectacle.nb_tickets = form_spectacle["nb_tickets"].data
            spectacle.unit_price = form_spectacle["price"].data

            db.session.commit()

            flask.flash(_("Spectacle ajouté."), "success")
            return form_spectacle, flask.redirect(redirect)

        delete = form_spectacle["delete"].data
        spectacle = db.session.scalars(db.select(ClubQSpectacle).filter_by(id=form_spectacle["id"].data)).one()

        if delete:
            db.session.delete(spectacle)
            db.session.commit()

            flask.flash(_("Spectacle supprimé."), "success")
            return form_spectacle, flask.redirect(redirect)

        spectacle.nom = form_spectacle["nom"].data
        spectacle._salle_id = form_spectacle["salle_id"].data
        spectacle.description = form_spectacle["description"].data
        spectacle.categorie = form_spectacle["categorie"].data
        spectacle.date = datetime.combine(form_spectacle["date"].data, form_spectacle["time"].data)
        spectacle.nb_tickets = form_spectacle["nb_tickets"].data
        spectacle.unit_price = form_spectacle["price"].data

        db.session.commit()
        flask.flash(_("Spectacle édité."), "success")
        return form_spectacle, flask.redirect(redirect)

    return form_spectacle, None
