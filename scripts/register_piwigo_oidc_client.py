"""Register the OPC Piwigo OIDC client in the database.
This should only be done ONCE and client ID + Secret should be stored in Piwigo"""

import time

from werkzeug.security import gen_salt

from app import db
from app.models.oidc import OAuth2Client


PIWIGO_REDIRECT_URI = "https://opc.pc-est-magique.fr/plugins/OpenIdConnect/auth.php"


def main():
    # Check to avoid duplication
    existing = OAuth2Client.query.all()
    for c in existing:
        uris = c.client_metadata.get("redirect_uris", []) if c.client_metadata else []
        if PIWIGO_REDIRECT_URI in uris:
            print(f"Un client avec cet URI existe déjà (client_id={c.client_id}).")
            print("Abandon.")
            return

    client_id = gen_salt(24)
    client_secret = gen_salt(48)

    client = OAuth2Client(
        client_id=client_id,
        client_id_issued_at=int(time.time()),
        client_secret_expires_at=0,  # never expires
    )
    client.set_client_metadata({
        "client_name": "Piwigo",
        "client_uri": PIWIGO_REDIRECT_URI,
        "redirect_uris": [PIWIGO_REDIRECT_URI],
        "scope": "openid profile email",
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "client_secret_basic",
    })
    client.client_secret = client_secret

    db.session.add(client)
    db.session.commit()

    print("Client enregistré avec succès !")
    print(f"  client_id:     {client_id}")
    print(f"  client_secret: {client_secret}")
    print(f"  redirect_uri:  {PIWIGO_REDIRECT_URI}")
    print(f"  scope:         openid profile email")
    print()
    print("Veuillez renseigner ces valeurs dans les paramètres du plugin OpenID Connect de l'instance Piwigo d'OPC.")
