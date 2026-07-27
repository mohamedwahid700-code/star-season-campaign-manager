"""
Base view.

Every page (Dashboard, Campaigns, Contacts, ...) subclasses `BaseView`
so that page headers, padding, and theming stay consistent without each
page re-implementing them. Subclasses override `build_content()` to add
their own widgets below the standard header.

Theme changes are handled by fully destroying and rebuilding every view
(see `MainWindow._handle_theme_toggle`) rather than by each widget
patching its own colors in place -- CustomTkinter doesn't recolor
manually-set `fg_color`/`text_color` automatically, and trying to do so
widget-by-widget across a large, varied view tree is exactly how a
"mixed dark/light controls" bug creeps in. Rebuilding guarantees every
widget is constructed fresh against the current theme.
"""

from __future__ import annotations

import customtkinter as ctk

from app.ui.theme.theme_manager import ThemeManager, get_theme_manager


class BaseView(ctk.CTkFrame):
    """
    Common scaffold for a full-page view hosted in the main window's
    content area.

    Parameters
    ----------
    master:
        The parent widget (the main window's content container).
    title:
        Page title rendered in the header.
    subtitle:
        Optional one-line description rendered under the title.
    """

    def __init__(self, master: ctk.CTkBaseClass, title: str, subtitle: str | None = None) -> None:
        self.theme: ThemeManager = get_theme_manager()
        super().__init__(master, fg_color=self.theme.color("background"), corner_radius=0)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._header = self._build_header(title, subtitle)
        self._header.grid(row=0, column=0, sticky="ew", padx=32, pady=(28, 12))

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=1, column=0, sticky="nsew", padx=32, pady=(0, 28))
        self.content.columnconfigure(0, weight=1)

        self.build_content()

    def _build_header(self, title: str, subtitle: str | None) -> ctk.CTkFrame:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.theme.color("text_primary"),
            anchor="w",
        )
        title_label.grid(row=0, column=0, sticky="w")

        if subtitle:
            subtitle_label = ctk.CTkLabel(
                header,
                text=subtitle,
                font=ctk.CTkFont(size=13),
                text_color=self.theme.color("text_secondary"),
                anchor="w",
            )
            subtitle_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        return header

    def build_content(self) -> None:
        """Override in subclasses to populate `self.content`."""
        raise NotImplementedError

    def on_show(self) -> None:
        """Called by the navigation system every time this view becomes visible.

        No-op by default; subclasses override to refresh data on display.
        """
        return None
