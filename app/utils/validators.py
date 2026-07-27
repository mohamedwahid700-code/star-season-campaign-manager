"""
Validation helpers shared across services.

Kept intentionally small and dependency-free (a single compiled regex)
so both the contact import pipeline and the contact edit form validate
emails identically.
"""

from __future__ import annotations

import re

# A pragmatic, widely-used "good enough" email pattern. It deliberately
# does not attempt to fully implement RFC 5322 (nothing practically
# does); it catches the overwhelming majority of typos and malformed
# addresses seen in real-world exhibitor spreadsheets.
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(value: str | None) -> bool:
    """Return True if `value` looks like a syntactically valid email address."""
    if not value:
        return False
    return bool(_EMAIL_PATTERN.match(value.strip()))


def normalize_email(value: str) -> str:
    """Lowercase and strip an email address for consistent duplicate detection."""
    return value.strip().lower()
