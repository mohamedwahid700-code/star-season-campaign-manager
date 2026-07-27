"""
Theme manager.

Wraps CustomTkinter's global appearance-mode API and exposes a small,
semantic color lookup (`color(name)`) so widgets never hard-code hex
values. Widgets that need to react to a theme change (because CTk does
not automatically recolor manually-set `fg_color`/`text_color` on every
widget) can subscribe via `on_change`.
"""

from __future__ import annotations

import logging
from typing import Callable

import customtkinter as ctk

from app.config.constants import ThemeMode
from app.ui.theme.colors import DARK_PALETTE, LIGHT_PALETTE

logger = logging.getLogger(__name__)

ThemeChangeCallback = Callable[[str], None]


class ThemeManager:
    """Process-wide singleton controlling appearance mode and color lookup."""

    _instance: "ThemeManager | None" = None

    def __new__(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._mode: str = ThemeMode.DARK.value
        self._subscribers: list[ThemeChangeCallback] = []
        self._initialized = True

    def apply_mode(self, mode: str) -> None:
        """Apply a theme mode ('Light' or 'Dark') globally via CustomTkinter."""
        normalized = mode if mode in (ThemeMode.LIGHT.value, ThemeMode.DARK.value) else ThemeMode.DARK.value
        self._mode = normalized
        ctk.set_appearance_mode(normalized)
        logger.info("Theme applied: %s", normalized)
        for callback in list(self._subscribers):
            callback(normalized)

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def is_dark(self) -> bool:
        return self._mode == ThemeMode.DARK.value

    def on_change(self, callback: ThemeChangeCallback) -> None:
        self._subscribers.append(callback)

    def color(self, name: str) -> str:
        """Look up a semantic color name in the palette for the current mode."""
        palette = DARK_PALETTE if self.is_dark else LIGHT_PALETTE
        try:
            return palette[name]
        except KeyError as exc:
            raise KeyError(
                f"Unknown theme color '{name}'. Available: {sorted(palette.keys())}"
            ) from exc


# Convenience module-level accessor mirroring the singleton instance.
def get_theme_manager() -> ThemeManager:
    return ThemeManager()
