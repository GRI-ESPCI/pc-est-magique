import time

from authlib.integrations.sqla_oauth2 import (
    OAuth2ClientMixin,
    OAuth2AuthorizationCodeMixin,
    OAuth2TokenMixin,
)

from app import db
from app.models import Model


class OAuth2Client(Model, OAuth2ClientMixin):
    __tablename__ = "oauth2_client"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("pceen.id", ondelete="CASCADE")
    )
    user = db.relationship("PCeen", backref=db.backref("oauth2_clients", cascade="all, delete-orphan"))


class OAuth2AuthorizationCode(Model, OAuth2AuthorizationCodeMixin):
    __tablename__ = "oauth2_code"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("pceen.id", ondelete="CASCADE")
    )
    user = db.relationship("PCeen")


class OAuth2Token(Model, OAuth2TokenMixin):
    __tablename__ = "oauth2_token"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("pceen.id", ondelete="CASCADE")
    )
    user = db.relationship("PCeen")

    def is_refresh_token_active(self):
        if self.revoked:
            return False
        # Refresh tokens are valid for twice the access token lifetime,
        # to give users time to re-authenticate without re-login.
        expires_at = self.issued_at + self.expires_in * 2
        return expires_at >= time.time()
