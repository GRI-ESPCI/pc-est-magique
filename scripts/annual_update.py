"""PC est magique - Effectue toutes les actions à réaliser automatiquement chaque année.

Conçu pour être appelé tous les ans, environ à la fin de l'été :
    * Remplace le rôle "Élève" par le rôle "Alumni" pour tous les comptes ayant terminé leur 4e année cette année ;
    * Envoie également un mail au PCéen l'informant du changement d'état ;
    * Crée un nouveau rôle pour l'année entrante, avec les droits appropriés.
    * Crée une nouvelle collection pour l'année entrante, avec les droits appropriés.

Ce script peut uniquement être appelé depuis Flask :
  * Soit depuis l'interface en ligne (menu GRI) ;
  * Soit par ligne de commande :
    cd /home/pc-est-magique/pc-est-magique
    ./env/bin/flask script annual_update.py

12/2022 Loïc 137
"""

import datetime
import os
import sys
import time

try:
    from app import db, __version__
    from app.models import Role, Permission, PCeen, Collection, PermissionType, PermissionScope
    from app.routes.gris import email
    from app.utils import helpers, loggers

except ImportError:
    sys.stderr.write(
        "ERREUR - Ce script peut uniquement être appelé depuis Flask :\n"
        "  * Soit depuis l'interface en ligne (menu GRI) ;\n"
        "  * Soit par ligne de commande :\n"
        "    cd /home/pc-est-magique/pc-est-magique; "
        "    ./env/bin/flask script annual_update.py\n"
    )
    sys.exit(1)


def replace_student_role(leaving_promo: int) -> None:
    pceens: list[PCeen] = PCeen.query.filter_by(promo=leaving_promo).all()
    total = len(pceens)

    student_role = Role.query.filter_by(name="Élève").one()
    alumni_role = Role.query.filter_by(name="Alumni").one()

    for index, pceen in enumerate(pceens):
        if student_role not in pceen.roles:
            continue
        time.sleep(2)

        print(f"Processing ({index + 1}/{total}): {pceen!r}...")

        pceen.roles.remove(student_role)
        if alumni_role not in pceen.roles:
            pceen.roles.append(alumni_role)

        email.send_role_switch_email(pceen)

        db.session.commit()
        helpers.log_action(f"Annual update: replaced Student role by Alumni role for {pceen!r} (so long)")


def create_new_collection(entering_promo: int) -> None:
    collection = Collection.query.filter_by(dir_name=str(entering_promo)).first()
    if not collection:
        collection = Collection(
            dir_name=str(entering_promo),
            name=f"[AUTO-CREATED] {entering_promo}",
            description=f"Tous les évènements de la première année de la promotion {entering_promo} à PC !",
            start=datetime.date(entering_promo + 1881, 9, 1),
            end=datetime.date(entering_promo + 1882, 6, 30),
            visible=False,
        )
        os.mkdir(collection.full_path)
        db.session.add(collection)
        db.session.commit()
        helpers.log_action(f"Annual update: created collection {collection!r}")

    role = Role.query.filter_by(name=str(entering_promo)).first()
    if not role:
        role = Role(name=str(entering_promo), index=entering_promo)
        db.session.add(role)
        db.session.commit()
        helpers.log_action(f"Annual update: created role {role!r}")

    # Add "read / collection 1XX" permission to the 4 promos studying this year
    read_collection = Permission(type=PermissionType.read, scope=PermissionScope.collection, ref_id=collection.id)
    role.permissions.append(read_collection)
    for year in range(1, 4):
        if role := Role.query.filter_by(name=str(entering_promo - year)).first():
            role.permissions.append(read_collection)

    db.session.commit()


@loggers.log_exception(reraise=True)
def main():
    current_year = datetime.date.today().year
    leaving_promo = current_year - 1885
    entering_promo = current_year - 1881

    replace_student_role(leaving_promo)
    create_new_collection(entering_promo)

    print("Done.")
