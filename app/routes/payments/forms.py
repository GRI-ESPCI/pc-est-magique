"""PC est magique - Payment Forms"""

import wtforms
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm

from app.utils.validators import Optional, PhoneNumber


class LydiaPaymentForm(FlaskForm):
    """WTForm used to get Lydia payment information."""

    phone = wtforms.TelField(
        _l("Numéro de téléphone associé à Lydia"),
        validators=[Optional(), PhoneNumber()],
    )
    submit_lydia = wtforms.SubmitField(_l("Envoyer une demande via Lydia"))
    submit_cb = wtforms.SubmitField(_l("Payer par carte bancaire"))