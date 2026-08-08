"""
Static, non-configurable constants shared across the application.

Anything a *user* can change belongs in the `settings` table via
`SettingsService`, not here. Anything that changes *per deployment*
belongs in `AppConfig`. This module is for values that are simply true
about the application, regardless of user or environment.
"""

from enum import Enum


class NavigationKey(str, Enum):
    """Identifiers for every navigable page in the main window."""

    DASHBOARD = "dashboard"
    EXHIBITIONS = "exhibitions"
    CAMPAIGNS = "campaigns"
    CONTACTS = "contacts"
    TEMPLATES = "templates"
    HISTORY = "history"
    REPORTS = "reports"
    SETTINGS = "settings"
    ABOUT = "about"


NAVIGATION_LABELS: dict[NavigationKey, str] = {
    NavigationKey.DASHBOARD: "Dashboard",
    NavigationKey.EXHIBITIONS: "Exhibitions",
    NavigationKey.CAMPAIGNS: "Campaigns",
    NavigationKey.CONTACTS: "Contacts",
    NavigationKey.TEMPLATES: "Templates",
    NavigationKey.HISTORY: "History",
    NavigationKey.REPORTS: "Reports",
    NavigationKey.SETTINGS: "Settings",
    NavigationKey.ABOUT: "About",
}

# Ordered navigation for the sidebar (top to bottom).
NAVIGATION_ORDER: list[NavigationKey] = [
    NavigationKey.DASHBOARD,
    NavigationKey.EXHIBITIONS,
    NavigationKey.CAMPAIGNS,
    NavigationKey.CONTACTS,
    NavigationKey.TEMPLATES,
    NavigationKey.HISTORY,
    NavigationKey.REPORTS,
    NavigationKey.SETTINGS,
    NavigationKey.ABOUT,
]


class ThemeMode(str, Enum):
    LIGHT = "Light"
    DARK = "Dark"
    SYSTEM = "System"


class SettingKey(str, Enum):
    """Canonical keys used in the `settings` table."""

    COMPANY_NAME = "company_name"
    DEFAULT_LANGUAGE = "default_language"
    THEME_MODE = "theme_mode"
    DEFAULT_DELAY_SECONDS = "default_delay_seconds"
    DEFAULT_OUTLOOK_ACCOUNT = "default_outlook_account"
    WINDOW_WIDTH = "window_width"
    WINDOW_HEIGHT = "window_height"
    WINDOW_MAXIMIZED = "window_maximized"
    CONTACT_IMPORT_COLUMN_MAPPING = "contact_import_column_mapping"


class SettingValueType(str, Enum):
    """Declares how a setting's raw string value should be interpreted."""

    STRING = "string"
    INT = "int"
    BOOL = "bool"
    JSON = "json"


# Default values applied the first time the application runs, before the
# user has ever touched Settings.
DEFAULT_SETTINGS: dict[SettingKey, tuple[str, SettingValueType]] = {
    SettingKey.COMPANY_NAME: ("Star Season for Exhibitions & Conferences", SettingValueType.STRING),
    SettingKey.DEFAULT_LANGUAGE: ("English", SettingValueType.STRING),
    SettingKey.THEME_MODE: (ThemeMode.DARK.value, SettingValueType.STRING),
    SettingKey.DEFAULT_DELAY_SECONDS: ("5", SettingValueType.INT),
    SettingKey.DEFAULT_OUTLOOK_ACCOUNT: ("", SettingValueType.STRING),
    SettingKey.WINDOW_WIDTH: ("1280", SettingValueType.INT),
    SettingKey.WINDOW_HEIGHT: ("800", SettingValueType.INT),
    SettingKey.WINDOW_MAXIMIZED: ("false", SettingValueType.BOOL),
    SettingKey.CONTACT_IMPORT_COLUMN_MAPPING: ("{}", SettingValueType.JSON),
}

SUPPORTED_LANGUAGES: list[str] = ["English", "Arabic"]

# Campaigns reuse the same language list as the rest of the application,
# but are kept as a separate name so Campaigns and general app language
# preferences can diverge in a future sprint without a rename here.
CAMPAIGN_LANGUAGES: list[str] = SUPPORTED_LANGUAGES

MIN_WINDOW_WIDTH = 1024
MIN_WINDOW_HEIGHT = 700


class TemplateVariable(str, Enum):
    """
    Mail-merge style tokens authors can drop into a Template or Campaign's
    HTML body. `TemplateRenderingService` replaces every recognized token
    with a real value drawn from the selected contact (and a couple of
    application-level values) when rendering a preview.
    """

    COMPANY = "Company"
    EVENT_NAME = "EventName"
    WEBSITE = "Website"
    COUNTRY = "Country"
    STAND = "Stand"
    CONTACT_NAME = "ContactName"
    SENDER_NAME = "SenderName"
    WHATSAPP = "WhatsApp"


# Human-readable description shown next to each token in the variables
# side panel of the template editor.
TEMPLATE_VARIABLE_DESCRIPTIONS: dict[TemplateVariable, str] = {
    TemplateVariable.COMPANY: "Recipient's company name",
    TemplateVariable.EVENT_NAME: "The campaign's event name",
    TemplateVariable.WEBSITE: "Recipient's website",
    TemplateVariable.COUNTRY: "Recipient's country",
    TemplateVariable.STAND: "Recipient's stand number",
    TemplateVariable.CONTACT_NAME: "Recipient's contact name",
    TemplateVariable.SENDER_NAME: "Name of the person sending the campaign",
    TemplateVariable.WHATSAPP: "Recipient's WhatsApp/phone number",
}

# Accepted column header spellings when importing an Excel/CSV contact
# list, normalized (lowercased, stripped) -> Contact model field name.
# Keeping this list here (rather than in the import service) means the
# export routine can reuse the canonical -> display direction too.
CONTACT_IMPORT_COLUMN_ALIASES: dict[str, str] = {
    # Email
    "email": "email",
    "emails": "email",
    "emails_found": "email",
    "e-mail": "email",
    "email_address": "email",
    "email address": "email",
    "contact_email": "email",
    "company_email": "email",
    "mail": "email",
    # Company
    "company": "company",
    "company_name": "company",
    "company name": "company",
    "organization": "company",
    # Contact
    "contact": "contact_name",
    "contact_name": "contact_name",
    "contact name": "contact_name",
    "person": "contact_name",
    "name": "contact_name",
    "full name": "contact_name",
    # Country
    "country": "country",
    # Website
    "website": "website",
    "web": "website",
    "url": "website",
    "web site": "website",
    # Phone
    "phone": "phone",
    "telephone": "phone",
    "mobile": "phone",
    "phone number": "phone",
    "whatsapp": "phone",
    # Stand
    "stand": "stand_number",
    "stand_number": "stand_number",
    "booth": "stand_number",
    "booth_number": "stand_number",
    "stand number": "stand_number",
    "booth number": "stand_number",
    # Notes
    "notes": "notes",
    "note": "notes",
    "comments": "notes",
}

# Display order and labels for exporting contacts back out to Excel/CSV.
CONTACT_EXPORT_COLUMNS: list[tuple[str, str]] = [
    ("contact_name", "Contact Name"),
    ("company", "Company Name"),
    ("email", "Email"),
    ("country", "Country"),
    ("website", "Website"),
    ("phone", "Phone"),
    ("stand_number", "Stand Number"),
    ("notes", "Notes"),
]
