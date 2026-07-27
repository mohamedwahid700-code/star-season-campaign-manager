"""
Splash screen.

Shown for a brief moment at application startup, before the main
window is constructed, displaying the official Star Season logo on the
brand's dark background. Implemented as its own short-lived `tk.Tk()`
root (rather than a `Toplevel`) so it can be shown and fully torn down
*before* `MainWindow` (the application's real Tk root) is created --
Tkinter supports this sequential pattern cleanly, since only one Tk
root ever exists at a time.
"""

from __future__ import annotations

import logging
import tkinter as tk

from app.utils.paths import get_image_path

logger = logging.getLogger(__name__)

_BRAND_BACKGROUND = "#111111"
_SPLASH_WIDTH = 560
_SPLASH_HEIGHT = 320


def show_splash(duration_ms: int = 1200) -> None:
    """
    Display the splash screen for `duration_ms` milliseconds, then close
    it. Safe to call even if the logo asset is missing -- falls back to
    a plain branded background with text rather than failing startup.
    """
    try:
        root = tk.Tk()
        root.overrideredirect(True)
        root.configure(bg=_BRAND_BACKGROUND)

        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = max(0, (screen_width - _SPLASH_WIDTH) // 2)
        y = max(0, (screen_height - _SPLASH_HEIGHT) // 2)
        root.geometry(f"{_SPLASH_WIDTH}x{_SPLASH_HEIGHT}+{x}+{y}")

        container = tk.Frame(root, bg=_BRAND_BACKGROUND)
        container.pack(fill="both", expand=True)

        _populate_splash_content(container)

        root.update_idletasks()
        root.update()
        root.after(duration_ms, root.destroy)
        root.mainloop()
    except Exception:  # noqa: BLE001 - the splash is cosmetic; never block startup over it
        logger.debug("Splash screen could not be shown; continuing without it.", exc_info=True)


def _populate_splash_content(container: tk.Frame) -> None:
    logo_path = get_image_path("star_season_logo_full.png")

    if logo_path.exists():
        from PIL import Image, ImageTk

        image = Image.open(logo_path)
        # Fit within the splash window while preserving aspect ratio.
        max_width, max_height = 480, 220
        ratio = min(max_width / image.width, max_height / image.height, 1.0)
        resized = image.resize(
            (int(image.width * ratio), int(image.height * ratio)), Image.LANCZOS
        )
        photo = ImageTk.PhotoImage(resized)

        label = tk.Label(container, image=photo, bg=_BRAND_BACKGROUND, borderwidth=0)
        label.image = photo  # keep a reference alive
        label.pack(expand=True)
    else:
        # Fallback if the logo asset is ever missing: brand text only.
        tk.Label(
            container, text="STAR SEASON", fg="#D4AF37", bg=_BRAND_BACKGROUND,
            font=("Segoe UI", 32, "bold"),
        ).pack(expand=True, pady=(60, 0))
        tk.Label(
            container, text="Campaign Manager", fg="#FFFFFF", bg=_BRAND_BACKGROUND,
            font=("Segoe UI", 14),
        ).pack()

    tk.Label(
        container, text="Loading...", fg="#B0B0B0", bg=_BRAND_BACKGROUND,
        font=("Segoe UI", 11),
    ).pack(side="bottom", pady=16)
