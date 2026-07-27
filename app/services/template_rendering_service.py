"""
Template variable rendering service.

Replaces mail-merge style tokens (`{Company}`, `{EventName}`, ...) in an
HTML body with real values, so a Template or Campaign can be previewed
"exactly as the recipient will receive it".

Design note -- why plain regex substitution instead of Jinja2:
Jinja2 is part of this project's tech stack, but its default delimiters
(`{{ }}`) don't match the single-brace `{Variable}` syntax specified for
this feature, and reconfiguring Jinja2 to use single braces as
delimiters is unsafe here: campaign HTML bodies routinely contain
inline CSS (e.g. `<div style="margin:{0}">`-style curly braces in
`<style>` blocks), which a single-brace Jinja environment would try to
parse as template expressions and fail on. A small, whitelisted regex
substitution -- matching only `{Word}` sequences that exactly match a
known `TemplateVariable` -- achieves the same mail-merge behavior
without that risk, and is easier to reason about for a fixed, small set
of tokens. Jinja2 remains available for a future sprint that composes a
full email around a layout (header/footer), which is a better fit for
its templating model.
"""

from __future__ import annotations

import getpass
import re

from app.config.constants import TEMPLATE_VARIABLE_DESCRIPTIONS, TemplateVariable
from app.models.campaign import Campaign
from app.models.contact import Contact

_TOKEN_PATTERN = re.compile(r"\{(" + "|".join(re.escape(v.value) for v in TemplateVariable) + r")\}")


class TemplateRenderingService:
    def available_variables(self) -> list[tuple[str, str]]:
        """Return `(token, description)` pairs for the variables side panel."""
        return [
            (f"{{{variable.value}}}", TEMPLATE_VARIABLE_DESCRIPTIONS[variable])
            for variable in TemplateVariable
        ]

    def build_context(self, contact: Contact | None, campaign: Campaign | None = None) -> dict[str, str]:
        """
        Build the token -> value mapping for a given contact (and, optionally,
        the campaign it's being previewed for).

        `{WhatsApp}` and `{Country}`/`{Website}`/`{Stand}`/`{ContactName}`/
        `{Company}` all come straight from the selected contact.
        `{EventName}` comes from the campaign, since an event name belongs
        to the campaign, not the recipient. `{SenderName}` uses the current
        Windows/OS user as a reasonable stand-in for "who is sending this",
        matching what the top bar already displays as the current user.
        """
        contact = contact
        return {
            TemplateVariable.COMPANY.value: (contact.company if contact else None) or "",
            TemplateVariable.EVENT_NAME.value: (campaign.event_name if campaign else None) or "",
            TemplateVariable.WEBSITE.value: (contact.website if contact else None) or "",
            TemplateVariable.COUNTRY.value: (contact.country if contact else None) or "",
            TemplateVariable.STAND.value: (contact.stand_number if contact else None) or "",
            TemplateVariable.CONTACT_NAME.value: (contact.contact_name if contact else None) or "",
            TemplateVariable.SENDER_NAME.value: getpass.getuser(),
            TemplateVariable.WHATSAPP.value: (contact.phone if contact else None) or "",
        }

    def render(self, html: str, contact: Contact | None, campaign: Campaign | None = None) -> str:
        """Replace every recognized `{Variable}` token in `html` with a real value."""
        context = self.build_context(contact, campaign)

        def _replace(match: re.Match) -> str:
            token_name = match.group(1)
            return context.get(token_name, match.group(0))

        return _TOKEN_PATTERN.sub(_replace, html)
