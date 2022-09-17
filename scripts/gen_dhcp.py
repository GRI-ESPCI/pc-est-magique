"""PC est magique - Génération des tables DHCP

Pour toutes les chambres, attribue une adresse IP aux appareils de
l'occupant actuel. L'attribution d'IP elle-même (y compris en cas de
bannissement est gérée par `Device.allocate_ip_for`).

Ce script peut uniquement être appelé depuis Flask :
  * Soit depuis l'interface en ligne (menu GRI) ;
  * Soit par ligne de commande :
    cd /home/pc-est-magique/pc-est-magique; ./env/bin/flask script gen_dhcp.py

10/2021 Loïc 137
"""

import os
import sys

import flask

try:
    from app.models import Room
    from app.utils import loggers
except ImportError:
    sys.stderr.write(
        "ERREUR - Ce script peut uniquement être appelé depuis Flask :\n"
        "  * Soit depuis l'interface en ligne (menu GRI) ;\n"
        "  * Soit par ligne de commande :\n"
        "    cd /home/pc-est-magique/pc-est-magique; "
        "    ./env/bin/flask script gen_dhcp.py\n"
    )
    sys.exit(1)


@loggers.log_exception(reraise=True)
def main() -> None:
    rules = ""

    rooms = Room.query.order_by(Room.num).all()
    for room in rooms:
        if not room.current_rental:
            print(f"Chambre {room.num} non occupée, on passe")
            continue

        pceen = room.current_rental.pceen
        print(f"Chambre {room.num} occupée par {pceen.full_name}")
        if pceen.is_banned:
            print(f"    -- BANNI : {pceen.current_ban} --")

        for device in pceen.devices:
            ip = device.allocate_ip_for(room)
            print(f"    Appareil #{device.id} : {device.mac_address} -> {ip}")
            rules += (
                f"host {pceen.username}-{room.num}-{device.id} {{\n"
                f"\thardware ethernet {device.mac_address};\n"
                f"\tfixed-address {ip};\n"
                "}\n"
            )

    # Écriture dans le fichier
    file = os.getenv("DHCP_HOSTS_FILE") or ""
    if not os.path.isfile(file):
        raise FileNotFoundError(
            f"Le ficher d'hôtes DHCP '{file}' n'existe pas (variable d'environment DHCP_HOSTS_FILE)"
        )

    with open(file, "w") as fp:
        fp.write(
            "# Ce fichier est généré automatiquement par gen_dhcp.py\n"
            f"# ({__file__}).\n"
            "# Ne PAS le modifier à la main, ce serait écrasé !\n#\n"
            "#   * Pour ajouter un appareil à un PCéen,\n"
            "#       - utiliser l'interface en ligne \n"
            f"#         ({flask.url_for('gris.pceens')})\n"
            "#       - OU utiliser `flask shell` pour l'ajouter en base,\n"
            "#         puis régénérer avec `flask script gen_dhcp.py`\n"
            "#         (flask = /home/pc-est-magique/pc-est-magique/env/bin/flask)\n#\n"
            "#   * Pour ajouter toute autre règle, modifier directement\n"
            "#     /env/dhcp/dhcpd.conv\n#\n"
        )
        fp.write(rules)
