# Star Season Campaign Manager

A commercial Windows desktop application for managing Outlook email campaigns
for exhibition and conference participants.

**Company:** Star Season for Exhibitions & Conferences
**Sprint:** Sprint 2 — Contact & Campaign Management
**Status:** Foundation (Sprint 1) + Contacts, Campaigns, and Templates
(Sprint 2) complete. Outlook sending, the email queue, and send delays are
built in a later sprint on top of this scaffold.

---

## What Sprint 1 included

- Full project structure (MVC + Repository Pattern + Service Layer)
- SQLite database with SQLAlchemy models for every core entity: campaigns,
  contacts, templates, history, blacklist, settings, logs
- A working settings manager (company name, language, theme, delay, default
  Outlook account, window size) persisted to the database
- A professional, themeable (light/dark) desktop UI: sidebar navigation, top
  bar, status bar, and all eight pages (Dashboard, Campaigns, Contacts,
  Templates, History, Reports, Settings, About)
- Daily rotating file logging
- Environment-based configuration

## What Sprint 2 added

- **Contact Management**: full CRUD, search, sort, and country filtering
  against a real exhibition-specific schema (company, email, country,
  website, phone, contact name, stand number, notes)
- **Excel/CSV contact import**: pick a file, preview every row classified as
  Imported / Skipped / Invalid / Duplicate before anything is written, then
  commit only the valid rows
- **Contact export** back to Excel or CSV
- **Campaign Management**: Create, Edit, Duplicate, Archive/Restore, and
  Delete, with its own name, event name, language, subject, and HTML body
- **Template library**: a separate, reusable set of HTML templates a
  campaign can be seeded from
- **Rich text HTML editor**: bold/italic/underline, bullet & numbered lists,
  links, embedded images, text alignment, RTL/LTR, undo/redo -- shared by
  both the Campaign and Template editors
- **Mail-merge variables**: `{Company}`, `{EventName}`, `{Website}`,
  `{Country}`, `{Stand}`, `{ContactName}`, `{SenderName}`, `{WhatsApp}`,
  inserted from a side panel and substituted with a real contact's data
- **Preview**: renders the final HTML with variables replaced and opens it in
  the system's default web browser -- pixel-accurate, exactly as a recipient
  would see it
- A lightweight, additive schema-migration mechanism so upgrading from
  Sprint 1's database never loses existing data

No campaign sending, Outlook integration, email queueing, or send delays are
implemented yet -- by design, per the Sprint 2 scope.

---

## Requirements

- **Python 3.13** (Windows 10/11 recommended for full pywin32/Outlook support
  in later sprints)
- pip

## Installation

```bash
# 1. Clone or copy the project, then from the project root:
python -m venv .venv

# 2. Activate the virtual environment
#    Windows (PowerShell):
.venv\Scripts\Activate.ps1
#    Windows (cmd.exe):
.venv\Scripts\activate.bat

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) create your own environment file
copy .env.example .env
```

## Running the application

```bash
python main.py
```

On first run, the application will:

1. Create `data/star_season.db` (SQLite database) and every table.
2. Seed default settings (company name, theme, language, delay, window size).
3. Open the main window on the Dashboard.

If you're upgrading an existing Sprint 1 database, additive migrations run
automatically on startup to add the new Contact/Campaign columns -- nothing
is dropped and no existing data is lost.

## Building a standalone .exe (PyInstaller)

```bash
pyinstaller --name "StarSeasonCampaignManager" --windowed --onedir main.py
```

The generated executable will be under `dist/StarSeasonCampaignManager/`.
Remember to ship the `assets/`, `templates/`, and `.env` (if used) alongside
the executable, or use `--add-data` to bundle them.

## Project structure

```
app/
  config/       # AppConfig (env/deployment) + static constants
  controllers/  # MVC controllers: mediate between views and services
  database/     # SQLAlchemy engine/session, schema init, migrations
  models/       # SQLAlchemy ORM entities (campaigns, contacts, ...)
  repositories/ # Repository Pattern: all data access, one repo per model
  services/     # Service layer: settings, logging, contacts, campaigns,
                # templates, import/export, variable rendering
  ui/
    components/ # Sidebar, top bar, status bar, data table, HTML editor,
                # confirm dialog, variables panel, shared widgets
    dialogs/    # Modal create/edit/import dialogs
    theme/      # Brand color palette + ThemeManager (light/dark)
    views/      # One page per sidebar item, all subclassing BaseView
  utils/        # Logger setup, path resolution, validators, HTML preview
  main.py       # Application entry point (logging -> DB init -> UI)
assets/
  icons/
  images/
templates/      # Future: saved HTML email templates on disk
reports/        # Future: generated report exports
logs/           # Daily rotating log files (app.log, app.log.YYYY-MM-DD, ...)
main.py         # Thin root launcher -> app.main.main()
requirements.txt
.env.example
```

## Architecture notes

- **MVC:** Models (`app/models`) are plain SQLAlchemy entities. Views
  (`app/ui/views`) are CustomTkinter frames with zero data access. Controllers
  (`app/controllers`) are the only bridge between the two.
- **Repository Pattern:** every table has a dedicated repository
  (`app/repositories`) responsible for all querying/persistence. Nothing above
  the repository layer constructs a SQLAlchemy session or query directly.
- **Service Layer:** `SettingsService`, `LoggingService`, `ContactService`,
  `ContactImportExportService`, `CampaignService`, `TemplateService`, and
  `TemplateRenderingService` hold all business logic. Later sprints add
  `OutlookService`, an email queue service, etc. alongside these without
  touching existing code.
- **Migrations:** `app/database/migrations.py` is a small, additive,
  idempotent alternative to a full migration framework (no Alembic in this
  project's tech stack). It only ever adds columns and backfills data --
  never drops anything -- so upgrading between sprints is always safe.
- **HTML editor design:** CustomTkinter/Tkinter has no `contentEditable`
  widget, so the rich text editor is built on `tkinter.Text`'s native tag
  system (real bold/italic/underline/alignment rendering), with HTML
  import/export via BeautifulSoup4, and images embedded as base64 data URIs
  via Pillow so the resulting HTML is fully self-contained.
- **Preview rendering:** variable substitution uses a small whitelisted regex
  rather than reconfiguring Jinja2's delimiters, since campaign HTML routinely
  contains inline CSS whose curly braces would otherwise be misparsed as
  template expressions. Preview opens the rendered HTML in the system's
  default browser (via the standard library's `webbrowser` module) for a
  pixel-accurate result with no extra dependencies.
- **Extensibility by design:** the `settings` table is a generic key/value
  store (not one column per setting), navigation is driven by a single
  `NavigationKey` enum + a dict of view classes, and every ORM relationship
  needed by future features (Campaign ↔ Template, Campaign/Contact ↔ History)
  is already modeled, even though nothing writes to History yet.

## License

Proprietary — © Star Season for Exhibitions & Conferences. All rights reserved.
