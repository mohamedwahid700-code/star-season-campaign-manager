"""
Path resolution helpers.

Centralizes how the application locates bundled assets (icons, images),
so this is the only place that needs to change if the app is later
packaged with PyInstaller (where `sys._MEIPASS` replaces the normal
project root at runtime).
"""

from __future__ import annotations

import sys
from pathlib import Path

from app.config.app_config import get_config


def get_base_path() -> Path:
    """
    Return the directory assets should be resolved relative to.

    When frozen by PyInstaller, resources are unpacked to a temporary
    directory exposed as `sys._MEIPASS`. In a normal Python run, this is
    simply the project root.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return get_config().project_root


def get_asset_path(*parts: str) -> Path:
    """Resolve a path under the `assets/` directory, e.g. get_asset_path('icons', 'logo.png')."""
    return get_base_path() / "assets" / Path(*parts)


def get_icon_path(filename: str) -> Path:
    return get_asset_path("icons", filename)


def get_image_path(filename: str) -> Path:
    return get_asset_path("images", filename)
