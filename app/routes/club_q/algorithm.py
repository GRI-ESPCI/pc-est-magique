import logging
import os


# Set up specific logging for the club q algorithm
club_q_algo_logger = logging.Logger("club_q_algo")
_club_q_algo_handler = logging.FileHandler("logs/club_q/algorithm.log")
_club_q_algo_formatter = logging.Formatter("")
_club_q_algo_handler.setFormatter(_club_q_algo_formatter)
club_q_algo_logger.addHandler(_club_q_algo_handler)


def attribution(voeux, pceens, promo_1A, bonus):
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
        club_q_algo_logger.info(f"{pceen.full_name} - {sum_places_attribuees_pceen(pceen, voeux)} places attribuées")
