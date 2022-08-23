"""PC est magique - Mise en place des paiements Internet à la Rez

Pour tous les PCéens qui ont enregistré un appareil mais qui n'ont pas
d'abonnement :
  * Crée le premier abonnement
  * Envoie un mail d'information d'expiration dans un mois

Ce script ne fait a priori rien passé le premier appel (étant donné que
l'enregistrement du premier appareil déclenche le premier abonnement).

Il sera probablement détruit lors d'une prochaine mise à jour.

Ce script peut uniquement être appelé depuis Flask :
  * Soit depuis l'interface en ligne (menu GRI) ;
  * Soit par ligne de commande :
    cd /home/pc-est-magique/pc-est-magique; ./env/bin/flask script setup_payments.py

12/2021 Loïc 137
"""

import sys

import flask
import flask_babel
from flask_babel import _

try:
    from app.email import send_email
    from app.models import PCeen
    from app.utils import loggers
except ImportError:
    sys.stderr.write(
        "ERREUR - Ce script peut uniquement être appelé depuis Flask :\n"
        "  * Soit depuis l'interface en ligne (menu GRI) ;\n"
        "  * Soit par ligne de commande :\n"
        "    cd /home/pc-est-magique/pc-est-magique; "
        "    ./env/bin/flask script setup_payments.py\n"
    )
    sys.exit(1)


def send_on_setup_email(pceen: PCeen) -> None:
    with flask_babel.force_locale(pceen.locale or "fr"):
        # Render mail content, in PCéen language
        subject = _("IMPORTANT - Paiement d'Internet")
        html_body = flask.render_template(
            "payments/mails/on_setup.html",
            pceen=pceen,
            sub=pceen.current_subscription,
        )

    # Send email
    send_email(
        "payments/on_setup",
        subject=f"[PC est magique] {subject}",
        recipients={pceen.email: pceen.full_name},
        html_body=html_body,
    )


@loggers.log_exception(reraise=True)
def main() -> None:
    pceens = PCeen.query.all()
    n_rez = len(pceens)

    for i_rez, pceen in enumerate(pceens):
        print(f"[{i_rez + 1}/{n_rez}] {pceen.full_name} : ", end="")
        sys.stdout.flush()

        if not pceen.devices:
            print("Pas d'appareils, skip")
            continue
        if pceen.subscriptions:
            print("Déjà un abonnement, skip")
            continue

        # Un appareil mais pas d'abonnement : c tipar
        print("Ajout de l'abonnement... ", end="")
        sys.stdout.flush()
        pceen.add_first_subscription()
        print("Envoi du mail... ", end="")
        sys.stdout.flush()
        send_on_setup_email(pceen)
        print("Fait !")
