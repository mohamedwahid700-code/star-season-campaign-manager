"""
Star Season brand color palette.

Two flat dictionaries -- one per appearance mode -- map semantic color
names to hex values. UI code should always ask `ThemeManager` for a
color by semantic name (e.g. `theme.color("surface")`) rather than
hard-coding hex values, so switching modes or rebranding later touches
this single file.

Brand colors (per Star Season's official branding):
    Gold:  #D4AF37  -- the single accent color in both modes
    Black: #111111  -- the dark mode background
"""

from __future__ import annotations

GOLD = "#D4AF37"
GOLD_HOVER_DARK_MODE = "#E8C158"   # lighter on hover against a dark surface
GOLD_HOVER_LIGHT_MODE = "#B8952E"  # darker on hover against a light surface
BLACK = "#111111"

LIGHT_PALETTE: dict[str, str] = {
    "primary": GOLD,
    "primary_hover": GOLD_HOVER_LIGHT_MODE,
    "primary_soft": "#FBF1D6",     # pale gold tint, for selected rows/badges

    "background": "#F2F2F0",       # light gray window background
    "surface": "#FFFFFF",          # cards, sidebar, top bar
    "surface_alt": "#EDEDEB",      # subtle secondary surface (input fields)

    "border": "#DDDDDA",
    "divider": "#E6E6E3",

    "text_primary": BLACK,
    "text_secondary": "#5A5A57",
    "text_disabled": "#A0A09C",
    "text_on_primary": BLACK,      # dark text reads best on a bright gold accent

    "success": "#1E9E6B",
    "warning": "#C9791B",
    "danger": "#D14343",
    "info": "#2E7FD1",
}

DARK_PALETTE: dict[str, str] = {
    "primary": GOLD,
    "primary_hover": GOLD_HOVER_DARK_MODE,
    "primary_soft": "#3A2F14",     # dark gold-brown tint, for selected rows/badges

    "background": BLACK,
    "surface": "#1A1A1A",          # dark gray panels
    "surface_alt": "#242424",      # slightly lighter dark gray (input fields)

    "border": "#333333",
    "divider": "#2A2A2A",

    "text_primary": "#FFFFFF",
    "text_secondary": "#B0B0B0",
    "text_disabled": "#6E6E6E",
    "text_on_primary": BLACK,      # dark text reads best on a bright gold accent

    "success": "#3FBF8F",
    "warning": "#E0A73C",
    "danger": "#E56464",
    "info": "#5B9FE8",
}
