import wtforms

from markupsafe import Markup

class MarkdownWidget(wtforms.widgets.TextArea):

    def __call__(self, field, **kwargs):
        kwargs.setdefault("style", "display: none;")
        html = super().__call__(field, **kwargs)

        return Markup(
            f"<div id='cm-editor-{field.id}'></div>"
        ) + html
