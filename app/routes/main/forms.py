"""PC est magique - Main Pages Forms"""

import wtforms
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from discord_webhook import DiscordEmbed

from app.utils.validators import DataRequired, Optional, Email, NumberRange


class ContactForm(FlaskForm):
    """WTForm used to send a contact request to Discord."""

    name = wtforms.StringField(_l("Nom"), validators=[DataRequired()])
    email = wtforms.EmailField(_l("Adresse e-mail (optionnel)"), validators=[Optional(), Email()])
    title = wtforms.StringField(_l("Titre"), validators=[DataRequired()])
    message = wtforms.TextAreaField(_l("Message"), validators=[DataRequired()])
    submit = wtforms.SubmitField(_l("Envoyer"))

    def create_embed(self) -> DiscordEmbed:
        """Create a Discord embed describing the contact request."""
        embed = DiscordEmbed(title=self.title.data, description=self.message.data, color="64b9e9")
        embed.set_author(name=self.name.data)
        embed.set_footer(text="Formulaire de contact PC est magique")
        embed.add_embed_field(name="E-mail :", value=self.email.data or "*Non renseigné*")
        embed.set_timestamp()
        return embed


from flask_wtf.file import FileField, FileAllowed


# Common Bootstrap icons for banners
BOOTSTRAP_ICONS = [
    ("", "— Aucune icône —"),
    ("megaphone-fill", "Mégaphone"),
    ("info-circle-fill", "Information"),
    ("exclamation-triangle-fill", "Avertissement"),
    ("exclamation-octagon-fill", "Alerte"),
    ("calendar-event-fill", "Événement"),
    ("music-note-beamed", "Musique"),
    ("cup-fill", "Bar"),
    ("receipt-cutoff", "Ticket"),
    ("star-fill", "Étoile"),
    ("gift-fill", "Cadeau"),
    ("people-fill", "Personnes"),
    ("award-fill", "Médaille"),
    ("house-fill", "Maison"),
    ("trophy-fill", "Trophée"),
    ("camera-fill", "Appareil photo"),
    ("pin-map-fill", "Carte"),
    ("heart-fill", "Cœur"),
    ("lightning-charge-fill", "Éclair"),
    ("bell-fill", "Cloche"),
    ("check-circle-fill", "Validé"),
    ("x-circle-fill", "Annulé"),
    ("lock-fill", "Verrou"),
    ("envelope-fill", "Email"),
    ("chat-fill", "Chat"),
    ("wrench", "Outils"),
    ("broadcast", "Diffusion"),
    ("file-earmark-text-fill", "Document"),
    ("bookmark-fill", "Signet"),
    ("tag-fill", "Étiquette"),
    ("patch-question-fill", "Question"),
]


class BannerStyleFormMixin:
    """Mixin for styling fields shared by preset and banner forms."""
    background_color = wtforms.StringField(_l("Couleur de fond (Hex)"), default="#152f4e")
    text_color = wtforms.StringField(_l("Couleur du texte (Hex)"), default="#ffffff")
    icon = wtforms.SelectField(_l("Icône"), choices=BOOTSTRAP_ICONS, validators=[Optional()])
    image_file = FileField(
        _l("Image de fond"),
        validators=[Optional(), FileAllowed(["png", "jpg", "jpeg", "gif", "webp"], _l("Images uniquement !"))],
    )
    text_alignment = wtforms.SelectField(
        _l("Alignement du texte"),
        choices=[("center", _l("Centré")), ("left", _l("Gauche")), ("right", _l("Droite"))],
        default="center",
    )
    layout_style = wtforms.SelectField(
        _l("Disposition"),
        choices=[("vertical", _l("Vertical (empilé)")), ("horizontal", _l("Horizontal (côte à côte)"))],
        default="vertical",
    )
    overlay_opacity = wtforms.IntegerField(
        _l("Opacité de l'overlay couleur (%)"),
        default=70,
        validators=[Optional(), NumberRange(min=0, max=100)],
    )


class PresetForm(FlaskForm, BannerStyleFormMixin):
    """Form to create or edit a banner style preset."""

    id = wtforms.HiddenField("id")
    name = wtforms.StringField(_l("Nom du preset"), validators=[DataRequired()])
    submit = wtforms.SubmitField(_l("Enregistrer le preset"))

class BannerForm(FlaskForm, BannerStyleFormMixin):
    """Form to add or edit a home page banner."""

    id = wtforms.HiddenField("id")
    title = wtforms.StringField(_l("Titre / Label admin"), validators=[DataRequired()])
    is_text = wtforms.BooleanField(_l("Bannière Textuelle"), default=False)
    text_content = wtforms.TextAreaField(_l("Texte de l'annonce"), validators=[Optional()])
    link_url = wtforms.URLField(_l("Lien de redirection"), validators=[Optional()])
    attached_file = FileField(_l("Fichier joint"), validators=[Optional()])
    preset_id = wtforms.SelectField(_l("Preset de style"), coerce=lambda x: int(x) if x and str(x).isdigit() else None, choices=[], validators=[Optional()])
    submit = wtforms.SubmitField(_l("Enregistrer"))


class CarouselConfigForm(FlaskForm):
    """Form to configure the global carousel settings."""

    autoplay_delay = wtforms.IntegerField(_l("Délai de défilement (secondes)"), validators=[wtforms.validators.DataRequired(), wtforms.validators.NumberRange(min=2, max=60)])
    submit = wtforms.SubmitField(_l("Enregistrer les réglages"))
