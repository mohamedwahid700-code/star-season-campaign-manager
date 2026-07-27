"""
Base dialog.

Every modal in this application should subclass `BaseDialog` instead of
`ctk.CTkToplevel` directly. It guarantees, in one place, the behavior
every dialog needs:

    - The window never exceeds the user's actual screen size, even if
      the dialog asks for a larger "preferred" size -- it shrinks to
      fit, down to a sensible minimum, and is always resizable so the
      user can enlarge it again if their screen allows.
    - The window is centered on screen.
    - Content lives in a scrollable area (`self.content`) that grows
      with the window but automatically shows a scrollbar the instant
      content no longer fits -- nothing is ever silently clipped.
    - Action buttons live in `self.footer`, a fixed (non-scrolling) row
      pinned to the bottom of the window, so Save/Cancel/etc. are
      always visible no matter how tall the content is or how small
      the screen is.

Subclasses call `super().__init__(...)` then build their UI into
`self.content` and `self.footer` (both plain `CTkFrame`-like containers
that grid/pack children as usual) instead of gridding widgets directly
onto `self`.
"""

from __future__ import annotations

import customtkinter as ctk

from app.ui.theme.theme_manager import ThemeManager

# Reserve some room for the OS taskbar/dock and window chrome so a
# "fit to screen" dialog never touches the very edges of the display.
_SCREEN_MARGIN_WIDTH = 80
_SCREEN_MARGIN_HEIGHT = 120

# Sprint 4 requirement: every dialog must remain usable at 1366x768.
_MIN_SUPPORTED_SCREEN_WIDTH = 1366
_MIN_SUPPORTED_SCREEN_HEIGHT = 768


def apply_screen_aware_geometry(
    window: ctk.CTkToplevel,
    preferred_width: int,
    preferred_height: int,
    min_width: int = 420,
    min_height: int = 320,
) -> None:
    """
    Size and center any `CTkToplevel` so it never exceeds the user's
    actual screen -- shrinking from `preferred_*` down to fit, but never
    below `min_*`. Shared by `BaseDialog` and any "workspace" style
    dialog (e.g. the Campaign/Template editors) that manages its own
    internal expansion/scrolling instead of using `BaseDialog`'s
    scrollable content area.
    """
    window.update_idletasks()

    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    available_width = max(screen_width - _SCREEN_MARGIN_WIDTH, min_width)
    available_height = max(screen_height - _SCREEN_MARGIN_HEIGHT, min_height)

    window_width = max(min_width, min(preferred_width, available_width))
    window_height = max(min_height, min(preferred_height, available_height))

    x = max(0, (screen_width - window_width) // 2)
    y = max(0, (screen_height - window_height) // 2)

    window.resizable(True, True)
    window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    window.minsize(min(min_width, window_width), min(min_height, window_height))


def activate_grab(window: ctk.CTkToplevel) -> None:
    """Best-effort modal focus grab, safe to call even if the window manager rejects it."""
    try:
        window.grab_set()
        window.focus_force()
    except Exception:  # noqa: BLE001 - grabbing focus is best-effort
        pass


class BaseDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        theme_manager: ThemeManager,
        title: str,
        preferred_width: int,
        preferred_height: int,
        min_width: int = 420,
        min_height: int = 320,
    ) -> None:
        super().__init__(master, fg_color=theme_manager.color("background"))
        self._theme = theme_manager

        self.title(title)
        self.transient(master)

        apply_screen_aware_geometry(self, preferred_width, preferred_height, min_width, min_height)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Scrollable content area: grows with the window, scrolls the
        # instant content taller than the available space is added.
        self.content = ctk.CTkScrollableFrame(
            self, fg_color="transparent", scrollbar_button_color=theme_manager.color("border"),
        )
        self.content.grid(row=0, column=0, sticky="nsew")
        self.content.columnconfigure(0, weight=1)

        # Fixed footer: never inside the scrollable area, so Save/
        # Cancel/etc. are always on screen regardless of content height.
        self.footer = ctk.CTkFrame(self, fg_color=theme_manager.color("surface"), corner_radius=0)
        self.footer.grid(row=1, column=0, sticky="ew")
        self.footer.columnconfigure(0, weight=1)

        self.after(50, self._activate_grab)

    def _activate_grab(self) -> None:
        activate_grab(self)

    def recenter(self) -> None:
        """Re-center the dialog on screen; useful after programmatically resizing it."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        self.geometry(f"+{x}+{y}")
