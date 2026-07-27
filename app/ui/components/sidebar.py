"""
Sidebar navigation component.

Renders one button per entry in `NAVIGATION_ORDER` and delegates all
routing state to `NavigationController`. The sidebar has no knowledge
of which view class backs each key -- that mapping lives in
`MainWindow` -- so new pages only require an entry in
`app/config/constants.py` plus a view class, not a sidebar change.
"""

from __future__ import annotations

import customtkinter as ctk
from PIL import Image

from app.config.constants import NAVIGATION_LABELS, NAVIGATION_ORDER, NavigationKey
from app.controllers.navigation_controller import NavigationController
from app.ui.theme.theme_manager import ThemeManager
from app.utils.paths import get_icon_path


class Sidebar(ctk.CTkFrame):
    WIDTH = 220

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        navigation_controller: NavigationController,
        theme_manager: ThemeManager,
        app_name: str,
    ) -> None:
        self._navigation_controller = navigation_controller
        self._theme = theme_manager
        self._buttons: dict[NavigationKey, ctk.CTkButton] = {}

        super().__init__(
            master,
            width=self.WIDTH,
            corner_radius=0,
            fg_color=theme_manager.color("surface"),
            border_width=0,
        )
        self.grid_propagate(False)
        self.columnconfigure(0, weight=1)

        self._build_brand(app_name)
        self._build_nav_buttons()

        navigation_controller.subscribe(self._on_navigation_changed)
        self._on_navigation_changed(navigation_controller.current_key)

    def _build_brand(self, app_name: str) -> None:
        brand_frame = ctk.CTkFrame(self, fg_color="transparent", height=64)
        brand_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(24, 12))
        brand_frame.grid_propagate(False)
        brand_frame.columnconfigure(1, weight=1)

        self._build_brand_icon(brand_frame)

        text_frame = ctk.CTkFrame(brand_frame, fg_color="transparent")
        text_frame.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            text_frame,
            text="Star Season",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=self._theme.color("primary"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            text_frame,
            text="Campaign Manager",
            font=ctk.CTkFont(size=11),
            text_color=self._theme.color("text_secondary"),
            anchor="w",
        ).grid(row=1, column=0, sticky="w")

    def _build_brand_icon(self, brand_frame: ctk.CTkFrame) -> None:
        icon_path = get_icon_path("app_icon.png")
        if not icon_path.exists():
            return
        try:
            image = Image.open(icon_path)
            logo_image = ctk.CTkImage(light_image=image, dark_image=image, size=(36, 36))
            ctk.CTkLabel(brand_frame, image=logo_image, text="").grid(
                row=0, column=0, sticky="w", padx=(0, 10)
            )
        except Exception:  # noqa: BLE001 - the icon is decorative; never break the sidebar over it
            pass

    def _build_nav_buttons(self) -> None:
        nav_container = ctk.CTkFrame(self, fg_color="transparent")
        nav_container.grid(row=1, column=0, sticky="new", padx=12, pady=(8, 0))
        nav_container.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        for index, key in enumerate(NAVIGATION_ORDER):
            button = ctk.CTkButton(
                nav_container,
                text=NAVIGATION_LABELS[key],
                anchor="w",
                height=40,
                corner_radius=8,
                fg_color="transparent",
                text_color=self._theme.color("text_secondary"),
                hover_color=self._theme.color("surface_alt"),
                command=lambda k=key: self._navigation_controller.navigate_to(k),
            )
            button.grid(row=index, column=0, sticky="ew", pady=3)
            self._buttons[key] = button

    def _on_navigation_changed(self, active_key: NavigationKey) -> None:
        for key, button in self._buttons.items():
            if key == active_key:
                button.configure(
                    fg_color=self._theme.color("primary_soft"),
                    text_color=self._theme.color("text_primary"),
                )
            else:
                button.configure(
                    fg_color="transparent",
                    text_color=self._theme.color("text_secondary"),
                )
