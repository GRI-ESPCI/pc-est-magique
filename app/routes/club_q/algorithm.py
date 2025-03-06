import logging
import os
import random
import copy
import flask
from flask_babel import _
from app.models import ClubQVoeu
from app import db

# Set up specific logging for the club q algorithm
club_q_algo_logger = logging.Logger("club_q_algo")
_club_q_algo_handler = logging.FileHandler("logs/club_q/algorithm.log")
_club_q_algo_formatter = logging.Formatter("")
_club_q_algo_handler.setFormatter(_club_q_algo_formatter)
club_q_algo_logger.addHandler(_club_q_algo_handler)

app = flask.Flask(__name__)


def attribution(voeux, pceens, spectacles, promo_1A, bonus, corruption):
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
                    Enlever le voeu de la liste et l'ajouter à celui des voeux à mettre à jour
                Sinon si y a que partiellement assez de places restantes pour donner le maximum de places entre le nombre de places minimum voulues et le nombre de places voulues :
                    Attribuer le maximum de places possible
                    Enlever le voeu de la liste et l'ajouter à celui des voeux à mettre à jour
                Sinon
                    Ajouter le mécontentement au pcéen fois l'exponentielle inverse de la priorité + 1
                    Regarder si le pcéen a fait un voeu avec une priorité plus basse et l'augmenter de 1
                    Enlever le voeu de la liste
                    Sortir de la boucle des voeux
            Sinon
                Enlever le voeu de la liste
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

    voeux_update = []
    #voeux_copy = [ClubQVoeu(id=voeu.id, _season_id=voeu._season_id, priorite=voeu.priorite) for voeu in voeux] #Create a copy of the value of the voeux which can be updated, as voeux is only a list of reference, and making a copy of it will change nothing
    voeux_copy = copy.deepcopy(voeux) #[voeu.__dict__.copy() for voeu in voeux]
    #app.logger.info(voeux[600])

    spectacles_places_attribuees = initialized_attributed_spectacles_places(spectacles, voeux)

    random.shuffle(voeux)
    voeux.sort(key=lambda x: (x.priorite, -x.pceen.discontent))
    id_save = [voeu.id for voeu in voeux]
    priority_save = [voeu.priorite for voeu in voeux]


    while len(voeux) != 0:
        voeux.sort(key=lambda x: (x.priorite, -x.pceen.discontent))

        while len(voeux) != 0:
            voeu = voeux[0]

            if corruption and random.random() > 0.99:
                i = random.randint(0, len(efioohze) - 1)
                club_q_algo_logger.info(efioohze[i])

            if voeu.places_attribuees == 0:

                for j in range(len(spectacles_places_attribuees)):
                    if voeu.spectacle.id == spectacles_places_attribuees[j][0]:
                        id_list_spect_attrib = j
                        break

                if (
                    voeu.spectacle.nb_tickets
                    - spectacles_places_attribuees[id_list_spect_attrib][1]
                    - voeu.places_demandees
                    >= 0
                ):
                    voeu.places_attribuees = voeu.places_demandees
                    spectacles_places_attribuees[id_list_spect_attrib][1] += voeu.places_demandees
                    club_q_algo_logger.info(
                        f"Plein - {voeu.places_attribuees} places - {voeu.pceen.full_name} - {voeu.spectacle.nom} - Priorité {voeu.priorite} - Mécontentement {voeu.pceen.discontent :.2f}"
                    )
                    if voeu.priorite < 6:
                        for pceen in pceens:
                            if voeu.pceen.id == pceen.id:
                                pceen.discontent = round(pceen.discontent + (1 / 3 * voeu.priorite - 2)*round(voeu.places_attribuees**1.5, 1), 1)
                                voeu.pceen.discontent = pceen.discontent
                                club_q_algo_logger.info(
                                    f"Réduction mécontentement de {(1/3*voeu.priorite-2)*round(voeu.places_attribuees**1.5,1) :.2f} . Nouveau mécontentement : {pceen.discontent :.2f}"
                                )
                    restore_priority(voeu, id_save, priority_save)
                    voeux_update.append(voeu)
                    voeux.pop(0)


                elif (
                    voeu.spectacle.nb_tickets
                    - spectacles_places_attribuees[id_list_spect_attrib][1]
                    - places_minimum_handle(voeu.places_minimum)
                    > 0
                ):
                    voeu.places_attribuees = (
                        voeu.spectacle.nb_tickets - spectacles_places_attribuees[id_list_spect_attrib][1]
                    )
                    spectacles_places_attribuees[id_list_spect_attrib][1] += voeu.places_attribuees
                    club_q_algo_logger.info(
                        f"Partiel - {voeu.places_attribuees} places - {voeu.pceen.full_name} - {voeu.spectacle.nom} - Priorité {voeu.priorite} - Mécontentement {voeu.pceen.discontent :.2f} - {voeu.places_demandees} demandées."
                    )
                    if voeu.priorite < 6:
                        for pceen in pceens:
                            if voeu.pceen.id == pceen.id:
                                pceen.discontent = round(pceen.discontent + (1 / 6 * voeu.priorite - 1)*round(voeu.places_attribuees**1.5, 1), 1)
                                voeu.pceen.discontent = pceen.discontent
                                club_q_algo_logger.info(
                                    f"Réduction mécontentement de {(1/6*voeu.priorite-1)*round(voeu.places_attribuees**1.5,1) :.2f}. Nouveau mécontentement : {pceen.discontent :.2f}"
                                )
                    restore_priority(voeu, id_save, priority_save)
                    voeux_update.append(voeu)
                    voeux.pop(0)


                else:
                    club_q_algo_logger.info(
                        f"Refusé - {voeu.pceen.full_name} - {voeu.spectacle.nom} - Priorité {voeu.priorite} - {spectacles_places_attribuees[id_list_spect_attrib][1]} places restantes - {voeu.places_demandees} places demandées"
                    )
                    if voeu.priorite < 5:
                        for pceen in pceens:
                            if voeu.pceen.id == pceen.id:
                                pceen.discontent = round(pceen.discontent - 2 / 3 * voeu.priorite + 8 / 3, 1)
                                voeu.pceen.discontent = pceen.discontent
                                club_q_algo_logger.info(
                                    f"Ajout de {-2/3*voeu.priorite+8/3 :.2f} de mécontentement. Nouveau mécontentement : {pceen.discontent :.2f}"
                                )
                    a = 0
                    for voeu_c in voeux:
                        if voeu._pceen_id == voeu_c._pceen_id and voeu_c != voeu and voeu_c.priorite > voeu.priorite:
                            voeu_c.priorite = voeu_c.priorite - 1
                            club_q_algo_logger.info(
                                f"Incrémentation priorité voeu {voeu_c.id} - {voeu_c.spectacle.nom} - Nouvelle priorité : {voeu_c.priorite:} - Ancienne priorité : {voeu_c.priorite+1}"
                            )
                            a = 1
                    if a == 0:
                        club_q_algo_logger.info(
                            f"Plus de voeux pour {voeu.pceen.full_name} après la priorité {voeu.priorite}"
                        )
                    restore_priority(voeu, id_save, priority_save)
                    voeux.pop(0)

                    break
            else:
                restore_priority(voeu, id_save, priority_save)
                voeux.pop(0)
    #app.logger.info(voeux[600])

    """
    # Reattribuate correct proprities
    for voeu in voeux_update:
        for voeu_init in voeux_copy:
            
            if voeu.id == voeu_init.id:
                app.logger.info(f"Before {voeu.priorite}, {voeu_init.priorite}")
                voeu.priorite = voeu_init.priorite
                app.logger.info(f"After {voeu.priorite}, {voeu_init.priorite}")
    """

    # Sum up for logs
    club_q_algo_logger.info("\n")
    sum_up(voeux_update, pceens, corruption)

    return (voeux_update, pceens)


