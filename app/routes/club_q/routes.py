"""PC est magique - Club Q Pages Routes"""

import flask
from flask_babel import _

from app import context, db
from app.models import ClubQSeason, ClubQSalle, ClubQSpectacle, ClubQVoeux
from app.routes.club_q import bp, forms
from app.utils import helpers, typing



@bp.route("", methods=["GET", "POST"])
@bp.route("/", methods=["GET", "POST"])
def main() -> typing.RouteReturn:
    """PC est magique Club Q page."""
    form = forms.ClubQForm()
    season_id = 0  # ID of the season to show
    spectacles = ClubQSpectacle.query.filter_by(_season_id=season_id).order_by(ClubQSpectacle.id).all()
    if form.validate_on_submit():
        for spect in spectacles:
            if form.priorite.data:
                voeux = ClubQVoeux.query.filter_by(_spectacle_id=spect.id, _client_id=context.g.pceen.id, _season_id=spect._season_id).first()
                if not voeux:
                    voeux = ClubQVoeux(_spectacle_id=spect.id, _client_id=context.g.pceen.id, _season_id=spect._season_id)
                    db.session.add(voeux)
                voeux.priorite = form.priorite.data
                voeux.places_demandees = form.nb_places.data
                voeux.places_minimum = form.nb_places_minimum.data or None

        
        db.session.commit()
        flask.flash(_("Vos choix ont été enregistrés."))    
    return flask.render_template("club_q/main.html", title=_("Club Q"), form=form, spectacles=spectacles)

