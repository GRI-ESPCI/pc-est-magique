"""PC est magique - Club Q Pages Routes"""

import flask
from flask_babel import _

from app import context, db
from app.models import ClubQSpectacle, ClubQVoeux, PermissionScope, PermissionType
from app.routes.club_q import bp, forms
from app.utils import typing
from app.utils.validators import Optional

import wtforms


@bp.route("", methods=["GET", "POST"])
@bp.route("/", methods=["GET", "POST"])
@context.permission_only(PermissionType.read, PermissionScope.club_q)
def main() -> typing.RouteReturn:
    """PC est magique Club Q page."""

    #Ajout dynamique de 1 form par spectacle de la saison
    season_id = 0  # ID of the season to show
    spectacles = ClubQSpectacle.query.filter_by(_season_id=season_id).order_by(ClubQSpectacle.date).all()
    for spect in spectacles:
        setattr(forms.ClubQForm, f"priorite_{spect.id}", wtforms.IntegerField(('Priorité'),render_kw={"class": "form-control"}, validators=[Optional()]))
        setattr(forms.ClubQForm, f"nb_places_{spect.id}", wtforms.IntegerField(('Nombre places demandées'), render_kw={"class": "form-control"}, validators=[Optional()]))
        setattr(forms.ClubQForm, f"nb_places_minimum_{spect.id}", wtforms.IntegerField(('Nombre places minimum demandées'), render_kw={"class": "form-control"}, validators=[Optional()]))

    #Gestion des requêtes
    form = forms.ClubQForm()
    if form.validate_on_submit():
        for spect in spectacles:
            if form[f"priorite_{spect.id}"].data:
                voeux = ClubQVoeux.query.filter_by(_spectacle_id=spect.id, _client_id=context.g.pceen.id, _season_id=spect._season_id).first()
                if not voeux:
                    voeux = ClubQVoeux(_spectacle_id=spect.id, _client_id=context.g.pceen.id, _season_id=spect._season_id)
                    db.session.add(voeux)
                voeux.priorite = form[f"priorite_{spect.id}"].data
                voeux.places_demandees = form[f"nb_places_{spect.id}"].data
                voeux.places_minimum = form[f"nb_places_minimum_{spect.id}"].data or None

        
        db.session.commit()
        flask.flash(_("Vos choix ont été enregistrés."))    
    return flask.render_template("club_q/main.html", title=_("Page de réservation pour le Club Q"), form=form, spectacles=spectacles)

