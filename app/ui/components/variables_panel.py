"""
Variables side panel component.

Lists every available `{Variable}` token next to the HTML editor in the
Campaign and Template dialogs. Clicking a token inserts it at the
editor's current cursor position via the `on_insert` callback.

The token list itself lives inside a `CTkScrollableFrame` (with the
"Variables" heading pinned above it, outside the scroll area) so that
on smaller screens -- 1366x768 laptops in particular -- every merge
field stays reachable even when the full list doesn't fit the panel's
visible height, instead of silently clipping the bottom entries.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.ui.theme.theme_manager import ThemeManager

# Width of the panel, shared by both the fixed header and the scrollable
# body so their contents line up and the panel keeps a consistent
# footprint next to the HTML editor.
_PANEL_WIDTH = 210


def build_variables_panel(
    parent: ctk.CTkBaseClass,
    theme: ThemeManager,
    variables: list[tuple[str, str]],
    on_insert: Callable[[str], None],
) -> ctk.CTkFrame:
    """Build and return a panel listing `(token, description)` pairs as
    clickable buttons that call `on_insert(token)`. Scrolls internally
    once the token list is taller than the available space."""
    panel = ctk.CTkFrame(parent, fg_color=theme.color("surface"), corner_radius=8, width=_PANEL_WIDTH)
    panel.columnconfigure(0, weight=1)
    panel.rowconfigure(1, weight=1)
    panel.grid_propagate(False)

    header = ctk.CTkFrame(panel, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))
    header.columnconfigure(0, weight=1)

    ctk.CTkLabel(
        header,
        text="Variables",
        font=ctk.CTkFont(size=13, weight="bold"),
        text_color=theme.color("text_primary"),
        anchor="w",
    ).grid(row=0, column=0, sticky="w")

    ctk.CTkLabel(
        header,
        text="Click to insert at cursor",
        font=ctk.CTkFont(size=11),
        text_color=theme.color("text_secondary"),
        anchor="w",
    ).grid(row=1, column=0, sticky="w")

    scroll_area = ctk.CTkScrollableFrame(
        panel, fg_color="transparent", scrollbar_button_color=theme.color("border"),
        width=_PANEL_WIDTH - 20,
    )
    scroll_area.grid(row=1, column=0, sticky="nsew", padx=(4, 0), pady=(0, 8))
    scroll_area.columnconfigure(0, weight=1)

    for position, (token, description) in enumerate(variables):
        row = position * 2
        button = ctk.CTkButton(
            scroll_area,
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
        button.grid(row=row, column=0, sticky="ew", padx=8, pady=3)

        ctk.CTkLabel(
            scroll_area,
            text=description,
            font=ctk.CTkFont(size=10),
            text_color=theme.color("text_secondary"),
            anchor="w",
            wraplength=160,
            justify="left",
        ).grid(row=row + 1, column=0, sticky="w", padx=8, pady=(0, 6))

    return panel
