"""
Root-level launcher.

Kept intentionally tiny: this is the script PyInstaller will point at
(`pyinstaller main.py`) and the file a developer runs with
`python main.py`. All real startup logic lives in `app/main.py`.
"""

import sys

from app.main import main

if __name__ == "__main__":
    sys.exit(main())
