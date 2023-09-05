import logging
import os
import random

# Set up specific logging for the club q algorithm
club_q_algo_logger = logging.Logger("club_q_algo")
_club_q_algo_handler = logging.FileHandler("logs/club_q/algorithm.log")
_club_q_algo_formatter = logging.Formatter("")
_club_q_algo_handler.setFormatter(_club_q_algo_formatter)
club_q_algo_logger.addHandler(_club_q_algo_handler)


def attribution(voeux, pceens, promo_1A, bonus, corruption):
    """
    Algorithme d'attribution des places du Club Q :

    Args:
        voeux: Liste des voeux de la saison à trier.
        pceens: Liste des pceens qui ont accès au Club Q dont le mécontentement peut varier

    Returns:
        voeux: La liste des voeux dont des places ont été attribuées
        pceens: La liste des pcéens dont le mécontentement a pu varier

    Algorithme :
    Tant que la fin de la liste des voeux n'a pas été atteinte :
        Trier la liste des voeux par priorité croissante et mécontentement croissant
        Parcourir la liste des voeux :
            Si le voeu n'a pas encore des places attribuées :
                S'il y a suffisament de places restantes pour donner toutes les places voulues par le pceen :
                    Attribuer toutes les places voulues
                Sinon si y a que partiellement assez de places restantes pour donner le maximum de places entre le nombre de places minimum voulues et le nombre de places voulues :
                    Attribuer le maximum de places possible
                Sinon
                    Ajouter le mécontentement au pcéen fois l'exponentielle inverse de la priorité + 1
                    Regarder si le pcéen a fait un voeu avec une priorité plus basse et l'augmenter de 1
                    Sortir de la boucle des voeux
        Si voeu avec places non attribuées, récupérer la liste des voeux excepté celui qui n'a pas pu être attribué et recommencer la boucle.

    """
    for pceen in pceens:
        if pceen.discontent == None:
            pceen.discontent = 0

    clear_log_file()

    for pceen in pceens:
        if pceen.promo == promo_1A:
            pceen.discontent += bonus[0]
        elif pceen.promo == promo_1A - 1:
            pceen.discontent += bonus[1]
        elif pceen.promo == promo_1A - 2:
            pceen.discontent += bonus[2]
        elif pceen.promo == promo_1A - 3:
            pceen.discontent += bonus[3]
        else:
            pceen.discontent += -10

    i = 0
    while i < len(voeux):
        voeux, pceens = current_discontent(voeux, pceens)
        voeux.sort(key=lambda x: (x.priorite, -x.pceen.discontent))
        i = 0
        for voeu in voeux:
            if random.random() > 0.99:
                i = random.randint(0, len(efioohze) - 1)
                print(i)
                club_q_algo_logger.info(efioohze[i])

            if voeu.places_attribuees == 0:
                if (
                    voeu.spectacle.nb_tickets
                    - sum_places_attribuees_spect(voeu.spectacle, voeux)
                    - voeu.places_demandees
                    >= 0
                ):
                    voeu.places_attribuees = voeu.places_demandees
                    club_q_algo_logger.info(
                        f"Full - {voeu.places_attribuees} places - {voeu.pceen.full_name} - {voeu.spectacle.nom} - Priority {voeu.priorite} - Discontent {voeu.pceen.discontent :.2f}"
                    )
                    if voeu.priorite < 6:
                        for pceen in pceens:
                            if voeu.pceen.id == pceen.id:
                                pceen.discontent = pceen.discontent + 1 / 3 * voeu.priorite - 2
                                club_q_algo_logger.info(
                                    f"Substracted {1/3*voeu.priorite-2 :.2f} discontent. New discontent : {pceen.discontent :.2f}"
                                )
                elif (
                    voeu.spectacle.nb_tickets
                    - sum_places_attribuees_spect(voeu.spectacle, voeux)
                    - places_minimum_handle(voeu.places_minimum)
                    >= 0
                ):
                    voeu.places_attribuees = voeu.spectacle.nb_tickets - sum_places_attribuees_spect(
                        voeu.spectacle, voeux
                    )
                    club_q_algo_logger.info(
                        f"Partial - {voeu.places_attribuees} places - {voeu.pceen.full_name} - {voeu.spectacle.nom} - Priority {voeu.priorite} - Discontent {voeu.pceen.discontent :.2f} - {voeu.places_demandees} asked."
                    )
                    if voeu.priorite < 6:
                        for pceen in pceens:
                            if voeu.pceen.id == pceen.id:
                                pceen.discontent = pceen.discontent + 1 / 6 * voeu.priorite - 1
                                club_q_algo_logger.info(
                                    f"Substracted {1/6*voeu.priorite-1 :.2f} discontent. New discontent : {pceen.discontent :.2f}"
                                )
                else:
                    club_q_algo_logger.info(
                        f"Refused - {voeu.pceen.full_name} - {voeu.spectacle.nom} - Priority {voeu.priorite} - {sum_places_attribuees_spect(voeu.spectacle, voeux)} left - {voeu.places_demandees} asked"
                    )
                    if voeu.priorite < 5:
                        for pceen in pceens:
                            if voeu.pceen.id == pceen.id:
                                pceen.discontent = pceen.discontent - 2 / 3 * voeu.priorite + 8 / 3
                                club_q_algo_logger.info(
                                    f"Added {-2/3*voeu.priorite+8/3 :.2f} discontent. New discontent : {pceen.discontent :.2f}"
                                )
                    a = 0
                    for voeu_c in voeux:
                        if voeu._pceen_id == voeu_c._pceen_id and voeu_c != voeu and voeu_c.priorite > voeu.priorite:
                            voeu_c.priorite = voeu_c.priorite - 1
                            club_q_algo_logger.info(
                                f"Upgraded priority of Voeu {voeu_c.id} - {voeu_c.spectacle.nom} - Priority {voeu_c.priorite:} - Old priority : {voeu_c.priorite+1}"
                            )
                            a = 1
                    if a == 0:
                        club_q_algo_logger.info(
                            f"Did not find any more voeu for {voeu.pceen.full_name} after priority {voeu.priorite}"
                        )
                    break
            i += 1
        if i == 0:
            voeux = voeux[1:]
        elif i < len(voeux):
            voeux = voeux[:i] + voeux[i + 1 :]

    # Sum up for logs
    club_q_algo_logger.info("\n")
    sum_up(voeux, pceens)

    return (voeux, pceens)


