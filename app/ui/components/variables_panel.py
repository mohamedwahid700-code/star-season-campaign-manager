"""
Variables side panel component.

Lists every available `{Variable}` token next to the HTML editor in the
Campaign and Template dialogs. Clicking a token inserts it at the
editor's current cursor position via the `on_insert` callback.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.ui.theme.theme_manager import ThemeManager


def build_variables_panel(
    parent: ctk.CTkBaseClass,
    theme: ThemeManager,
    variables: list[tuple[str, str]],
    on_insert: Callable[[str], None],
) -> ctk.CTkFrame:
    """Build and return a panel listing `(token, description)` pairs as
    clickable buttons that call `on_insert(token)`."""
    panel = ctk.CTkFrame(parent, fg_color=theme.color("surface"), corner_radius=8)
    panel.columnconfigure(0, weight=1)

    ctk.CTkLabel(
        panel,
        text="Variables",
        font=ctk.CTkFont(size=13, weight="bold"),
        text_color=theme.color("text_primary"),
        anchor="w",
    ).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 4))

    ctk.CTkLabel(
        panel,
        text="Click to insert at cursor",
        font=ctk.CTkFont(size=11),
        text_color=theme.color("text_secondary"),
        anchor="w",
    ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))

    for position, (token, description) in enumerate(variables):
        row = 2 + (position * 2)
        button = ctk.CTkButton(
            panel,
            text=token,
            anchor="w",
            height=30,
            corner_radius=6,
            fg_color=theme.color("surface_alt"),
            hover_color=theme.color("border"),
            text_color=theme.color("text_primary"),
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda t=token: on_insert(t),
        )
        button.grid(row=row, column=0, sticky="ew", padx=12, pady=3)

        ctk.CTkLabel(
            panel,
            text=description,
            font=ctk.CTkFont(size=10),
            text_color=theme.color("text_secondary"),
            anchor="w",
            wraplength=170,
            justify="left",
        ).grid(row=row + 1, column=0, sticky="w", padx=12, pady=(0, 6))

    return panel
