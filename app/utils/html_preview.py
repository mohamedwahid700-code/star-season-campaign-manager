"""
HTML preview utility.

The project's tech stack has no embedded HTML rendering widget, so
"render final HTML exactly as the recipient will receive it" is
satisfied by writing the rendered HTML to a temporary file and opening
it in the user's default web browser via the standard library's
`webbrowser` module -- real, pixel-accurate rendering, with zero extra
dependencies.
"""

from __future__ import annotations

import logging
import tempfile
import webbrowser
from pathlib import Path

logger = logging.getLogger(__name__)

_HTML_WRAPPER = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 24px; color: #111827; }}
  img {{ max-width: 100%; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def open_html_preview(html_body: str, subject: str = "Preview") -> Path:
    """Write `html_body` to a temp file wrapped in a minimal document and open it."""
    document = _HTML_WRAPPER.format(title=subject or "Preview", body=html_body)

    temp_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    )
    try:
        temp_file.write(document)
    finally:
        temp_file.close()

    path = Path(temp_file.name)
    logger.info("Opening HTML preview in system browser: %s", path)
    webbrowser.open(path.as_uri())
    return path
