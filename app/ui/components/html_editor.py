"""
HTML rich text editor component.

CustomTkinter (and Tkinter generally) has no `contentEditable`-style
HTML widget, so this builds a practical WYSIWYG-*like* editor on top of
the standard library's `tkinter.Text` widget, using its native tag
system for real visual formatting (bold/italic/underline/alignment are
rendered live, not just stored as markup), plus:

    - `to_html()`  -- serializes the widget's tagged content to an HTML
      fragment suitable for storing in `Template.html_content` or
      `Campaign.html_body`.
    - `load_html()` -- parses an HTML fragment (via BeautifulSoup4) back
      into tagged runs, so editing an existing Template/Campaign shows
      real formatting again, not raw tags.

Images are embedded as base64 data URIs (via Pillow for
opening/resizing/re-encoding) so the resulting HTML is fully
self-contained -- no external image hosting is required for an email
body. Links are tracked in a dict from a unique per-link tag name to
its href, since a Tk tag only carries a name, not arbitrary attributes.
"""

from __future__ import annotations

import base64
import io
import logging
import re
import tkinter as tk
from tkinter import filedialog, simpledialog
from typing import Callable

import customtkinter as ctk
from bs4 import BeautifulSoup, NavigableString, Tag
from PIL import Image, ImageTk

from app.ui.theme.theme_manager import ThemeManager

logger = logging.getLogger(__name__)

_MAX_IMAGE_WIDTH = 480

_INLINE_TAG_HTML = {
    "bold": ("strong", ""),
    "italic": ("em", ""),
    "underline": ("u", ""),
}

_ALIGN_TAGS = ("align_left", "align_center", "align_right")
_DIRECTION_TAGS = ("rtl", "ltr")


