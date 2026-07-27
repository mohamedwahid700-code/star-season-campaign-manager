"""
Data table component.

CustomTkinter has no built-in table widget, so this wraps the standard
library's `ttk.Treeview` -- which gives real column headers, click-to-sort,
row selection, and a native scrollbar for free -- and re-skins it with
`ttk.Style` to match the current brand theme. Used by the Contacts and
Campaigns pages so both share identical table behavior.

The table itself does not know how to sort or filter data; clicking a
column header just calls back to whoever created the table with the
column key, and the caller (a controller-backed view) re-fetches
already-sorted rows from the database. This keeps sorting/filtering
logic in one place (the repository layer) instead of duplicating it in
the UI.
"""

from __future__ import annotations

from tkinter import ttk
from typing import Callable

import customtkinter as ctk

from app.ui.theme.theme_manager import ThemeManager


class DataTable(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        theme_manager: ThemeManager,
        columns: list[tuple[str, str, int]],
        on_sort: Callable[[str], None] | None = None,
        on_row_double_click: Callable[[str], None] | None = None,
        on_selection_change: Callable[[str | None], None] | None = None,
    ) -> None:
        """
        Parameters
        ----------
        columns:
            List of `(key, label, width)` tuples, in display order.
        on_sort:
            Called with a column `key` when its header is clicked.
        on_row_double_click:
            Called with the row's `iid` (its `str(id)`) on double-click.
        on_selection_change:
            Called with the selected row's `iid`, or `None` if the
            selection was cleared.
        """
        self._theme = theme_manager
        self._column_keys = [key for key, _, _ in columns]
        self._on_sort = on_sort
        self._on_row_double_click = on_row_double_click
        self._on_selection_change = on_selection_change

        super().__init__(master, fg_color="transparent")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._style_name = f"StarSeason{id(self)}.Treeview"
        self._configure_style()

        self.tree = ttk.Treeview(
            self,
            columns=self._column_keys,
            show="headings",
            selectmode="browse",
            style=self._style_name,
        )
        for key, label, width in columns:
            self.tree.heading(key, text=label, command=lambda k=key: self._handle_sort(k))
            self.tree.column(key, width=width, anchor="w")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        if on_row_double_click:
            self.tree.bind("<Double-1>", self._handle_double_click)
        if on_selection_change:
            self.tree.bind("<<TreeviewSelect>>", self._handle_selection_change)

    def _configure_style(self) -> None:
        style = ttk.Style()
        # "clam" is the only built-in ttk theme that reliably accepts full
        # color overrides on both Windows and Linux; without it, some
        # platforms silently ignore background/foreground configuration.
        style.theme_use("clam")

        style.configure(
            self._style_name,
            background=self._theme.color("surface"),
            fieldbackground=self._theme.color("surface"),
            foreground=self._theme.color("text_primary"),
            bordercolor=self._theme.color("border"),
            borderwidth=0,
            rowheight=30,
        )
        style.map(
            self._style_name,
            background=[("selected", self._theme.color("primary_soft"))],
            foreground=[("selected", self._theme.color("primary"))],
        )
        style.configure(
            f"{self._style_name}.Heading",
            background=self._theme.color("surface_alt"),
            foreground=self._theme.color("text_secondary"),
            borderwidth=0,
            relief="flat",
        )
        style.map(f"{self._style_name}.Heading", background=[("active", self._theme.color("border"))])

    def refresh_theme(self) -> None:
        """Re-apply theme colors after a light/dark toggle."""
        self._configure_style()

    def set_rows(self, rows: list[tuple[str, tuple]]) -> None:
        """Replace all rows. `rows` is a list of `(iid, values)` tuples."""
        self.tree.delete(*self.tree.get_children())
        for iid, values in rows:
            self.tree.insert("", "end", iid=iid, values=values)

    def get_selected_iid(self) -> str | None:
        selection = self.tree.selection()
        return selection[0] if selection else None

    def _handle_sort(self, key: str) -> None:
        if self._on_sort:
            self._on_sort(key)

    def _handle_double_click(self, _event) -> None:
        iid = self.get_selected_iid()
        if iid and self._on_row_double_click:
            self._on_row_double_click(iid)

    def _handle_selection_change(self, _event) -> None:
        if self._on_selection_change:
            self._on_selection_change(self.get_selected_iid())
