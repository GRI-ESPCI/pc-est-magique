"""PC est magique - Création des comptes utilisateurs de la promo entrante.

Ce script peut uniquement être appelé depuis Flask :
  * Soit depuis l'interface en ligne (menu GRI) ;
  * Soit par ligne de commande :
    cd /home/pc-est-magique/pc-est-magique
    ./env/bin/flask script update_roles.py

Le fichier contenant les informations des nouveaux utilisateurs doit
avoir pour nom `new_promo.csv` et doit avoir les colonnes suivantes :
Peu importe, Nom, Prénom, Email
Il faut modifier le script pour changer le numéro de la promo.

08/2023 Louis (aka Le Chauve Capé) 139
"""
import csv
import string
import random

try:
    from app import db, __version__
    from app.models import PCeen
    from app.routes.auth import email
    from app.routes.auth.utils import new_username
    from app.utils import helpers, loggers
    from app.utils.roles import grant_rezident_role

except ImportError:
    sys.stderr.write(
        "ERREUR - Ce script peut uniquement être appelé depuis Flask :\n"
        "  * Soit depuis l'interface en ligne (menu GRI) ;\n"
        "  * Soit par ligne de commande :\n"
        "    cd /home/pc-est-magique/pc-est-magique; "
        "    ./env/bin/flask script update_roles.py\n"
    )
    sys.exit(1)

@loggers.log_exception(reraise=True)
def main():
    with open("new_promo.csv", 'r', newline='') as file:
        reader = csv.reader(file, delimiter=',')
        for row in reader:
            user = PCeen(
                username=new_username(row[2], row[1]),
                nom=row[1],
                prenom=row[2],
                promo=142,
                email=row[3]
            )

            # Generate random password
            letters = string.ascii_lowercase
            user.set_password(''.join(random.choice(letters) for i in range(32)))

            grant_rezident_role(user)
            db.session.add(user)
            db.session.commit()
            helpers.log_action(
                f"Internal -> Registered account {user!r} ({user.prenom} {user.nom} " f"{user.promo}, {user.email})"
            )
            email.send_account_registered_email(user)
    print("Done.")


