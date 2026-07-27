"""About view.

Displays static application and company metadata, including the
official Star Season logo. Version information is pulled from
`app/__init__.py` so it only ever needs to be bumped in one place per
release.
"""

from __future__ import annotations

import customtkinter as ctk
from PIL import Image

from app import __app_name__, __company__, __sprint__, __version__
from app.ui.views.base_view import BaseView
from app.utils.paths import get_image_path


class AboutView(BaseView):
    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, title="About", subtitle=None)

    def build_content(self) -> None:
        card = ctk.CTkFrame(
            self.content,
            fg_color=self.theme.color("surface"),
            corner_radius=12,
            border_width=1,
            border_color=self.theme.color("border"),
        )
        card.grid(row=0, column=0, sticky="ew")
        card.columnconfigure(0, weight=1)

        self._build_logo(card)

        ctk.CTkLabel(
            card,
            text=__app_name__,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=self.theme.color("text_primary"),
        ).grid(row=1, column=0, sticky="w", padx=32, pady=(20, 4))

        ctk.CTkLabel(
            card,
            text=f"Version {__version__}  •  {__sprint__}",
            font=ctk.CTkFont(size=13),
            text_color=self.theme.color("text_secondary"),
        ).grid(row=2, column=0, sticky="w", padx=32, pady=(0, 20))

        ctk.CTkLabel(
            card,
            text=(
                "Star Season Campaign Manager helps Star Season plan, build, "
                "and track Outlook email campaigns for exhibition and "
                "conference participants across Saudi Arabia, the UAE, and "
                "Egypt."
            ),
            font=ctk.CTkFont(size=13),
            text_color=self.theme.color("text_primary"),
            wraplength=560,
            justify="left",
        ).grid(row=3, column=0, sticky="w", padx=32, pady=(0, 24))

        divider = ctk.CTkFrame(card, fg_color=self.theme.color("divider"), height=1)
        divider.grid(row=4, column=0, sticky="ew", padx=32)

        ctk.CTkLabel(
            card,
            text=f"© {__company__}",
            font=ctk.CTkFont(size=12),
            text_color=self.theme.color("text_secondary"),
        ).grid(row=5, column=0, sticky="w", padx=32, pady=(16, 32))

    def _build_logo(self, card: ctk.CTkFrame) -> None:
        logo_path = get_image_path("star_season_logo_full.png")
        if not logo_path.exists():
            return

        try:
            image = Image.open(logo_path)
            max_width = 320
            ratio = min(max_width / image.width, 1.0)
            display_size = (int(image.width * ratio), int(image.height * ratio))
            logo_image = ctk.CTkImage(light_image=image, dark_image=image, size=display_size)

            ctk.CTkLabel(card, image=logo_image, text="").grid(
                row=0, column=0, sticky="w", padx=32, pady=(28, 0)
            )
        except Exception:  # noqa: BLE001 - the logo is decorative; never break the About page over it
            pass
