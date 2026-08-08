"""Repository for `Contact` records."""

from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import InstrumentedAttribute

from app.database.base import session_scope
from app.models.contact import Contact
from app.repositories.base_repository import BaseRepository

# Columns the Contacts page is allowed to sort by, mapped from the UI's
# column key to the actual ORM attribute. Keeping this whitelist here
# (rather than trusting an arbitrary column name from the UI) prevents
# building a query against a non-existent/unsafe attribute.
SORTABLE_COLUMNS: dict[str, InstrumentedAttribute] = {
    "contact_name": Contact.contact_name,
    "company": Contact.company,
    "email": Contact.email,
    "country": Contact.country,
    "stand_number": Contact.stand_number,
    "created_at": Contact.created_at,
    "updated_at": Contact.updated_at,
}


class ContactRepository(BaseRepository[Contact]):
    def __init__(self) -> None:
        super().__init__(Contact)

    def get_by_email(self, email: str) -> Contact | None:
        with session_scope() as session:
            return session.query(Contact).filter(Contact.email == email).first()

    def get_existing_emails(self, emails: list[str]) -> set[str]:
        """Return the subset of `emails` that already exist in the database.

        Used by the import workflow to flag duplicates against contacts
        already on file, in a single query rather than one lookup per row.
        """
        if not emails:
            return set()
        with session_scope() as session:
            rows = (
                session.query(Contact.email)
                .filter(Contact.email.in_(emails))
                .all()
            )
            return {row.email for row in rows}

    def get_contact_ids_by_emails(self, emails: list[str]) -> dict[str, int]:
        """Return {email: contact_id} for every one of `emails` that already exists.

        Used by the exhibition-scoped import to tell "reuse this existing
        global Contact" apart from "this email is brand new", in a single
        query rather than one lookup per row.
        """
        if not emails:
            return {}
        with session_scope() as session:
            rows = (
                session.query(Contact.id, Contact.email)
                .filter(Contact.email.in_(emails))
                .all()
            )
            return {row.email: row.id for row in rows}

    def bulk_add(self, contacts: list[Contact]) -> int:
        """Insert many contacts in a single transaction. Returns the number inserted."""
        if not contacts:
            return 0
        with session_scope() as session:
            session.add_all(contacts)
            session.flush()
            return len(contacts)

    def search(
        self,
        term: str | None = None,
        country: str | None = None,
        sort_by: str = "updated_at",
        sort_descending: bool = True,
    ) -> list[Contact]:
        """
        Return contacts matching an optional free-text search and/or country
        filter, sorted by a whitelisted column.
        """
        sort_column = SORTABLE_COLUMNS.get(sort_by, Contact.updated_at)

        with session_scope() as session:
            query = session.query(Contact)

            if term:
                pattern = f"%{term.strip()}%"
                query = query.filter(
                    or_(
                        Contact.contact_name.ilike(pattern),
                        Contact.company.ilike(pattern),
                        Contact.email.ilike(pattern),
                        Contact.country.ilike(pattern),
                        Contact.stand_number.ilike(pattern),
                    )
                )

            if country:
                query = query.filter(Contact.country == country)

            order = sort_column.desc() if sort_descending else sort_column.asc()
            return query.order_by(order).all()

    def get_distinct_countries(self) -> list[str]:
        with session_scope() as session:
            rows = (
                session.query(Contact.country)
                .filter(Contact.country.isnot(None), Contact.country != "")
                .distinct()
                .order_by(Contact.country.asc())
                .all()
            )
            return [row.country for row in rows]
