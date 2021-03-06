"""PC est magique - Crée les permissions et rôles de base.

Ce script peut uniquement être appelé depuis Flask :
  * Soit depuis l'interface en ligne (menu GRI) ;
  * Soit par ligne de commande :
    cd /home/pc-est-magique/pc-est-magique
    ./env/bin/flask script update_roles.py

02/2022 Loïc 137
"""

import sys

try:
    from app import db, __version__
    from app.models import Role, Permission, PermissionScope, PermissionType
    from app.utils import helpers, typing

except ImportError:
    sys.stderr.write(
        "ERREUR - Ce script peut uniquement être appelé depuis Flask :\n"
        "  * Soit depuis l'interface en ligne (menu GRI) ;\n"
        "  * Soit par ligne de commande :\n"
        "    cd /home/pc-est-magique/pc-est-magique; "
        "    ./env/bin/flask script update_roles.py\n"
    )
    sys.exit(1)


def permissions() -> dict[str, dict[str, typing.Any]]:
    """Permissions à définir. Modifier cette fonction pour modifier les permissions."""
    return {
        "access_photos": dict(
            type=PermissionType.read,
            scope=PermissionScope.photos,
            ref_id=None,
        ),
        "access_intrarez": dict(
            type=PermissionType.read,
            scope=PermissionScope.intrarez,
            ref_id=None,
        ),
        "manage_pceens": dict(
            type=PermissionType.all,
            scope=PermissionScope.pceen,
            ref_id=None,
        ),
        "manage_roles": dict(
            type=PermissionType.all,
            scope=PermissionScope.role,
            ref_id=None,
        ),
        "manage_collections": dict(
            type=PermissionType.all,
            scope=PermissionScope.collection,
            ref_id=None,
        ),
    }


def roles(perms: dict[str, Permission]) -> dict[str, dict[str, typing.Any]]:
    """Rôles à définir. Modifier cette fonction pour modifier les rôles.

    Args:
        perms: Permissions définies dans permissions(), après récupération / création.
    """
    return {
        "Admin": dict(
            index=0,
            color="e40046",
            permissions=[
                perms["manage_pceens"],
                perms["manage_roles"],
                perms["manage_collections"],
            ],
        ),
        "Rezident": dict(  # NE PAS RENOMMER - nom utilisé dans app/routes/auth/utils.py
            index=10,
            color="d5c0a9",
            permissions=[
                perms["access_intrarez"],
            ],
        ),
        "Élève": dict(  # NE PAS RENOMMER - nom utilisé dans app/routes/auth/utils.py
            index=10,
            color="64b9e9",
            permissions=[
                perms["access_photos"],
            ],
        ),
        "Alumni": dict(
            index=10,
            color="152f4e",
            permissions=[
                perms["access_photos"],
            ],
        ),
    }


def main():
    perms = {}
    for slug, perm_dict in permissions().items():
        permission = Permission.query.filter_by(**perm_dict).first()
        if permission:
            perms[slug] = permission
            continue

        print(f"Ajout de la permission {perm_dict}...")
        perms[slug] = Permission(**perm_dict)
        db.session.add(perms[slug])

    for name, roles_dict in roles(perms).items():
        role = Role.query.filter_by(name=name).first()
        if role:
            print(f"Mise à jour de {role}...")
            for col, val in roles_dict.items():
                setattr(role, col, val)
            continue

        print(f"Ajout du rôle '{name}'...")
        role = Role(name=name, **roles_dict)
        db.session.add(role)

    db.session.commit()
    helpers.log_action(
        f"Updated permissions and roles to those in 'update_roles.py' in v{__version__}"
    )
    print("Modifications effectuées.")
