"""PC est magique Flask App - Casino Admin Routes"""

import flask
from flask_babel import _

from app import context, db, models
from app.enums import PredictionStatus
from app.routes.casino import bp
from app.utils import typing

from flask_wtf import FlaskForm

@bp.route("/admin")
def admin() -> typing.RouteReturn:
    """Casino admin dashboard."""
    predictions = models.Prediction.query.order_by(models.Prediction.id.desc()).all()
    return flask.render_template(
        "casino/admin/index.html",
        title=_("Gestion du Casino"),
        predictions=predictions,
        form=FlaskForm()
    )

@bp.route("/admin/create", methods=["GET", "POST"])
def admin_create() -> typing.RouteReturn:
    """Create a new prediction."""
    form = FlaskForm()
    if form.validate_on_submit():
        name = flask.request.form.get("name")
        description = flask.request.form.get("description")
        
        if not name:
            flask.flash(_("Le nom est obligatoire."), "danger")
            return flask.redirect(flask.url_for("casino.admin_create"))
            
        prediction = models.Prediction(
            name=name,
            description=description,
            author=context.g.logged_in_user,
            status=PredictionStatus.open
        )
        db.session.add(prediction)
        
        # Parse options
        option_names = flask.request.form.getlist("option_name[]")
        option_colors = flask.request.form.getlist("option_color[]")
        for i, opt_name in enumerate(option_names):
            if opt_name.strip():
                color = option_colors[i] if i < len(option_colors) else "#000000"
                db.session.add(models.PredictionOption(
                    prediction=prediction,
                    name=opt_name.strip(),
                    color=color
                ))
                
        db.session.commit()
        flask.flash(_("Prédiction créée avec succès."), "success")
        return flask.redirect(flask.url_for("casino.admin"))
        
    return flask.render_template(
        "casino/admin/create.html",
        form=form,
        title=_("Créer une prédiction")
    )

@bp.route("/admin/<int:id>/lock", methods=["POST"])
def admin_lock(id: int) -> typing.RouteReturn:
    """Lock a prediction."""
    form = FlaskForm()
    if not form.validate():
        flask.abort(400)
        
    prediction = models.Prediction.query.get_or_404(id)
    if prediction.status == PredictionStatus.open:
        prediction.status = PredictionStatus.locked
        db.session.commit()
        flask.flash(_("Prédiction verrouillée."), "success")
    return flask.redirect(flask.url_for("casino.admin"))

@bp.route("/admin/<int:id>/cancel", methods=["POST"])
def admin_cancel(id: int) -> typing.RouteReturn:
    """Cancel a prediction and refund."""
    form = FlaskForm()
    if not form.validate():
        flask.abort(400)
        
    prediction = models.Prediction.query.get_or_404(id)
    if prediction.status == PredictionStatus.resolved:
        flask.flash(_("Prédiction déjà résolue."), "danger")
        return flask.redirect(flask.url_for("casino.admin"))
        
    # Refund all bets
    for option in prediction.options:
        for bet in option.bets:
            bet.pceen.casino_coins = models.PCeen.casino_coins + bet.amount
            
    db.session.delete(prediction)
    db.session.commit()
    flask.flash(_("Prédiction annulée et paris remboursés."), "success")
    return flask.redirect(flask.url_for("casino.admin"))

@bp.route("/admin/<int:id>/resolve", methods=["POST"])
def admin_resolve(id: int) -> typing.RouteReturn:
    """Resolve a prediction and distribute coins."""
    form = FlaskForm()
    if not form.validate():
        flask.abort(400)
        
    prediction = models.Prediction.query.get_or_404(id)
    if prediction.status == PredictionStatus.resolved:
        flask.flash(_("Prédiction déjà résolue."), "danger")
        return flask.redirect(flask.url_for("casino.admin"))
        
    option_id = flask.request.form.get("option_id")
    if not option_id:
        flask.flash(_("Option invalide."), "danger")
        return flask.redirect(flask.url_for("casino.admin"))
        
    try:
        option_id_int = int(option_id)
    except (ValueError, TypeError):
        flask.flash(_("Option invalide."), "danger")
        return flask.redirect(flask.url_for("casino.admin"))
    
    winning_option = models.PredictionOption.query.get(option_id_int)
    if not winning_option or winning_option._prediction_id != prediction.id:
        flask.flash(_("Option invalide."), "danger")
        return flask.redirect(flask.url_for("casino.admin"))
        
    prediction.resolved_option = winning_option
    prediction.status = PredictionStatus.resolved
    
    # Calculate rewards
    total_pool = sum(bet.amount for opt in prediction.options for bet in opt.bets)
    winning_pool = sum(bet.amount for bet in winning_option.bets)
    
    if winning_pool > 0:
        for bet in winning_option.bets:
            reward = (bet.amount * total_pool) // winning_pool
            bet.pceen.casino_coins = models.PCeen.casino_coins + reward
            
    db.session.commit()
    flask.flash(_("Prédiction résolue, récompenses distribuées !"), "success")
    return flask.redirect(flask.url_for("casino.admin"))

@bp.route("/admin/<int:id>/delete", methods=["POST"])
def admin_delete(id: int) -> typing.RouteReturn:
    """Delete a resolved prediction to clear it from the UI."""
    form = FlaskForm()
    if not form.validate():
        flask.abort(400)
        
    prediction = models.Prediction.query.get_or_404(id)
    if prediction.status != PredictionStatus.resolved:
        flask.flash(_("Vous ne pouvez supprimer que les prédictions résolues."), "danger")
        return flask.redirect(flask.url_for("casino.admin"))
        
    db.session.delete(prediction)
    db.session.commit()
    flask.flash(_("Prédiction supprimée."), "success")
    return flask.redirect(flask.url_for("casino.admin"))
