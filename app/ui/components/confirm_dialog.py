"""
Confirmation dialog component.

A small modal used before any destructive or hard-to-reverse action
(delete contact, delete campaign, delete template). Blocks interaction
with the rest of the app until the user picks Confirm or Cancel via
`grab_set()`, and reports the result back through a callback rather
than a return value, since CTkToplevel windows are shown asynchronously
by the Tk event loop.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.ui.dialogs.base_dialog import activate_grab, apply_screen_aware_geometry
from app.ui.theme.theme_manager import ThemeManager


class ConfirmDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        theme_manager: ThemeManager,
        title: str,
        message: str,
        on_confirm: Callable[[], None],
        confirm_text: str = "Delete",
        danger: bool = True,
    ) -> None:
        super().__init__(master, fg_color=theme_manager.color("surface"))
        self._theme = theme_manager
        self._on_confirm = on_confirm

        self.title(title)
        self.transient(master)
        apply_screen_aware_geometry(
            self, preferred_width=420, preferred_height=180, min_width=340, min_height=160
        )

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        container.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            container,
            text=message,
            font=ctk.CTkFont(size=13),
            text_color=theme_manager.color("text_primary"),
            wraplength=370,
            justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(0, 20))

        button_row = ctk.CTkFrame(container, fg_color="transparent")
        button_row.grid(row=1, column=0, sticky="e")

        ctk.CTkButton(
            button_row,
            text="Cancel",
            width=100,
            height=34,
            fg_color=theme_manager.color("surface_alt"),
            hover_color=theme_manager.color("border"),
            text_color=theme_manager.color("text_primary"),
            command=self.destroy,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            button_row,
            text=confirm_text,
            width=100,
            height=34,
            fg_color=theme_manager.color("danger") if danger else theme_manager.color("primary"),
            hover_color=theme_manager.color("danger") if danger else theme_manager.color("primary_hover"),
            text_color="#FFFFFF" if danger else theme_manager.color("text_on_primary"),
            command=self._handle_confirm,
        ).pack(side="left")

        # Grab focus after the window is actually mapped, otherwise
        # grab_set() can raise on some window managers.
        self.after(50, self._activate_grab)

    def _activate_grab(self) -> None:
        activate_grab(self)

    def _handle_confirm(self) -> None:
        self.destroy()
        self._on_confirm()


def ask_confirm(
    master: ctk.CTkBaseClass,
    theme_manager: ThemeManager,
    title: str,
    message: str,
    on_confirm: Callable[[], None],
    confirm_text: str = "Delete",
    danger: bool = True,
) -> None:
    """Convenience wrapper so callers don't need to import the class directly."""
    ConfirmDialog(master, theme_manager, title, message, on_confirm, confirm_text, danger)
