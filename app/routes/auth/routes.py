"""PC est magique - Authentication Routes"""

import flask
import flask_login
from flask_babel import _

from app import context, db
from app.routes.auth import bp, forms, email
from app.models import PCeen
from app.routes.auth.utils import new_username, grant_rezident_role
from app.utils import helpers, typing


@bp.route("/auth_needed")
def auth_needed() -> typing.RouteReturn:
    """Authentification needed page."""
    return flask.render_template("auth/auth_needed.html", title=_("Connexion nécessaire"))


@bp.route("/register")
def register() -> typing.RouteReturn:
    """PC est magique manual registration method choice page."""
    if context.g.logged_in:
        return helpers.redirect_to_next()

    return flask.render_template("auth/register.html", title=_("Nouveau compte"))


@bp.route("/register/rezident", methods=["GET", "POST"])
@context.internal_only
def register_rezident() -> typing.RouteReturn:
    """PC est magique Rezident registration page."""
    if context.g.logged_in:
        return helpers.redirect_to_next()

    form = forms.RegistrationForm()
    if form.validate_on_submit():
        pceen = PCeen(
            username=new_username(form.prenom.data, form.nom.data),
            nom=form.nom.data.title(),
            prenom=form.prenom.data.title(),
            promo=form.promo.data,
            email=form.email.data,
        )
        pceen.set_password(form.password.data)
        grant_rezident_role(pceen)
        db.session.add(pceen)
        db.session.commit()
        helpers.log_action(
            f"Internal -> Registered account {pceen!r} ({pceen.prenom} {pceen.nom} " f"{pceen.promo}, {pceen.email})"
        )
        flask.flash(_("Compte créé avec succès !"), "success")
        flask_login.login_user(pceen, remember=False)
        email.send_account_registered_email(pceen)
        return helpers.redirect_to_next()

    return flask.render_template("auth/register_rezident.html", title=_("Nouveau compte Rezident"), form=form)


@bp.route("/login", methods=["GET", "POST"])
def login() -> typing.RouteReturn:
    """PC est magique login page."""
    if context.g.logged_in:
        return helpers.redirect_to_next()

    form = forms.LoginForm()
    if form.validate_on_submit():
        # Check user / password
        pceen = (
            PCeen.query.filter_by(username=form.login.data).first()
            or PCeen.query.filter_by(email=form.login.data).first()
        )
        if pceen is None:
            flask.flash(_("Nom d'utilisateur inconnu"), "danger")
        elif not pceen.check_password(form.password.data):
            flask.flash(_("Mot de passe incorrect"), "danger")
        else:
            # OK
            flask_login.login_user(pceen, remember=form.remember_me.data)
            flask.flash(_("Connecté !"), "success")
            return helpers.redirect_to_next()

    return flask.render_template("auth/login.html", title=_("Connexion"), form=form)


@bp.route("/logout")
def logout() -> typing.RouteReturn:
    """PC est magique logout page."""
    if context.g.logged_in:
        flask_login.logout_user()
        context.g.logged_in = False
        context.g.logged_in_user = None
        context.g.pceen = None
        context.g.is_gri = False
        flask.flash(_("Vous avez été déconnecté."), "success")

    return helpers.redirect_to_next()


@bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request() -> typing.RouteReturn:
    """PC est magique password reset request page."""
    if context.g.logged_in:
        return helpers.redirect_to_next()

    form = forms.ResetPasswordRequestForm()
    if form.validate_on_submit():
        pceen = PCeen.query.filter_by(email=form.email.data).first()
        if pceen:
            email.send_password_reset_email(pceen)
        flask.flash(
            _(
                "Un email a été envoyé avec les instructions pour "
                "réinitialiser le mot de passe. Pensez à vérifier vos "
                "spams."
            ),
            "info",
        )
        return helpers.ensure_safe_redirect("auth.login")

    return flask.render_template("auth/reset_password_request.html", title=_("Mot de passe oublié"), form=form)


@bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token) -> typing.RouteReturn:
    """PC est magique password reset page (link sent by mail)."""
    if context.g.logged_in:
        flask.flash(_("Ce lien n'est pas utilisable en étant authentifié."), "warning")
        return helpers.redirect_to_next()

    pceen = PCeen.verify_reset_password_token(token)
    if not pceen:
        flask.flash(_("Lien de réinitialisation invalide ou expiré."), "danger")
        return helpers.redirect_to_next()

    form = forms.ResetPasswordForm()
    if form.validate_on_submit():
        pceen.set_password(form.password.data)
        db.session.commit()
        helpers.log_action(f"Reset password of {pceen!r}")
        flask.flash(_("Le mot de passe a été réinitialisé avec succès."), "success")
        return helpers.ensure_safe_redirect("auth.login")

    return flask.render_template("auth/reset_password.html", title=_("Nouveau mot de passe"), form=form)
