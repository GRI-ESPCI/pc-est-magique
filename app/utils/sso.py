import flask
import flask_saml
import saml2
import saml2.client
import saml2.config
import saml2.entity
import saml2.metadata

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
        self.app = app

        app.config["SAML_PREFIX"] = "/saml"
        app.config["SAML_DEFAULT_REDIRECT"] = "/"
        app.config["SAML_USE_SESSIONS"] = False

        self.config = {
            "metadata": self._get_metadata(
                app.config["SAML_METADATA_URL"],
                app.config["SAML_METADATA_FALLBACK_URL"],
            ),
            "prefix": app.config["SAML_PREFIX"],
            "default_redirect": app.config["SAML_DEFAULT_REDIRECT"],
        }

        saml_routes = {
            "logout": self.logout,
            "sso": self.login,
            "acs": self.login_acs,
            "metadata": self.metadata,
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
        app.extensions["saml"] = (self, self.config)

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

    def _get_client(self):
        acs_url = flask.url_for("login_acs", _external=True)
        metadata_url = flask.url_for("metadata", _external=True)
        settings = {
            "entityid": metadata_url,
            "key_file": self.app.config["SAML_CERTIFICATE_PRIVATE_KEY_FILE"],
            "cert_file": self.app.config["SAML_CERTIFICATE_PUBLIC_KEY_FILE"],
            "encryption_keypairs": [
                {
                    "key_file": self.app.config["SAML_CERTIFICATE_PRIVATE_KEY_FILE"],
                    "cert_file": self.app.config["SAML_CERTIFICATE_PUBLIC_KEY_FILE"],
                }
            ],
            "generate_cert_info": True,
            "metadata": {"inline": [self.config["metadata"]]},
            "service": {
                "sp": {
                    "endpoints": {
                        "assertion_consumer_service": [
                            (acs_url, saml2.BINDING_HTTP_POST),
                        ],
                    },
                    "allow_unsolicited": True,
                },
            },
            "contact_person": [
                {
                    "given_name": "GRI Team -- BDE ESPCI Paris - PSL",
                    "email_address": ["pc-est-magique@pc-est-magique.fr"],
                    "type": "technical",
                },
            ],
        }
        config = saml2.config.Config()
        config.load(settings)
        config.allow_unknown_attributes = True
        client = saml2.client.Saml2Client(config=config)
        return client

    def logout(self):
        flask_saml.log.debug("Received logout request")
        flask_saml.saml_log_out.send(flask.current_app._get_current_object())
        url = flask.request.url_root[:-1] + self.config["default_redirect"]
        return flask.redirect(url)

    def login(self):
        flask_saml.log.debug("Received login request")
        return_url = flask_saml._get_return_to()
        saml_client = self._get_client()
        reqid, info = saml_client.prepare_for_authenticate(relay_state=return_url)
        headers = dict(info["headers"])
        response = flask.redirect(headers.pop("Location"), code=302)
        for name, value in headers.items():
            response.headers[name] = value
        response.headers["Cache-Control"] = "no-cache, no-store"
        response.headers["Pragma"] = "no-cache"
        return response

    def login_acs(self):
        if "SAMLResponse" not in flask.request.form:
            return "Missing SAMLResponse POST data", 500

        flask_saml.log.debug("Received SAMLResponse for login")
        try:
            saml_client = self._get_client()
            authn_response = saml_client.parse_authn_request_response(
                flask.request.form["SAMLResponse"],
                saml2.entity.BINDING_HTTP_POST,
            )
            if authn_response is None:
                raise RuntimeError("Unknown SAML error, please check logs")
        except Exception as exc:
            flask_saml.saml_error.send(
                flask.current_app._get_current_object(),
                exception=exc,
            )
        else:
            flask_saml.saml_authenticated.send(
                flask.current_app._get_current_object(),
                subject=authn_response.get_subject().text,
                attributes=authn_response.get_identity(),
                auth=authn_response,
            )
        relay_state = flask.request.form.get("RelayState")
        if not relay_state:
            relay_state = self.config["default_redirect"]
        redirect_to = relay_state
        if not relay_state.startswith(flask.request.url_root):
            redirect_to = flask.request.url_root[:-1] + redirect_to
        return flask.redirect(redirect_to)

    def metadata(self):
        saml_client = self._get_client()
        metadata_str = saml2.metadata.create_metadata_string(
            configfile=None,
            config=saml_client.config,
        )
        return metadata_str, {"Content-Type": "text/xml"}
