# Building & Installing the Windows Executable

This folder contains everything needed to package Star Season Campaign
Manager as a standalone Windows executable -- no Python, no terminal, no
VS Code required to run it once built.

## Building the .exe (do this once, on a Windows machine)

**Requirements on the build machine:**
- Windows 10/11
- Python 3.13 installed and on PATH
- Outlook Classic installed (only needed to *test* the Outlook features
  afterward, not to build)

**Steps:**

1. Copy the whole project folder onto the Windows machine.
2. Double-click `packaging\build_windows.bat` (or run it from `cmd.exe`).
   It will:
   - create a virtual environment (`.venv`) if one doesn't exist,
   - install every dependency from `requirements.txt` (including
     `pywin32`, which only installs on Windows),
   - run PyInstaller using `packaging\star_season_campaign_manager.spec`.
3. When it finishes, you'll have:
   ```
   dist\StarSeasonCampaignManager\StarSeasonCampaignManager.exe
   ```
   along with every DLL/data file it needs, all in that one folder.

This only needs to be done once per machine/version -- after that, you
can copy the entire `dist\StarSeasonCampaignManager\` folder to any
other Windows machine and it will run without needing Python installed
there at all.

## Installing / running the built app

1. Copy the entire `dist\StarSeasonCampaignManager\` folder to wherever
   you want the app to live (Desktop, `C:\Program Files\`, a USB drive,
   etc.). Every file in that folder must stay together.
2. Double-click `StarSeasonCampaignManager.exe` (or the included
   `Run Star Season Campaign Manager.bat` shortcut) to launch. No
   terminal window appears -- just the application.
3. On first launch, the app creates its own `data\`, `logs\`,
   `templates\`, and `reports\` folders next to the executable and sets
   up the database automatically.
4. (Optional) To create a Desktop shortcut: right-click
   `StarSeasonCampaignManager.exe` -> **Send to** -> **Desktop (create
   shortcut)**.

## Icon

`assets/icons/app_icon.ico` is a generic placeholder badge (a blue "SS"
monogram in the app's own brand color) -- **not** Star Season's real
logo, since no official logo file was provided to build from. Replace
`assets/icons/app_icon.ico` with the real company logo (converted to
`.ico`, ideally containing 16/32/48/128/256 px sizes) and rebuild
whenever the actual logo is available.

## Updating the app later

Re-run `packaging\build_windows.bat` after pulling/copying in new code.
It rebuilds `dist\StarSeasonCampaignManager\` from scratch; your data
(`data\star_season.db`, `logs\`) lives *next to* the .exe and is not
touched by a rebuild as long as you rebuild into the same folder or
copy your `data\` folder over afterward.

## Troubleshooting

- **"Windows protected your PC" SmartScreen warning**: expected for an
  unsigned .exe. Click **More info** -> **Run anyway**. Code-signing the
  executable is a separate step not covered here.
- **Antivirus flags the .exe**: common with PyInstaller-built apps built
  without a code signature. Add an exclusion for the app's folder if
  needed.
- **Outlook features don't work**: they require Outlook Classic (not
  the new Outlook for Windows app) to be installed and set up on the
  machine running the .exe.
