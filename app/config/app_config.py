"""
Application configuration manager.

This module is responsible for loading deployment-level configuration
(paths, database URL, debug flags) from environment variables / a `.env`
file. It is intentionally separate from `SettingsService`, which manages
*user-configurable* preferences (theme, language, default delay, etc.)
persisted in the database.

Rule of thumb:
    - AppConfig  -> "where things are" / "how the process is deployed"
    - Settings   -> "what the user prefers", editable at runtime from the UI
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


def _resolve_project_root() -> Path:
    """
    Resolve the directory user-writable data (database, logs) should
    live under.

    In a normal `python main.py` run this is simply the project root
    (three levels up from this file). When frozen by PyInstaller,
    `__file__` instead resolves *inside* the bundled `_internal` folder
    -- fine for read-only assets (see `app/utils/paths.py`), but wrong
    for user data, which should sit next to the .exe itself (found via
    `sys.executable`) rather than inside that implementation-detail
    folder, so it's easy to find/back up and survives a rebuild into
    the same output folder.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent


# Absolute path to the project root (three levels up from this file:
# app/config/app_config.py -> app/config -> app -> <project_root>) in a
# normal run, or the folder containing the .exe when frozen.
PROJECT_ROOT: Path = _resolve_project_root()

# Load the .env file (if present) once, at import time. This does not
# raise if the file is missing; sane defaults are provided below.
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")


def _get_bool(env_var: str, default: bool) -> bool:
    """Parse an environment variable as a boolean in a forgiving way."""
    raw = os.getenv(env_var)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _get_path(env_var: str, default: Path) -> Path:
    raw = os.getenv(env_var)
    if not raw:
        return default
    candidate = Path(raw)
    return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate


@dataclass(frozen=True)
class AppConfig:
    """
    Immutable, process-wide deployment configuration.

    Instances are cheap to create; `get_config()` below returns a cached
    singleton so the environment is only parsed once per process.
    """

    app_name: str = "Star Season Campaign Manager"
    company_name: str = "Star Season for Exhibitions & Conferences"
    environment: str = field(default_factory=lambda: os.getenv("APP_ENV", "production"))
    debug: bool = field(default_factory=lambda: _get_bool("APP_DEBUG", False))

    project_root: Path = PROJECT_ROOT
    data_dir: Path = field(default_factory=lambda: _get_path("APP_DATA_DIR", PROJECT_ROOT / "data"))
    logs_dir: Path = field(default_factory=lambda: _get_path("APP_LOGS_DIR", PROJECT_ROOT / "logs"))
    templates_dir: Path = field(default_factory=lambda: _get_path("APP_TEMPLATES_DIR", PROJECT_ROOT / "templates"))
    reports_dir: Path = field(default_factory=lambda: _get_path("APP_REPORTS_DIR", PROJECT_ROOT / "reports"))
    assets_dir: Path = field(default_factory=lambda: _get_path("APP_ASSETS_DIR", PROJECT_ROOT / "assets"))

    database_url: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL", "")
    )

    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())
    log_retention_days: int = field(default_factory=lambda: int(os.getenv("LOG_RETENTION_DAYS", "30")))

    def __post_init__(self) -> None:
        # `database_url` can't be derived from `self.data_dir` inside a
        # dataclass field's `default_factory` (it runs before `self`
        # exists), so it's finalized here instead: an explicit
        # DATABASE_URL environment variable always wins; otherwise the
        # database lives inside `data_dir`, so APP_DATA_DIR consistently
        # relocates both the directory and the database file together.
        if not self.database_url:
            resolved_url = f"sqlite:///{(self.data_dir / 'star_season.db').as_posix()}"
            object.__setattr__(self, "database_url", resolved_url)

    def ensure_directories(self) -> None:
        """Create every directory this configuration depends on, if missing."""
        for directory in (
            self.data_dir,
            self.logs_dir,
            self.templates_dir,
            self.reports_dir,
            self.assets_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)


_config_instance: AppConfig | None = None


def get_config() -> AppConfig:
    """Return the process-wide `AppConfig` singleton, creating it on first use."""
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig()
        _config_instance.ensure_directories()
    return _config_instance
