import reportlab as rl
from reportlab.lib import units, pagesizes, styles
from reportlab.pdfgen import canvas
from reportlab.platypus import flowables
import io
import os
import openpyxl


cm = rl.lib.units.cm


def pdf_client(pceen, season, voeux):
    # Create a PDF buffer
    buffer = io.BytesIO()

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
        for voeu in voeux
    ]

    specs.append("-" * 158)
    specs.append(f"Total à payer : {pceen.total_price} €.")

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
    sheet["E4"] = sum((voeu.places_attribuees or 0) for voeu in voeux_attrib)

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

