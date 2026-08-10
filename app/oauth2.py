from authlib.integrations.flask_oauth2 import AuthorizationServer
from authlib.oauth2.rfc6749.grants import (
    AuthorizationCodeGrant as _AuthorizationCodeGrant,
)
from authlib.oidc.core.grants import OpenIDCode as _OpenIDCode

from app import db
from app.models.oidc import OAuth2Client, OAuth2AuthorizationCode, OAuth2Token
from app.models.auth import PCeen


server = AuthorizationServer()


def query_client(client_id):
    return OAuth2Client.query.filter_by(client_id=client_id).first()


def save_token(token_data, request):
    if request.user:
        user_id = request.user.id
    else:
        user_id = None
    client = request.client
    item = OAuth2Token(
        client_id=client.client_id,
        user_id=user_id,
        **token_data
    )
    db.session.add(item)
    db.session.commit()


class AuthorizationCodeGrant(_AuthorizationCodeGrant):
    def save_authorization_code(self, code, request):
        client = request.client
        auth_code = OAuth2AuthorizationCode(
            code=code,
            client_id=client.client_id,
            redirect_uri=request.redirect_uri,
            scope=request.scope,
            user_id=request.user.id,
        )
        db.session.add(auth_code)
        db.session.commit()
        return auth_code

    def query_authorization_code(self, code, client):
        item = OAuth2AuthorizationCode.query.filter_by(
            code=code, client_id=client.client_id).first()
        if item and not item.is_expired():
            return item
        return None

    def delete_authorization_code(self, authorization_code):
        db.session.delete(authorization_code)
        db.session.commit()

    def authenticate_user(self, authorization_code):
        return PCeen.query.get(authorization_code.user_id)


class OpenIDCode(_OpenIDCode):
    def get_jwt_config(self, grant):
        from flask import current_app
        import os
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization

        key = current_app.config.get("OIDC_PRIVATE_KEY")
        if not key:
            key_path = current_app.config.get("OIDC_RSA_KEY_PATH")
            if not key_path:
                key_path = os.path.join(current_app.root_path, '..', 'oidc_rsa.pem')
                
            if os.path.exists(key_path):
                with open(key_path, 'r') as f:
                    key = f.read()
            else:
                private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
                key = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ).decode('utf-8')
                with open(key_path, 'w') as f:
                    f.write(key)

        return {
            "key": key,
            "alg": "RS256",
            "iss": current_app.config.get("OIDC_ISSUER", "https://pc-est-magique.fr"),
            "exp": 3600
        }

    def exists_nonce(self, nonce, request):
        # Nonce replay check intentionally disabled to only serve Piwigo. 
        # For multi-client use, we should store and check nonces in the DB.
        return False

    def generate_user_info(self, user, scope):
        user_info = {
            "sub": str(user.id),
            "preferred_username": user.prenom,
            "email": user.email,
        }

        user_info["name"] = f"{user.prenom} {user.nom}"
        
        groups = []
        if hasattr(user, 'promo') and user.promo:
            groups.append(str(user.promo))
            
        user_info["groups"] = groups
        return user_info


def config_oauth(app):
    server.init_app(app, query_client=query_client, save_token=save_token)
    server.register_grant(AuthorizationCodeGrant, [OpenIDCode(require_nonce=False)])