class HtmlEditor(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, theme_manager: ThemeManager) -> None:
        self._theme = theme_manager
        self._links: dict[str, str] = {}
        self._images: list[ImageTk.PhotoImage] = []  # keep refs alive; Tk drops GC'd images
        self._image_sources: dict[str, str] = {}  # image name -> original data URI
        self._link_counter = 0
        self._image_counter = 0
        self._current_align = "align_left"
        self._current_direction = "ltr"
        self._list_counter = 0

        super().__init__(master, fg_color=theme_manager.color("surface"), corner_radius=8)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._build_toolbar()
        self._build_text_widget()
        self._configure_tags()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def _build_toolbar(self) -> None:
        toolbar = ctk.CTkFrame(self, fg_color=self._theme.color("surface_alt"), corner_radius=6)
        toolbar.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))

        def add_button(text: str, command: Callable[[], None], width: int = 34) -> None:
            ctk.CTkButton(
                toolbar,
                text=text,
                width=width,
                height=28,
                corner_radius=6,
                font=ctk.CTkFont(size=12),
                fg_color="transparent",
                text_color=self._theme.color("text_primary"),
                hover_color=self._theme.color("border"),
                command=command,
            ).pack(side="left", padx=2, pady=4)

        add_button("B", self.toggle_bold)
        add_button("I", self.toggle_italic)
        add_button("U", self.toggle_underline)
        self._add_separator(toolbar)
        add_button("• List", lambda: self.apply_list("bullet"), width=50)
        add_button("1. List", lambda: self.apply_list("number"), width=50)
        self._add_separator(toolbar)
        add_button("Link", self.insert_link, width=44)
        add_button("Image", self.insert_image, width=50)
        self._add_separator(toolbar)
        add_button("Left", lambda: self.set_alignment("align_left"), width=42)
        add_button("Center", lambda: self.set_alignment("align_center"), width=52)
        add_button("Right", lambda: self.set_alignment("align_right"), width=46)
        self._add_separator(toolbar)
        add_button("RTL", lambda: self.set_direction("rtl"), width=38)
        add_button("LTR", lambda: self.set_direction("ltr"), width=38)
        self._add_separator(toolbar)
        add_button("Undo", self.undo, width=48)
        add_button("Redo", self.redo, width=48)

    def _add_separator(self, toolbar: ctk.CTkFrame) -> None:
        ctk.CTkFrame(toolbar, width=1, height=20, fg_color=self._theme.color("border")).pack(
            side="left", padx=6, pady=4
        )

    def _build_text_widget(self) -> None:
        container = ctk.CTkFrame(self, fg_color=self._theme.color("background"), corner_radius=6)
        container.grid(row=1, column=0, sticky="nsew", padx=8, pady=(4, 8))
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        self.text = tk.Text(
            container,
            wrap="word",
            undo=True,
            autoseparators=True,
            maxundo=-1,
            bg=self._theme.color("surface"),
            fg=self._theme.color("text_primary"),
            insertbackground=self._theme.color("text_primary"),
            selectbackground=self._theme.color("primary_soft"),
            selectforeground=self._theme.color("primary"),
            relief="flat",
            borderwidth=0,
            padx=12,
            pady=10,
            font=("Segoe UI", 12),
        )
        self.text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ctk.CTkScrollbar(container, command=self.text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.text.configure(yscrollcommand=scrollbar.set)

    def _configure_tags(self) -> None:
        self.text.tag_configure("bold", font=("Segoe UI", 12, "bold"))
        self.text.tag_configure("italic", font=("Segoe UI", 12, "italic"))
        self.text.tag_configure("underline", underline=True)
        self.text.tag_configure("align_left", justify="left")
        self.text.tag_configure("align_center", justify="center")
        self.text.tag_configure("align_right", justify="right")
        self.text.tag_configure("bullet", lmargin1=24, lmargin2=40)
        self.text.tag_configure("number", lmargin1=24, lmargin2=40)
        self.text.tag_configure(
            "link_default", foreground=self._theme.color("info"), underline=True
        )

    # ------------------------------------------------------------------
    # Toolbar actions
    # ------------------------------------------------------------------
    def toggle_bold(self) -> None:
        self._toggle_tag_on_selection("bold")

    def toggle_italic(self) -> None:
        self._toggle_tag_on_selection("italic")

    def toggle_underline(self) -> None:
        self._toggle_tag_on_selection("underline")

    def _toggle_tag_on_selection(self, tag: str) -> None:
        try:
            start, end = self.text.index("sel.first"), self.text.index("sel.last")
        except tk.TclError:
            return  # no selection -- nothing to toggle
        current_tags = self.text.tag_names("sel.first")
        if tag in current_tags:
            self.text.tag_remove(tag, start, end)
        else:
            self.text.tag_add(tag, start, end)

    def set_alignment(self, align_tag: str) -> None:
        line_start, line_end = self._current_line_bounds()
        for tag in _ALIGN_TAGS:
            self.text.tag_remove(tag, line_start, line_end)
        self.text.tag_add(align_tag, line_start, line_end)
        self._current_align = align_tag

    def set_direction(self, direction_tag: str) -> None:
        line_start, line_end = self._current_line_bounds()
        for tag in _DIRECTION_TAGS:
            self.text.tag_remove(tag, line_start, line_end)
        self.text.tag_add(direction_tag, line_start, line_end)
        # RTL reads naturally right-aligned; nudge alignment to match
        # unless the user already picked one explicitly for this line.
        if direction_tag == "rtl" and not any(
            t in self.text.tag_names(line_start) for t in _ALIGN_TAGS
        ):
            self.text.tag_add("align_right", line_start, line_end)
        self._current_direction = direction_tag

    def apply_list(self, kind: str) -> None:
        """Insert a bullet/number marker at the start of the current line."""
        line_start = self.text.index("insert linestart")
        self._list_counter += 1
        marker = "•  " if kind == "bullet" else f"{self._list_counter}.  "
        self.text.insert(line_start, marker)
        line_end = self.text.index(f"{line_start} lineend")
        self.text.tag_add(kind, line_start, line_end)

    def insert_link(self) -> None:
        try:
            selected_text = self.text.get("sel.first", "sel.last")
        except tk.TclError:
            selected_text = ""

        url = simpledialog.askstring("Insert Link", "URL:", parent=self)
        if not url:
            return
        display_text = selected_text or simpledialog.askstring(
            "Insert Link", "Link text:", parent=self, initialvalue=url
        )
        if not display_text:
            return

        self._link_counter += 1
        tag_name = f"link_{self._link_counter}"
        self._links[tag_name] = url
        self.text.tag_configure(tag_name, foreground=self._theme.color("info"), underline=True)

        try:
            start, end = self.text.index("sel.first"), self.text.index("sel.last")
            self.text.delete(start, end)
            insert_at = start
        except tk.TclError:
            insert_at = self.text.index("insert")

        self.text.insert(insert_at, display_text, ("link_default", tag_name))

    def insert_image(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Insert Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")],
        )
        if not file_path:
            return

        try:
            with Image.open(file_path) as source_image:
                image = source_image.convert("RGBA")
                if image.width > _MAX_IMAGE_WIDTH:
                    ratio = _MAX_IMAGE_WIDTH / image.width
                    image = image.resize(
                        (int(image.width * ratio), int(image.height * ratio)), Image.LANCZOS
                    )

                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                data_uri = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")

                photo_image = ImageTk.PhotoImage(image)
        except Exception:
            logger.exception("Failed to load image for insertion: %s", file_path)
            return

        self._image_counter += 1
        image_name = f"editor_image_{self._image_counter}"
        self._images.append(photo_image)
        self._image_sources[image_name] = data_uri

        self.text.image_create("insert", image=photo_image, name=image_name)

    def undo(self) -> None:
        try:
            self.text.edit_undo()
        except tk.TclError:
            pass

    def redo(self) -> None:
        try:
            self.text.edit_redo()
        except tk.TclError:
            pass

    def insert_variable_token(self, token: str) -> None:
        """Insert a `{Variable}` token at the current cursor position."""
        self.text.insert("insert", token)
        self.text.focus_set()

    def _current_line_bounds(self) -> tuple[str, str]:
        return self.text.index("insert linestart"), self.text.index("insert lineend")

    # ------------------------------------------------------------------
    # Content access
    # ------------------------------------------------------------------
    def get_plain_text(self) -> str:
        return self.text.get("1.0", "end-1c")

    def clear(self) -> None:
        self.text.delete("1.0", "end")
        self._links.clear()
        self._images.clear()
        self._image_sources.clear()

    def to_html(self) -> str:
        """Serialize the current editor content to an HTML fragment."""
        line_count = int(self.text.index("end-1c").split(".")[0])
        blocks: list[str] = []

        list_buffer: list[str] = []
        list_kind: str | None = None

        def flush_list() -> None:
            nonlocal list_buffer, list_kind
            if list_buffer:
                tag = "ul" if list_kind == "bullet" else "ol"
                items = "".join(f"<li>{item}</li>" for item in list_buffer)
                blocks.append(f"<{tag}>{items}</{tag}>")
            list_buffer = []
            list_kind = None

        for line_number in range(1, line_count + 1):
            line_start = f"{line_number}.0"
            line_end = f"{line_number}.end"
            if self.text.compare(line_start, "==", line_end):
                flush_list()
                continue

            tags_at_start = self.text.tag_names(line_start)
            raw_line_text = self.text.get(line_start, line_end)

            if "bullet" in tags_at_start or "number" in tags_at_start:
                kind = "bullet" if "bullet" in tags_at_start else "number"
                # The visible marker ("•  " / "1.  ") is real text in the
                # Tk buffer so it renders in the WYSIWYG editor, but a
                # semantic <ul>/<ol><li> already renders its own marker in
                # a browser -- so it must not also appear as literal text
                # inside <li>, or the recipient would see it twice.
                marker_length = self._detect_list_marker_length(raw_line_text, kind)
                content_start = f"{line_number}.{marker_length}"
                inline_html = self._render_line_inline_html(content_start, line_end)

                if list_kind is not None and list_kind != kind:
                    flush_list()
                list_kind = kind
                list_buffer.append(inline_html)
                continue

            flush_list()
            inline_html = self._render_line_inline_html(line_start, line_end)

            align = next((t for t in _ALIGN_TAGS if t in tags_at_start), "align_left")
            direction = next((t for t in _DIRECTION_TAGS if t in tags_at_start), "ltr")
            align_css = align.replace("align_", "")
            style = f"text-align:{align_css};direction:{direction};"
            blocks.append(f'<p style="{style}">{inline_html}</p>')

        flush_list()
        return "\n".join(blocks)

    @staticmethod
    def _detect_list_marker_length(line_text: str, kind: str) -> int:
        """Return how many leading characters are the visible list marker."""
        if kind == "bullet":
            match = re.match(r"^•\s+", line_text)
        else:
            match = re.match(r"^\d+\.\s+", line_text)
        return len(match.group(0)) if match else 0

    def _render_line_inline_html(self, line_start: str, line_end: str) -> str:
        dump = self.text.dump(line_start, line_end, tag=True, text=True, image=True)
        open_tags: list[str] = []
        html_parts: list[str] = []

        for kind, value, _index in dump:
            if kind == "tagon":
                if value in _INLINE_TAG_HTML:
                    tag_html, _ = _INLINE_TAG_HTML[value]
                    open_tags.append(value)
                    html_parts.append(f"<{tag_html}>")
                elif value in self._links:
                    open_tags.append(value)
                    html_parts.append(f'<a href="{self._escape_attr(self._links[value])}">')
            elif kind == "tagoff":
                if value in _INLINE_TAG_HTML:
                    tag_html, _ = _INLINE_TAG_HTML[value]
                    html_parts.append(f"</{tag_html}>")
                    if value in open_tags:
                        open_tags.remove(value)
                elif value in self._links:
                    html_parts.append("</a>")
                    if value in open_tags:
                        open_tags.remove(value)
            elif kind == "text":
                html_parts.append(self._escape_text(value))
            elif kind == "image":
                data_uri = self._image_sources.get(value, "")
                if data_uri:
                    html_parts.append(f'<img src="{data_uri}" alt="" />')

        # Tk's `dump` upper bound is exclusive, so a tag that ends exactly
        # at the line's last character can have its "tagoff" event fall
        # just outside the queried range. Defensively close anything left
        # open (in reverse/LIFO order) rather than emit unbalanced HTML.
        for value in reversed(open_tags):
            if value in _INLINE_TAG_HTML:
                tag_html, _ = _INLINE_TAG_HTML[value]
                html_parts.append(f"</{tag_html}>")
            elif value in self._links:
                html_parts.append("</a>")

        return "".join(html_parts)

    @staticmethod
    def _escape_text(value: str) -> str:
        return (
            value.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    @staticmethod
    def _escape_attr(value: str) -> str:
        return value.replace('"', "&quot;")

    # ------------------------------------------------------------------
    # Loading existing HTML back into the editor
    # ------------------------------------------------------------------
    def load_html(self, html: str) -> None:
        """Parse `html` (as produced by `to_html()`, or reasonably similar
        hand-authored markup) and populate the editor with tagged runs."""
        self.clear()
        if not html.strip():
            return

        soup = BeautifulSoup(html, "html.parser")
        for element in soup.contents:
            self._insert_block(element)

    def _insert_block(self, element) -> None:
        if isinstance(element, NavigableString):
            text = str(element).strip()
            if text:
                self.text.insert("end", text + "\n")
            return

        if not isinstance(element, Tag):
            return

        if element.name == "p":
            align_tag, direction_tag = self._parse_style(element.get("style", ""))
            line_start = self.text.index("end-1c")
            self._insert_inline_children(element)
            self.text.insert("end", "\n")
            line_end = self.text.index("end-1c")
            if align_tag:
                self.text.tag_add(align_tag, line_start, line_end)
            if direction_tag:
                self.text.tag_add(direction_tag, line_start, line_end)

        elif element.name in ("ul", "ol"):
            kind = "bullet" if element.name == "ul" else "number"
            for index, item in enumerate(element.find_all("li", recursive=False), start=1):
                marker = "•  " if kind == "bullet" else f"{index}.  "
                line_start = self.text.index("end-1c")
                self.text.insert("end", marker)
                self._insert_inline_children(item)
                self.text.insert("end", "\n")
                line_end = self.text.index("end-1c")
                self.text.tag_add(kind, line_start, line_end)

        else:
            # Unknown block-level element (e.g. a hand-authored <div>):
            # fall back to inserting its text content on its own line
            # rather than silently dropping it.
            self._insert_inline_children(element)
            self.text.insert("end", "\n")

    def _insert_inline_children(self, element: Tag) -> None:
        for child in element.children:
            self._insert_inline(child, active_tags=())

    def _insert_inline(self, node, active_tags: tuple[str, ...]) -> None:
        if isinstance(node, NavigableString):
            text = str(node)
            if text:
                self.text.insert("end", text, active_tags)
            return

        if not isinstance(node, Tag):
            return

        if node.name in ("strong", "b"):
            new_tags = active_tags + ("bold",)
            for child in node.children:
                self._insert_inline(child, new_tags)
        elif node.name in ("em", "i"):
            new_tags = active_tags + ("italic",)
            for child in node.children:
                self._insert_inline(child, new_tags)
        elif node.name == "u":
            new_tags = active_tags + ("underline",)
            for child in node.children:
                self._insert_inline(child, new_tags)
        elif node.name == "a":
            href = node.get("href", "")
            self._link_counter += 1
            tag_name = f"link_{self._link_counter}"
            self._links[tag_name] = href
            self.text.tag_configure(tag_name, foreground=self._theme.color("info"), underline=True)
            new_tags = active_tags + ("link_default", tag_name)
            for child in node.children:
                self._insert_inline(child, new_tags)
        elif node.name == "img":
            self._insert_image_from_src(node.get("src", ""))
        elif node.name == "br":
            self.text.insert("end", "\n", active_tags)
        else:
            for child in node.children:
                self._insert_inline(child, active_tags)

    def _insert_image_from_src(self, src: str) -> None:
        if not src.startswith("data:image"):
            return  # external images aren't supported by the editor's WYSIWYG surface
        try:
            _, encoded = src.split(",", 1)
            raw_bytes = base64.b64decode(encoded)
            image = Image.open(io.BytesIO(raw_bytes)).convert("RGBA")
            photo_image = ImageTk.PhotoImage(image)
        except Exception:
            logger.exception("Failed to decode embedded image while loading HTML.")
            return

        self._image_counter += 1
        image_name = f"editor_image_{self._image_counter}"
        self._images.append(photo_image)
        self._image_sources[image_name] = src
        self.text.image_create("end", image=photo_image, name=image_name)

    @staticmethod
    def _parse_style(style: str) -> tuple[str | None, str | None]:
        align_tag = None
        direction_tag = None
        for declaration in style.split(";"):
            if ":" not in declaration:
                continue
            prop, _, value = declaration.partition(":")
            prop = prop.strip().lower()
            value = value.strip().lower()
            if prop == "text-align":
                align_tag = {"left": "align_left", "center": "align_center", "right": "align_right"}.get(value)
            elif prop == "direction":
                direction_tag = {"rtl": "rtl", "ltr": "ltr"}.get(value)
        return align_tag, direction_tag
