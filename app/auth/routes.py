"""PC est magique - Authentication Routes"""

import re

import flask
import flask_login
from flask_babel import _
import unidecode

from app import context, db
from app.auth import bp, forms, email
from app.models import PCeen
from app.tools import typing, utils


def new_username(prenom: str, nom: str) -> str:
    """Create a new pceen unique username from a forname and a name.

    Args:
        prenom: The pceen's forname.
        nom: The pceen's last name.

    Returns:
        The first non-existing corresponding username.
    """
    pnom = prenom.lower()[0] + nom.lower()[:7]
    # Exclude non-alphanumerics characters
    base_username = re.sub(r"\W", "", unidecode.unidecode(pnom), re.A)
    # Construct first non-existing username
    username = base_username
    discr = 1
    while PCeen.query.filter_by(username=username).first():
        username = f"{base_username}{discr}"
        discr += 1
    return username


@bp.route("/auth_needed")
def auth_needed() -> typing.RouteReturn:
    """Authentification needed page."""
    return flask.render_template("auth/auth_needed.html",
                                 title=_("Accès à Internet"))


@bp.route("/register", methods=["GET", "POST"])
def register() -> typing.RouteReturn:
    """PC est magique registration page."""
    if flask.g.logged_in:
        return utils.redirect_to_next()

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
        db.session.add(pceen)
        db.session.commit()
        utils.log_action(
            f"Registered account {pceen} ({pceen.prenom} {pceen.nom} "
            f"{pceen.promo}, {pceen.email})"
        )
        flask.flash(_("Compte créé avec succès !"), "success")
        flask_login.login_user(pceen, remember=False)
        email.send_account_registered_email(pceen)
        return utils.redirect_to_next()

    return flask.render_template("auth/register.html",
                                 title=_("Nouveau compte"), form=form)


@bp.route("/login", methods=["GET", "POST"])
def login() -> typing.RouteReturn:
    """PC est magique login page."""
    if flask.g.logged_in:
        return utils.redirect_to_next()

    form = forms.LoginForm()
    if form.validate_on_submit():
        # Check user / password
        pceen = (PCeen.query.filter_by(username=form.login.data).first()
                    or PCeen.query.filter_by(email=form.login.data).first())
        if pceen is None:
            flask.flash(_("Nom d'utilisateur inconnu"), "danger")
        elif not pceen.check_password(form.password.data):
            flask.flash(_("Mot de passe incorrect"), "danger")
        else:
            # OK
            flask_login.login_user(pceen, remember=form.remember_me.data)
            flask.flash(_("Connecté !"), "success")
            return utils.redirect_to_next()

    return flask.render_template("auth/login.html", title=_("Connexion"),
                                 form=form)


@bp.route("/logout")
def logout() -> typing.RouteReturn:
    """PC est magique logout page."""
    if flask.g.logged_in:
        flask_login.logout_user()
        flask.g.logged_in = False
        flask.g.logged_in_user = None
        flask.g.pceen = None
        flask.g.is_gri = False
        flask.flash(_("Vous avez été déconnecté."), "success")

    return utils.redirect_to_next()


@bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request() -> typing.RouteReturn:
    """PC est magique password reset request page."""
    if flask.g.logged_in:
        return utils.redirect_to_next()

    form = forms.ResetPasswordRequestForm()
    if form.validate_on_submit():
        pceen = PCeen.query.filter_by(email=form.email.data).first()
        if pceen:
            email.send_password_reset_email(pceen)
        flask.flash(_("Un email a été envoyé avec les instructions pour "
                      "réinitialiser le mot de passe. Pensez à vérifier vos "
                      "spams."), "info")
        return utils.ensure_safe_redirect("auth.login")

    return flask.render_template("auth/reset_password_request.html",
                                 title=_("Mot de passe oublié"), form=form)


@bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token) -> typing.RouteReturn:
    """PC est magique password reset page (link sent by mail)."""
    if flask.g.logged_in:
        flask.flash(_("Ce lien n'est pas utilisable en étant authentifié."),
                    "warning")
        return utils.redirect_to_next()

    pceen = PCeen.verify_reset_password_token(token)
    if not pceen:
        flask.flash(_("Lien de réinitialisation invalide ou expiré."),
                    "danger")
        return utils.redirect_to_next()

    form = forms.ResetPasswordForm()
    if form.validate_on_submit():
        pceen.set_password(form.password.data)
        db.session.commit()
        utils.log_action(f"Reset password of {pceen}")
        flask.flash(_("Le mot de passe a été réinitialisé avec succès."),
                    "success")
        return utils.ensure_safe_redirect("auth.login")

    return flask.render_template("auth/reset_password.html",
                                 title=_("Nouveau mot de passe"), form=form)