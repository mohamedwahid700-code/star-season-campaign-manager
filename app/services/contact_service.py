"""
Contact service.

Wraps `ContactRepository` with the validation and normalization rules
that apply whenever a single contact is created or edited by hand (as
opposed to a bulk import, which has its own service since it needs
row-by-row preview/skip semantics that don't apply here).
"""

from __future__ import annotations

import logging

from app.models.contact import Contact
from app.repositories.contact_repository import ContactRepository
from app.utils.validators import is_valid_email, normalize_email

logger = logging.getLogger(__name__)


class DuplicateEmailError(ValueError):
    """Raised when saving a contact would collide with another contact's email."""


class InvalidEmailError(ValueError):
    """Raised when a contact's email address fails validation."""


class ContactService:
    def __init__(self, repository: ContactRepository | None = None) -> None:
        self._repository = repository or ContactRepository()

    def list_contacts(
        self,
        search_term: str | None = None,
        country: str | None = None,
        sort_by: str = "updated_at",
        sort_descending: bool = True,
    ) -> list[Contact]:
        return self._repository.search(
            term=search_term,
            country=country,
            sort_by=sort_by,
            sort_descending=sort_descending,
        )

    def get_countries(self) -> list[str]:
        return self._repository.get_distinct_countries()

    def get_contact(self, contact_id: int) -> Contact | None:
        return self._repository.get_by_id(contact_id)

    def create_contact(
        self,
        email: str,
        contact_name: str = "",
        company: str = "",
        country: str = "",
        website: str = "",
        phone: str = "",
        stand_number: str = "",
        notes: str = "",
    ) -> Contact:
        normalized_email = self._validate_and_normalize_email(email)
        if self._repository.get_by_email(normalized_email) is not None:
            raise DuplicateEmailError(f"A contact with email '{normalized_email}' already exists.")

        contact = Contact(
            email=normalized_email,
            contact_name=contact_name.strip() or None,
            company=company.strip() or None,
            country=country.strip() or None,
            website=website.strip() or None,
            phone=phone.strip() or None,
            stand_number=stand_number.strip() or None,
            notes=notes.strip() or None,
        )
        created = self._repository.add(contact)
        logger.info("Contact created: id=%s email=%s", created.id, created.email)
        return created

    def update_contact(
        self,
        contact_id: int,
        email: str,
        contact_name: str = "",
        company: str = "",
        country: str = "",
        website: str = "",
        phone: str = "",
        stand_number: str = "",
        notes: str = "",
    ) -> Contact:
        normalized_email = self._validate_and_normalize_email(email)

        existing_with_email = self._repository.get_by_email(normalized_email)
        if existing_with_email is not None and existing_with_email.id != contact_id:
            raise DuplicateEmailError(f"Another contact already uses email '{normalized_email}'.")

        contact = self._repository.get_by_id(contact_id)
        if contact is None:
            raise ValueError(f"Contact with id={contact_id} does not exist.")

        contact.email = normalized_email
        contact.contact_name = contact_name.strip() or None
        contact.company = company.strip() or None
        contact.country = country.strip() or None
        contact.website = website.strip() or None
        contact.phone = phone.strip() or None
        contact.stand_number = stand_number.strip() or None
        contact.notes = notes.strip() or None

        updated = self._repository.update(contact)
        logger.info("Contact updated: id=%s email=%s", updated.id, updated.email)
        return updated

    def delete_contact(self, contact_id: int) -> bool:
        deleted = self._repository.delete(contact_id)
        if deleted:
            logger.info("Contact deleted: id=%s", contact_id)
        return deleted

    @staticmethod
    def _validate_and_normalize_email(email: str) -> str:
        if not is_valid_email(email):
            raise InvalidEmailError(f"'{email}' is not a valid email address.")
        return normalize_email(email)
