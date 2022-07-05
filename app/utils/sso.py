import flask
import flask_saml

from app import PCEstMagiqueApp


class SAML(flask_saml.FlaskSAML):
    def _get_metadata(self, metadata_url: str, metadata_fallback_url: str) -> str:
        try:
            return flask_saml._get_metadata(metadata_url)
        except RuntimeError:
            if not metadata_fallback_url:
                raise
            return flask_saml._get_metadata(metadata_fallback_url)

    def init_app(self, app: PCEstMagiqueApp):
        app.config["SAML_PREFIX"] = "/saml"
        app.config["SAML_DEFAULT_REDIRECT"] = "/"
        app.config["SAML_USE_SESSIONS"] = False

        config = {
            "metadata": self._get_metadata(
                app.config["SAML_METADATA_URL"],
                app.config["SAML_METADATA_FALLBACK_URL"],
            ),
            "prefix": app.config["SAML_PREFIX"],
            "default_redirect": app.config["SAML_DEFAULT_REDIRECT"],
        }

        saml_routes = {
            "logout": flask_saml.logout,
            "sso": flask_saml.login,
            "acs": flask_saml.login_acs,
            "metadata": flask_saml.metadata,
        }
        for route, func in saml_routes.items():
            app.add_url_rule(
                f"/saml/{route}",
                # endpoint=f"saml.{route}",
                view_func=func,
                methods=["GET", "POST"],
            )

        if not hasattr(app, "extensions"):
            app.extensions = {}
        app.extensions["saml"] = (self, config)

        @flask_saml.saml_authenticated.connect_via(app)
        def _session_login(sender, subject, attributes, auth):
            flask.session["saml"] = {
                "sender": sender,
                "subject": subject,
                "attributes": attributes,
                "auth": auth,
            }

        @flask_saml.saml_log_out.connect_via(app)
        def _session_logout(sender):
            flask.session["saml"] = {}

        @flask_saml.saml_error.connect_via(app)
        def on_saml_error(sender, exception):
            flask.flash(str(exception), "error")
