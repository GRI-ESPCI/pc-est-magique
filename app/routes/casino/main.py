"""PC est magique Flask App - Casino Routes"""

import datetime

import flask
from flask_babel import _

from app import context, db, models
from app.enums import PredictionStatus
from app.routes.casino import bp
from app.utils import typing
from flask_wtf import FlaskForm
from flask_babel import format_date
from sqlalchemy.orm import selectinload

@bp.route("/")
@bp.route("/index")
def index() -> typing.RouteReturn:
    """Casino dashboard: active and recent predictions, and coin claim."""
    predictions = models.Prediction.query.order_by(models.Prediction.status, models.Prediction.id.desc()).all()
    pceen = context.g.logged_in_user
    
    can_claim = pceen.can_claim_casino_coins
    next_claim_date_str = None
    if not can_claim:
        now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        if now.month == 12:
            next_claim_date = datetime.date(now.year + 1, 1, 1)
        else:
            next_claim_date = datetime.date(now.year, now.month + 1, 1)
        next_claim_date_str = format_date(next_claim_date, format="medium")
        
    now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    two_years_ago = now - datetime.timedelta(days=365 * 2)
    top_users = models.PCeen.query.options(
        selectinload(models.PCeen.casino_bets)
        .selectinload(models.Bet.option)
        .selectinload(models.PredictionOption.prediction)
    ).filter(
        models.PCeen.casino_bets.any(models.Bet.created_at >= two_years_ago)
    ).order_by(models.PCeen.total_casino_coins.desc()).limit(5).all()


    return flask.render_template(
        "casino/index.html", 
        title=_("Casino"), 
        predictions=predictions,
        can_claim=can_claim,
        next_claim_date_str=next_claim_date_str,
        top_users=top_users,
        form=FlaskForm()
    )

@bp.route("/claim", methods=["POST"])
def claim() -> typing.RouteReturn:
    """Claim monthly coins."""
    form = FlaskForm()
    if not form.validate():
        flask.abort(400)
    pceen = context.g.logged_in_user
    if pceen.can_claim_casino_coins:
        pceen.casino_coins = models.PCeen.casino_coins + 100
        pceen.last_casino_claim = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        db.session.commit()
        flask.flash(_("Vous avez récupéré vos 100 PC Coins mensuels !"), "success")
    else:
        flask.flash(_("Vous avez déjà récupéré vos PC Coins récemment."), "warning")
    return flask.redirect(flask.url_for("casino.index"))

@bp.route("/prediction/<int:id>", methods=["GET", "POST"])
def prediction(id: int) -> typing.RouteReturn:
    """View prediction details and place bet."""
    prediction = models.Prediction.query.options(
        selectinload(models.Prediction.options)
        .selectinload(models.PredictionOption.bets)
    ).get_or_404(id)
    pceen = context.g.logged_in_user
    
    form = FlaskForm()
    if form.validate_on_submit():
        if prediction.status != PredictionStatus.open:
            flask.flash(_("Les paris sont fermés pour cette prédiction."), "danger")
            return flask.redirect(flask.url_for("casino.prediction", id=prediction.id))
        action = flask.request.form.get("action", "bet")
        
        if action == "cancel":
            try:
                option_id = int(flask.request.form.get("option_id"))
            except (ValueError, TypeError):
                flask.flash(_("Données invalides."), "danger")
                return flask.redirect(flask.url_for("casino.prediction", id=prediction.id))
                
            option = models.PredictionOption.query.get(option_id)
            if not option or option._prediction_id != prediction.id:
                flask.flash(_("Option invalide."), "danger")
                return flask.redirect(flask.url_for("casino.prediction", id=prediction.id))
                
            bets_to_cancel = models.Bet.query.filter_by(_pceen_id=pceen.id, _option_id=option.id).all()
            if not bets_to_cancel:
                flask.flash(_("Aucune mise à annuler."), "warning")
                return flask.redirect(flask.url_for("casino.prediction", id=prediction.id))
                
            refund_amount = sum(b.amount for b in bets_to_cancel)
            for b in bets_to_cancel:
                db.session.delete(b)
            pceen.casino_coins = models.PCeen.casino_coins + refund_amount
            db.session.commit()
            
            flask.flash(_("Mise annulée. Vous avez récupéré %(amount)d PC Coins.", amount=refund_amount), "success")
            return flask.redirect(flask.url_for("casino.prediction", id=prediction.id))
            
        try:
            amount = int(flask.request.form.get("amount", 0))
            option_id = int(flask.request.form.get("option_id"))
        except (ValueError, TypeError):
            flask.flash(_("Données invalides."), "danger")
            return flask.redirect(flask.url_for("casino.prediction", id=prediction.id))
            
        if amount <= 0:
            flask.flash(_("Le montant doit être strictement positif."), "danger")
            return flask.redirect(flask.url_for("casino.prediction", id=prediction.id))
            
        if pceen.casino_coins < amount:
            flask.flash(_("Vous n'avez pas assez de PC Coins."), "danger")
            return flask.redirect(flask.url_for("casino.prediction", id=prediction.id))
            
        option = models.PredictionOption.query.get(option_id)
        if not option or option._prediction_id != prediction.id:
            flask.flash(_("Option invalide."), "danger")
            return flask.redirect(flask.url_for("casino.prediction", id=prediction.id))
            
        bet = models.Bet(pceen=pceen, option=option, amount=amount)
        pceen.casino_coins = models.PCeen.casino_coins - amount
        db.session.add(bet)
        db.session.commit()
        flask.flash(_("Pari de %(amount)d PC Coins enregistré !", amount=amount), "success")
        return flask.redirect(flask.url_for("casino.prediction", id=prediction.id))
        
    user_bets = {}
    total_pool = 0
    for option in prediction.options:
        user_bets[option.id] = sum(b.amount for b in option.bets if b._pceen_id == pceen.id)
        total_pool += sum(b.amount for b in option.bets)


    return flask.render_template(
        "casino/prediction.html",
        title=prediction.name,
        prediction=prediction,
        user_bets=user_bets,
        total_pool=total_pool,
        form=FlaskForm()
    )

@bp.route("/leaderboard")
def leaderboard() -> typing.RouteReturn:
    """Casino full leaderboard."""
    now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    two_years_ago = now - datetime.timedelta(days=365 * 2)
    users = models.PCeen.query.options(
        selectinload(models.PCeen.casino_bets)
        .selectinload(models.Bet.option)
        .selectinload(models.PredictionOption.prediction)
    ).filter(
        models.PCeen.casino_bets.any(models.Bet.created_at >= two_years_ago)
    ).order_by(models.PCeen.total_casino_coins.desc()).all()
    
    return flask.render_template(
        "casino/leaderboard.html",
        title=_("Classement du Casino"),
        users=users,
    )
