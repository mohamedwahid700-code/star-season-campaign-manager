"""Contact create/edit dialog - a simple field form for one contact."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.controllers.contact_controller import ContactController, ContactFormData
from app.models.contact import Contact
from app.ui.dialogs.base_dialog import BaseDialog
from app.ui.theme.theme_manager import ThemeManager


class ContactDialog(BaseDialog):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        theme_manager: ThemeManager,
        contact_controller: ContactController,
        on_saved: Callable[[], None],
        contact: Contact | None = None,
    ) -> None:
        super().__init__(
            master, theme_manager,
            title="Edit Contact" if contact else "Add Contact",
            preferred_width=480, preferred_height=680,
            min_width=380, min_height=320,
        )
        self._controller = contact_controller
        self._on_saved = on_saved
        self._contact = contact

        self.content.columnconfigure(0, weight=1)

        fields = [
            ("Email *", "email"),
            ("Contact Name", "contact_name"),
            ("Company Name", "company"),
            ("Country", "country"),
            ("Website", "website"),
            ("Phone", "phone"),
            ("Stand Number", "stand_number"),
        ]

        self._entries: dict[str, ctk.CTkEntry] = {}
        row = 0
        for label_text, field_name in fields:
            ctk.CTkLabel(
                self.content, text=label_text, font=ctk.CTkFont(size=12, weight="bold"),
                text_color=theme_manager.color("text_primary"), anchor="w",
            ).grid(row=row, column=0, sticky="w", padx=20, pady=(14 if row == 0 else 8, 2))
            row += 1
            entry = ctk.CTkEntry(self.content, height=34)
            entry.grid(row=row, column=0, sticky="ew", padx=20)
            self._entries[field_name] = entry
            row += 1

        ctk.CTkLabel(
            self.content, text="Notes", font=ctk.CTkFont(size=12, weight="bold"),
            text_color=theme_manager.color("text_primary"), anchor="w",
        ).grid(row=row, column=0, sticky="w", padx=20, pady=(8, 2))
        row += 1
        self._notes_box = ctk.CTkTextbox(self.content, height=90)
        self._notes_box.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 20))
        row += 1

        self._status_label = ctk.CTkLabel(
            self.footer, text="", font=ctk.CTkFont(size=12), text_color=theme_manager.color("danger"),
        )
        self._status_label.grid(row=0, column=0, sticky="w", padx=20, pady=16)

        button_row = ctk.CTkFrame(self.footer, fg_color="transparent")
        button_row.grid(row=0, column=1, sticky="e", padx=20, pady=12)

        ctk.CTkButton(
            button_row, text="Cancel", width=100, height=36, corner_radius=8,
            fg_color=theme_manager.color("surface_alt"), hover_color=theme_manager.color("border"),
            text_color=theme_manager.color("text_primary"), command=self.destroy,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            button_row, text="Save Contact", width=130, height=36, corner_radius=8,
            fg_color=theme_manager.color("primary"), hover_color=theme_manager.color("primary_hover"),
            text_color=theme_manager.color("text_on_primary"), command=self._handle_save,
        ).pack(side="left")

        if contact:
            self._entries["email"].insert(0, contact.email)
            self._entries["contact_name"].insert(0, contact.contact_name or "")
            self._entries["company"].insert(0, contact.company or "")
            self._entries["country"].insert(0, contact.country or "")
            self._entries["website"].insert(0, contact.website or "")
            self._entries["phone"].insert(0, contact.phone or "")
            self._entries["stand_number"].insert(0, contact.stand_number or "")
            self._notes_box.insert("1.0", contact.notes or "")

    def _handle_save(self) -> None:
        data = ContactFormData(
            email=self._entries["email"].get().strip(),
            contact_name=self._entries["contact_name"].get().strip(),
            company=self._entries["company"].get().strip(),
            country=self._entries["country"].get().strip(),
            website=self._entries["website"].get().strip(),
            phone=self._entries["phone"].get().strip(),
            stand_number=self._entries["stand_number"].get().strip(),
            notes=self._notes_box.get("1.0", "end-1c").strip(),
        )

        try:
            if self._contact:
                self._controller.update_contact(self._contact.id, data)
            else:
                self._controller.create_contact(data)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user, not swallowed
            self._status_label.configure(text=str(exc))
            return

        self._on_saved()
        self.destroy()
