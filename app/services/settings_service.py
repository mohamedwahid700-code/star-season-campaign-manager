"""
Settings service.

This is the single place in the application that knows how to convert
between the raw string rows in the `settings` table and typed Python
values (str / int / bool). UI code and other services should always go
through `SettingsService`, never through `SettingsRepository` directly,
so type conversion stays consistent everywhere.

The service also supports lightweight change notifications: any part of
the UI can subscribe to a specific setting key and be called back when
it changes (used by the theme toggle to repaint every open view without
those views needing to poll the database).
"""

from __future__ import annotations

import json
import logging
from typing import Callable

from app.config.constants import DEFAULT_SETTINGS, SettingKey, SettingValueType
from app.repositories.settings_repository import SettingsRepository

logger = logging.getLogger(__name__)

SettingChangeCallback = Callable[[str, object], None]


class SettingsService:
    """Typed, cached access to application settings."""

    def __init__(self, repository: SettingsRepository | None = None) -> None:
        self._repository = repository or SettingsRepository()
        self._cache: dict[str, str] = {}
        self._value_types: dict[str, str] = {}
        self._subscribers: list[SettingChangeCallback] = []
        self._load_cache()

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------
    def _load_cache(self) -> None:
        rows = self._repository.get_all()
        self._cache = {row.key: row.value for row in rows}
        self._value_types = {row.key: row.value_type for row in rows}

    def reload(self) -> None:
        """Force a re-read of every setting from the database."""
        self._load_cache()

    # ------------------------------------------------------------------
    # Change notifications
    # ------------------------------------------------------------------
    def subscribe(self, callback: SettingChangeCallback) -> None:
        """Register a callback invoked as `callback(key, new_value)` on change."""
        self._subscribers.append(callback)

    def unsubscribe(self, callback: SettingChangeCallback) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def _notify(self, key: str, value: object) -> None:
        for callback in list(self._subscribers):
            try:
                callback(key, value)
            except Exception:  # noqa: BLE001 - a broken subscriber must not break settings
                logger.exception("Settings subscriber raised while handling key=%s", key)

    # ------------------------------------------------------------------
    # Generic typed access
    # ------------------------------------------------------------------
    def get_string(self, key: SettingKey, default: str = "") -> str:
        return self._cache.get(key.value, default)

    def get_int(self, key: SettingKey, default: int = 0) -> int:
        raw = self._cache.get(key.value)
        if raw is None:
            return default
        try:
            return int(raw)
        except ValueError:
            logger.warning("Setting %s has non-integer value %r; using default.", key.value, raw)
            return default

    def get_bool(self, key: SettingKey, default: bool = False) -> bool:
        raw = self._cache.get(key.value)
        if raw is None:
            return default
        return raw.strip().lower() in {"1", "true", "yes", "on"}

    def get_json(self, key: SettingKey, default: object = None) -> object:
        raw = self._cache.get(key.value)
        if raw is None:
            return default
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Setting %s has invalid JSON value; using default.", key.value)
            return default

    def set_value(self, key: SettingKey, value: object, value_type: SettingValueType) -> None:
        if value_type is SettingValueType.JSON:
            raw_value = json.dumps(value)
        elif value_type is SettingValueType.BOOL:
            raw_value = "true" if value else "false"
        else:
            raw_value = str(value)

        self._repository.upsert(key.value, raw_value, value_type.value)
        self._cache[key.value] = raw_value
        self._value_types[key.value] = value_type.value
        self._notify(key.value, value)

    # ------------------------------------------------------------------
    # Convenience accessors for well-known settings
    # ------------------------------------------------------------------
    def get_company_name(self) -> str:
        return self.get_string(SettingKey.COMPANY_NAME, DEFAULT_SETTINGS[SettingKey.COMPANY_NAME][0])

    def set_company_name(self, value: str) -> None:
        self.set_value(SettingKey.COMPANY_NAME, value, SettingValueType.STRING)

    def get_default_language(self) -> str:
        return self.get_string(
            SettingKey.DEFAULT_LANGUAGE, DEFAULT_SETTINGS[SettingKey.DEFAULT_LANGUAGE][0]
        )

    def set_default_language(self, value: str) -> None:
        self.set_value(SettingKey.DEFAULT_LANGUAGE, value, SettingValueType.STRING)

    def get_theme_mode(self) -> str:
        return self.get_string(SettingKey.THEME_MODE, DEFAULT_SETTINGS[SettingKey.THEME_MODE][0])

    def set_theme_mode(self, value: str) -> None:
        self.set_value(SettingKey.THEME_MODE, value, SettingValueType.STRING)

    def get_default_delay_seconds(self) -> int:
        return self.get_int(
            SettingKey.DEFAULT_DELAY_SECONDS,
            int(DEFAULT_SETTINGS[SettingKey.DEFAULT_DELAY_SECONDS][0]),
        )

    def set_default_delay_seconds(self, value: int) -> None:
        self.set_value(SettingKey.DEFAULT_DELAY_SECONDS, value, SettingValueType.INT)

    def get_default_outlook_account(self) -> str:
        return self.get_string(
            SettingKey.DEFAULT_OUTLOOK_ACCOUNT,
            DEFAULT_SETTINGS[SettingKey.DEFAULT_OUTLOOK_ACCOUNT][0],
        )

    def set_default_outlook_account(self, value: str) -> None:
        self.set_value(SettingKey.DEFAULT_OUTLOOK_ACCOUNT, value, SettingValueType.STRING)

    def get_window_size(self) -> tuple[int, int]:
        width = self.get_int(SettingKey.WINDOW_WIDTH, int(DEFAULT_SETTINGS[SettingKey.WINDOW_WIDTH][0]))
        height = self.get_int(
            SettingKey.WINDOW_HEIGHT, int(DEFAULT_SETTINGS[SettingKey.WINDOW_HEIGHT][0])
        )
        return width, height

    def set_window_size(self, width: int, height: int) -> None:
        self.set_value(SettingKey.WINDOW_WIDTH, width, SettingValueType.INT)
        self.set_value(SettingKey.WINDOW_HEIGHT, height, SettingValueType.INT)

    def get_window_maximized(self) -> bool:
        return self.get_bool(
            SettingKey.WINDOW_MAXIMIZED,
            DEFAULT_SETTINGS[SettingKey.WINDOW_MAXIMIZED][0] == "true",
        )

    def set_window_maximized(self, value: bool) -> None:
        self.set_value(SettingKey.WINDOW_MAXIMIZED, value, SettingValueType.BOOL)

    def get_contact_import_column_mapping(self) -> dict[str, str]:
        """Return the remembered raw-header -> canonical-field mapping from the last manual import."""
        raw = self.get_json(SettingKey.CONTACT_IMPORT_COLUMN_MAPPING, {})
        return raw if isinstance(raw, dict) else {}

    def set_contact_import_column_mapping(self, mapping: dict[str, str]) -> None:
        self.set_value(SettingKey.CONTACT_IMPORT_COLUMN_MAPPING, mapping, SettingValueType.JSON)
