"""PC est magique - Main Pages Forms"""

import wtforms
from wtforms.fields import html5
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from discord_webhook import DiscordEmbed

from app.tools.validators import DataRequired, Optional, Email


class ContactForm(FlaskForm):
    """WTForm used to send a contact request to Discord."""

    name = wtforms.StringField(_l("Nom"), validators=[DataRequired()])
    email = html5.EmailField(
        _l("Adresse e-mail (optionnel)"), validators=[Optional(), Email()]
    )
    title = wtforms.StringField(_l("Titre"), validators=[DataRequired()])
    message = wtforms.TextAreaField(_l("Message"), validators=[DataRequired()])
    submit = wtforms.SubmitField(_l("Envoyer"))

    def create_embed(self) -> DiscordEmbed:
        """Create a Discord embed describing the contact request."""
        embed = DiscordEmbed(
            title=self.title.data, description=self.message.data, color="64b9e9"
        )
        embed.set_author(name=self.name.data)
        embed.set_footer(text="Formulaire de contact PC est magique")
        embed.add_embed_field(
            name="E-mail :", value=self.email.data or "*Non renseigné*"
        )
        embed.set_timestamp()
        return embed
