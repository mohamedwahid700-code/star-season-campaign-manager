"""
Empty-state component.

Several Sprint 1 pages (Campaigns, Contacts, Templates, History,
Reports) are navigable but intentionally have no business logic yet.
Rather than duplicate the same "nothing here yet" layout in five view
files, they all render this shared component with page-specific copy.
"""

from __future__ import annotations

import customtkinter as ctk

from app.ui.theme.theme_manager import ThemeManager


def build_empty_state(
    parent: ctk.CTkBaseClass,
    theme: ThemeManager,
    headline: str,
    description: str,
) -> ctk.CTkFrame:
    """Build and return a centered empty-state card ready to be gridded/packed by the caller."""
    card = ctk.CTkFrame(
        parent,
        fg_color=theme.color("surface"),
        corner_radius=12,
        border_width=1,
        border_color=theme.color("border"),
    )
    card.columnconfigure(0, weight=1)

    ctk.CTkLabel(
        card,
        text=headline,
        font=ctk.CTkFont(size=18, weight="bold"),
        text_color=theme.color("text_primary"),
    ).grid(row=0, column=0, pady=(48, 8), padx=48)

    ctk.CTkLabel(
        card,
        text=description,
        font=ctk.CTkFont(size=13),
        text_color=theme.color("text_secondary"),
        wraplength=440,
        justify="center",
    ).grid(row=1, column=0, pady=(0, 48), padx=48)

    return card