def sum_places_attribuees_spect(spectacle, voeux):
    """
    Gives the number of given place for a spectacle on the current set of voeux (not yet registered in database)
    """
    sum = 0
    for voeu in voeux:
        if voeu._spectacle_id == spectacle.id:
            sum += voeu.places_attribuees
    return sum


def sum_places_attribuees_pceen(pceen, voeux):
    """
    Gives the number of given place for a pceen on the current set of voeux (not yet registered in database)
    """
    sum = 0
    for voeu in voeux:
        if voeu._pceen_id == pceen.id:
            sum += voeu.places_attribuees
    return sum


def current_discontent(voeux, pceens):
    """
    Correlate the current discontent of a pceen based on the voeu studied (not yet registered in database)
    """
    for voeu in voeux:
        for pceen in pceens:
            if pceen.id == voeu.pceen.id:
                voeu.pceen.discontent = pceen.discontent
    return (voeux, pceens)


def clear_log_file():
    with open(os.path.join("logs", "club_q", "algorithm.log"), "w") as file:
        pass


def places_minimum_handle(nb):
    if nb == None:
        nb = 0
    return nb


def sum_up(voeux, pceens):
    club_q_algo_logger.info("-" * 35)
    club_q_algo_logger.info("-----*** Résumé Spectacles ***-----")
    club_q_algo_logger.info("-" * 35)
    spectacles = []
    for voeu in voeux:
        if voeu.spectacle.id not in spectacles:
            club_q_algo_logger.info(
                f"{voeu.spectacle.nom} - {voeu.spectacle.nb_tickets} places - {sum_places_attribuees_spect(voeu.spectacle, voeux)} attribuées"
            )
            spectacles.append(voeu.spectacle.id)
    club_q_algo_logger.info("\n")
    club_q_algo_logger.info("-" * 31)
    club_q_algo_logger.info("-----*** Résumé Pcéens ***-----")
    club_q_algo_logger.info("-" * 31)
    for pceen in pceens:
        if random.random() > 0.90:
            i = random.randint(0, len(izadooa) - 1)
            print(i)
            club_q_algo_logger.info(izadooa[i])
        club_q_algo_logger.info(f"{pceen.full_name} - {sum_places_attribuees_pceen(pceen, voeux)} places attribuées")