def initialized_attributed_spectacles_places(spectacles, voeux):
    """
    Gives the list of attributed places for each spectacles
    """
    spectacles_places_attribuees = [[spectacles[i].id, 0] for i in range(len(spectacles))]

    for i, spectacle in enumerate(spectacles):
        spectacles_places_attribuees[i][1] = sum_places_attribuees_spect(spectacle, voeux)

    return spectacles_places_attribuees


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


def clear_log_file():
    with open(os.path.join("logs", "club_q", "algorithm.log"), "w") as file:
        pass


def places_minimum_handle(nb):
    if nb == None:
        nb = 0
    return nb


def sum_up(voeux, pceens, corruption):
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
        if corruption and random.random() > 0.90:
            i = random.randint(0, len(izadooa) - 1)
            print(i)
            club_q_algo_logger.info(izadooa[i])
        club_q_algo_logger.info(f"{pceen.full_name} - {sum_places_attribuees_pceen(pceen, voeux)} places attribuées")


def restore_priority(voeu, id_save, priority_save):
    var_check = False
    for v, id in enumerate(id_save):
        if voeu.id == id:
            voeu.priorite = priority_save[v] #Restore initial priority
            var_check = True
            break
    if not var_check:
        raise ValueError('While handleling this voeu, the original voeu could not be found')


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
