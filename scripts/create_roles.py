"""PC est magique - Crée les rôles de base.

Ce script peut uniquement être appelé depuis Flask :
  * Soit depuis l'interface en ligne (menu GRI) ;
  * Soit par ligne de commande :
    cd /home/pc-est-magique/pc-est-magique
    ./env/bin/flask script create_roles.py

02/2022 Loïc 137
"""

import sys

try:
    from app import db
    from app.models import Role, Permission, PermissionScope, PermissionType
except ImportError:
    sys.stderr.write(
        "ERREUR - Ce script peut uniquement être appelé depuis Flask :\n"
        "  * Soit depuis l'interface en ligne (menu GRI) ;\n"
        "  * Soit par ligne de commande :\n"
        "    cd /home/pc-est-magique/pc-est-magique; "
        "    ./env/bin/flask script create_roles.py\n"
    )
    sys.exit(1)


def main() -> None:
    permissions = [
        Permission(type=PermissionType.all, scope=PermissionScope.pceen),
        Permission(type=PermissionType.all, scope=PermissionScope.role),
        Permission(type=PermissionType.all, scope=PermissionScope.photos),
        Permission(type=PermissionType.all, scope=PermissionScope.collection),
    ]
    db.session.add_all(permissions)
    admin = Role(name="Admin", index=0, color="ff0000",
                 permissions=permissions)
    db.session.add(admin)
    db.session.commit()