efioohze = [
    "Les billets du Club Q disparaissent mystérieusement chaque année, mais le président Samuel Czitrom prétend qu'il s'agit d'une magie de l'ESPCI.",
    "Alec Cochard aurait été vu en train de négocier des rabais illégaux avec le CROUS pour obtenir plus de billets à bas prix.",
    "Le BDE aurait secrètement détourné des fonds pour financer des soirées avec des billets du Club Q en échange de votes lors des élections étudiantes.",
    "Les Alumnis de l'ESPCI organisent des jeux de hasard clandestins avec des billets de spectacles volés au Club Q, tout ça pour financer leurs réunions d'anciens élèves.",
    "Chimie Paris aurait échangé des formules chimiques secrètes contre des billets de ballet. Une opération risquée qui pourrait tout révéler !",
    "Le Club Q aurait créé une mystérieuse société offshore au Luxembourg pour cacher ses profits illicites. Le trésorier Alec Cochard en serait le cerveau.",
    "Samuel Czitrom aurait une collection secrète de billets de spectacles volés qu'il garde dans un coffre-fort au sous-sol de l'ESPCI.",
    "Le président du Club Q serait en train de négocier des alliances secrètes avec l'ENS Ulm pour contrôler le marché des spectacles étudiants.",
    "Alec Cochard aurait inventé un algorithme de corruption sophistiqué pour s'assurer que seuls ses amis obtiennent les meilleurs billets du Club Q.",
    "Le BDE aurait caché des indices dans les billets de spectacles du Club Q pour organiser une chasse au trésor illégale dans l'enceinte de l'ESPCI.",
    "Le Club Q aurait secrètement conclu un partenariat avec un cartel international de l'art pour échanger des billets de spectacles contre des toiles de maîtres volées.",
    "On raconte que Samuel Czitrom organise des soirées secrètes dans des sous-sols obscurs de Paris, où seuls les initiés ont accès aux précieux billets du Club Q.",
    "Alec Cochard serait devenu expert en cryptomonnaies pour blanchir l'argent provenant de la vente de billets. L'ESPCI pourrait-elle devenir le nouveau paradis fiscal ?",
    "Le président du Club Q aurait engagé un mystérieux agent double pour infiltrer les rangs de la concurrence et voler leurs secrets de billets à prix réduit.",
    "Le BDE et les Alumnis se seraient unis pour former une coalition secrète appelée 'Les Dévoreurs de Billets' dans le but de s'emparer du trésor du Club Q.",
    "Chimie Paris aurait mis en place un laboratoire secret pour dupliquer des billets du Club Q. L'expérience aurait-elle mal tourné ?",
    "On dit que le Club Q a créé sa propre monnaie numérique, le 'Qcoin', pour faciliter les transactions secrètes entre étudiants et institutions corrompues.",
    "Samuel Czitrom aurait construit un tunnel souterrain entre l'ESPCI et l'Opéra Garnier pour faciliter le vol de costumes de ballet en échange de billets.",
    "Alec Cochard aurait inventé une machine à voyager dans le temps pour acheter des billets à des prix réduits dans le passé et les revendre au présent.",
    "Le BDE aurait organisé des tournois de poker clandestins avec des billets de spectacles du Club Q comme enjeu. Le vainqueur emporte tous les billets !",
]


izadooa = [
    "Samuel Czitrom - 100 places attribuées : Là où il y a de la gêne, il n'y a pas de plaisir, mais il y a beaucoup de places attribuées !",
    "Alec Cochard - 96 places attribuées : Il a réussi à obtenir 96 places, mais il ne sait toujours pas où se trouve la salle de spectacle.",
    "Club Q - 1000 places attribuées : Qui aurait cru que le Club Q avait autant de membres ? Chaque membre a reçu une place attribuée, même les chaises vides !",
    "Le CROUS - 50 places attribuées : Le Club Q et le CROUS se sont associés pour un échange de places. Le Club Q a obtenu 50 places gratuites et le CROUS a obtenu... euh, rien.",
    "BDE - 75 places attribuées : Le BDE a essayé de négocier plus de places, mais le Club Q a dit : 'Désolé, nous n'avons que 75 places à attribuer, et elles sont déjà parties aux plus offrants.'",
    "Alumnis - 10 places attribuées : Les anciens élèves essaient de revenir à l'école, mais le Club Q est là pour leur rappeler qu'ils ont déjà obtenu leur diplôme !",
    "Chimie Paris - 30 places attribuées : Le Club Q a attribué 30 places à Chimie Paris pour un spectacle de magie. Ils espèrent que Chimie Paris pourra résoudre le mystère de la disparition des places.",
    "ENS Ulm - 20 places attribuées : L'ENS Ulm est jalouse du Club Q, mais elles ont reçu 20 places en cadeau pour les consoler.",
    "École Polytechnique - 5 places attribuées : L'École Polytechnique a demandé plus de places, mais le Club Q a répondu : 'Nous ne pouvons pas vous donner plus de places, car vous les transformeriez en équations différentielles.'",
    "Université Paris-Saclay - 25 places attribuées : L'Université Paris-Saclay a reçu 25 places, mais elles se sont perdues dans le vaste campus.",
]
