"""
Application entry point.

Responsible only for startup orchestration, in order:

    1. Enable DPI awareness on Windows, so text and layouts render crisp
       (not blurry/upscaled) on high-DPI laptop and monitor displays.
    2. Configure logging.
    3. Initialize the database (create tables, seed default settings).
    4. Show the splash screen with the Star Season logo.
    5. Launch the main window's Tk event loop.

Any exception raised before the window is shown is logged and
re-raised so a packaged .exe still surfaces a visible error rather than
silently closing.
"""

from __future__ import annotations

import logging
import sys

from app import __app_name__, __version__
from app.database.init_db import initialize_database
from app.utils.logger import configure_logging

logger = logging.getLogger(__name__)


def _enable_windows_dpi_awareness() -> None:
    """
    Tell Windows this process handles its own DPI scaling.

    Without this, Windows silently upscales a blurry, lower-resolution
    rendering of the window on high-DPI displays (common on modern
    laptops), instead of letting Tkinter/CustomTkinter render crisply at
    the real resolution. No-op (and safe to call) on any non-Windows
    platform.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes

        # PROCESS_PER_MONITOR_DPI_AWARE = 2 -- the modern, per-monitor
        # aware mode; falls back to the simpler system-DPI-aware call on
        # older Windows versions that don't support it.
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:  # noqa: BLE001 - fall back for older Windows
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:  # noqa: BLE001 - DPI awareness is a nice-to-have, never fatal
        logger.debug("Could not enable Windows DPI awareness.", exc_info=True)


def main() -> int:
    _enable_windows_dpi_awareness()

    configure_logging()
    logger.info("Starting %s v%s", __app_name__, __version__)

    try:
        initialize_database()
    except Exception:
        logger.exception("Fatal error during database initialization.")
        raise

    try:
        from app.ui.splash_screen import show_splash

        show_splash()
    except Exception:  # noqa: BLE001 - the splash is cosmetic, never fatal
        logger.debug("Splash screen failed; continuing to the main window.", exc_info=True)

    try:
        # Imported here, after logging/DB are ready, so CustomTkinter and
        # every UI module only ever run against a fully-initialized app.
        from app.ui.main_window import MainWindow

        window = MainWindow()
        window.mainloop()
    except Exception:
        logger.exception("Fatal error while running the application.")
        raise

    logger.info("Application closed normally.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
