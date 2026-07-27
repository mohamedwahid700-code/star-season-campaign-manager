"""
Bottom status bar component.

Shows a short status message (updated via `set_status`) plus static
build metadata (app version, current sprint). Kept intentionally
simple in Sprint 1; a later sprint may add a live queue/progress
indicator here for in-flight campaign sends.
"""

from __future__ import annotations

import customtkinter as ctk

from app import __sprint__, __version__
from app.ui.theme.theme_manager import ThemeManager


class StatusBar(ctk.CTkFrame):
    HEIGHT = 28

    def __init__(self, master: ctk.CTkBaseClass, theme_manager: ThemeManager) -> None:
        self._theme = theme_manager
        super().__init__(master, height=self.HEIGHT, corner_radius=0, fg_color=theme_manager.color("surface_alt"))
        self.grid_propagate(False)
        self.columnconfigure(0, weight=1)

        self._status_label = ctk.CTkLabel(
            self,
            text="Ready",
            font=ctk.CTkFont(size=11),
            text_color=self._theme.color("text_secondary"),
            anchor="w",
        )
        self._status_label.grid(row=0, column=0, sticky="w", padx=16)

        ctk.CTkLabel(
            self,
            text=f"v{__version__} · {__sprint__}",
            font=ctk.CTkFont(size=11),
            text_color=self._theme.color("text_secondary"),
            anchor="e",
        ).grid(row=0, column=1, sticky="e", padx=16)

    def set_status(self, message: str) -> None:
        self._status_label.configure(text=message)
