"""PC est magique - Profile Pages Routes"""

import flask
from flask_babel import _

from app import context, db
from app.routes.profile import bp, forms
from app.utils import helpers, typing


@bp.route("/")
@context.intrarez_setup_only
def main() -> typing.RouteReturn:
    """PC est magique profile page."""
    return flask.render_template("profile/main.html", title=_("Profil"))


@bp.route("/modify_account", methods=["GET", "POST"])
@context.intrarez_setup_only
def modify_account() -> typing.RouteReturn:
    """PC est magique account modification page."""
    form = forms.AccountModificationForm()
    if form.validate_on_submit():
        pceen = flask.g.pceen
        pceen.nom = form.nom.data.title()
        pceen.prenom = form.prenom.data.title()
        pceen.promo = form.promo.data
        pceen.email = form.email.data
        db.session.commit()
        helpers.log_action(
            f"Modified account {pceen} ({pceen.prenom} {pceen.nom} "
            f"{pceen.promo}, {pceen.email})"
        )
        flask.flash(_("Compte modifié avec succès !"), "success")
        return helpers.redirect_to_next()

    return flask.render_template(
        "profile/modify_account.html", title=_("Mettre à jour mon compte"), form=form
    )


@bp.route("/update_password", methods=["GET", "POST"])
@context.intrarez_setup_only
def update_password() -> typing.RouteReturn:
    """PC est magique password update page."""
    form = forms.PasswordUpdateForm()
    if form.validate_on_submit():
        if flask.g.pceen.check_password(form.current_password.data):
            flask.g.pceen.set_password(form.password.data)
            db.session.commit()
            helpers.log_action(f"Updated password of {flask.g.pceen}")
            flask.flash(_("Mot de passe mis à jour !"), "success")
            return helpers.redirect_to_next()
        else:
            flask.flash(_("Mot de passe actuel incorrect"), "danger")

    return flask.render_template(
        "profile/update_password.html", title=_("Modifier mon mot de passe"), form=form
    )
