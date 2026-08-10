from flask import Blueprint, request, current_app, jsonify, redirect, url_for
from flask_login import current_user
from authlib.integrations.flask_oauth2 import ResourceProtector as FlaskResourceProtector
from authlib.jose import JsonWebKey
from authlib.oauth2.rfc6750 import BearerTokenValidator
from cryptography.hazmat.primitives import serialization

from app.oauth2 import server, OpenIDCode
from app.models.oidc import OAuth2Token

bp = Blueprint("oidc", __name__)


@bp.route('/authorize', methods=['GET', 'POST'])
def authorize():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login', next=request.full_path))

    if request.method == 'GET':
        try:
            grant = server.get_consent_grant(end_user=current_user)
        except Exception as e:
            return str(e), 400
        # Auto-approve if the user is already authenticated on pc-est-magique
        return server.create_authorization_response(grant_user=current_user)

    grant_user = current_user
    return server.create_authorization_response(grant_user=grant_user)


@bp.route('/token', methods=['POST'])
def issue_token():
    return server.create_token_response()


@bp.route('/jwks')
def jwks():
    """Expose the RSA public key as a JWK so Piwigo
    can verify ID token signatures."""
    key_pem = _load_private_key_pem()
    private_key = serialization.load_pem_private_key(key_pem.encode(), password=None)
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    jwk = JsonWebKey.import_key(public_pem, {"kty": "RSA", "use": "sig", "alg": "RS256"})
    return jsonify({"keys": [jwk.as_dict()]})


def _load_private_key_pem():
    """Read the RSA private key PEM."""
    import os
    key = current_app.config.get("OIDC_PRIVATE_KEY")
    if key:
        return key
    key_path = current_app.config.get("OIDC_RSA_KEY_PATH")
    if not key_path:
        key_path = os.path.join(current_app.root_path, '..', 'oidc_rsa.pem')
    with open(key_path, 'r') as f:
        return f.read()


class MyBearerTokenValidator(BearerTokenValidator):
    def authenticate_token(self, token_string):
        return OAuth2Token.query.filter_by(access_token=token_string).first()

require_oauth = FlaskResourceProtector()
require_oauth.register_token_validator(MyBearerTokenValidator())


@bp.route('/userinfo')
@require_oauth('openid profile')
def userinfo():
    token = require_oauth.acquire_token()
    user = token.user
    generator = OpenIDCode(require_nonce=False)
    return jsonify(generator.generate_user_info(user, token.scope))


@bp.record_once
def register_well_known(state):
    """Register the .well-known/openid-configuration route at the app root"""
    app = state.app

    def openid_configuration():
        issuer = app.config.get("OIDC_ISSUER", "https://pc-est-magique.fr")
        return jsonify({
            "issuer": issuer,
            "authorization_endpoint": f"{issuer}/auth/oidc/authorize",
            "token_endpoint": f"{issuer}/auth/oidc/token",
            "userinfo_endpoint": f"{issuer}/auth/oidc/userinfo",
            "jwks_uri": f"{issuer}/auth/oidc/jwks",
            "response_types_supported": ["code"],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["RS256"],
            "scopes_supported": ["openid", "profile", "email"],
            "grant_types_supported": ["authorization_code"],
            "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
            "claims_supported": ["sub", "preferred_username", "email", "name", "groups"],
        })

    app.add_url_rule(
        '/.well-known/openid-configuration',
        endpoint='oidc_openid_configuration',
        view_func=openid_configuration,
    )
