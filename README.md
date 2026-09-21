# VELORA PANEL

**VELORA PANEL** is a control panel for launching multiple CS2 accounts and automating case farming.

Created in 2 months using Chat GPT.


## 📌 Requirements

| Requirement   | Note                      |
| ------------- | ------------------------- |
| Python 3.13   | Required to run the panel |
| Steam         | Latest version            |
| CS2           | Latest version            |
| Handle.exe    | utility with google       |

**Handle.exe** - https://learn.microsoft.com/ru-ru/sysinternals/downloads/handle

> ⚠️ Important: Make sure `cmd` always runs as administrator for proper functionality.

---

## 🛠 Installation


1. Install dependencies:

* win - cmd "run as administrator"
* cd {path to folder}
* pip install -r requirements.txt

2. Run the panel:

* cd {insert path to folder}
* py main.py

---
## 🛠 Troubleshooting



### Accounts or games fail to launch/accept
**Issue:** The panel does not trigger the game client, or accounts do not start at all.
**Solution:** The panel must be run with **Administrator privileges**.

### How to compile into an .exe file?
1. Open **Command Prompt (CMD)** as **Administrator**.
2. cd {path to folder}
3. pyinstaller --onefile --noconsole --clean --name "VeloraPanel" --icon=Icon1.ico --add-data "Icon1.ico;." --uac-admin main.py

---

## ⚙ Account Setup
1. To add accounts, place your `maFiles` (optional) in the `mafiles` folder.
2. Add logins and passwords in the `logpass.txt` file in the format:

```
login:password
```

---

## 🚀 Usage

* The panel allows launching multiple CS2 accounts simultaneously.
* Automatically arranges windows and collects lobbies.
* Works with accounts listed in `logpass.txt` and `maFiles`.


### Functional

* The panel automatically farms keys in cs2, but does not automatically collect items.

### Drop stats

* A drop report was implemented on the history of the sent trade.

## Security and reliability notes

* Steam passwords and account secrets are imported on first use into `secrets.dat`, protected by Windows DPAPI for the current Windows user. The legacy `logpass.txt` file is retained for compatibility and can be removed manually after migration is verified.
* A DPAPI error is reported explicitly; the panel does not silently replace or overwrite credentials.
* Stale `runtime.json` entries are pruned only when their PIDs resolve to the expected `steam.exe` and `cs2.exe` process names.
* Runtime records also store process creation times, preventing a reused PID from being attached to the wrong account. Older records remain readable and are upgraded on the next launch.
* Settings are type-checked at load time, including GSI token length, Telegram ACL values, looter limits, and trade-link format.
* UI log messages redact passwords, Steam secrets, bot/GSI tokens, and trade-link tokens.
* GSI rejects non-JSON or oversized payloads and ignores identical events received repeatedly within 30 seconds.
* FSM settings can be imported explicitly with `SettingsManager.import_fsm_file(path, overwrite=False)`. Only known non-secret settings are mapped; Telegram tokens and credentials are never imported.
* Optional process tuning (`ProcessPriority`, `ProcessAffinity`) follows the useful FSM/BES watch concept, but is disabled by default (`normal` priority, empty affinity) and never uses broad process termination.
* The default Steam/CS2 launch profile was refreshed for the current Steam client and CS2 runtime: obsolete Steam bootstrap flags and legacy renderer/workaround flags were removed. Keep only options required by your local windowed/farm workflow.
* Steam and CS2 installations are now discovered from the Steam registry and `libraryfolders.vdf`, including libraries outside the default `Program Files` directory. The CS2 executable is verified at `game/bin/win64/cs2.exe` before use.
* Each startup runs a non-destructive preflight for Steam, CS2, Node.js, GSI configuration, and token validity. Results are printed and written to the SQLite audit database `velora.db`.
* UI logs and startup checks are recorded in `velora.db`; credentials and secret values are redacted before logging.
* Steam-facing login and trade operations use per-account pacing. Throttle/authentication failures trigger a cooldown instead of repeated retries, while normal account and trade functionality remains available.
* FSM compatibility now covers its automation profile: auto-disconnect, anti-AFK, map-load, batch rotation, lobby mode, farming mode, 2v2, drop history, round target, login attempts, Ancient preload and auto-accept read time. Imported values are validated and do not overwrite secrets.
* Lobby search now uses validated `SearchRetriesBeforeShuffle` and `GameSearchTimeout` settings instead of hard-coded recovery limits.
* Account launches are paced by default (8 seconds post-launch, 20 seconds between accounts) to avoid burst authentication and process storms. These are safety delays, not disabled features, and can be adjusted upward in settings.
* CS2 startup is correlated only with the selected account's Steam process and its descendant `cs2.exe`; `CS2LaunchTimeout` (30-1800 seconds, default 180) prevents an unbounded wait when Steam or CS2 fails.
* The stop control terminates only processes owned by loaded VELORA account objects and their descendants. It does not kill unrelated Steam/CS2 instances or wipe the global Steam `userdata` directory.
* `TelegramAllowedChatIds` must contain the numeric Telegram chat IDs allowed to control the panel. An empty list disables remote commands (fail-closed).
* `GSIAuthToken` must match the `auth.token` value in `settings/gamestate_integration_fsn.cfg`.
* The panel writes `settings.json` and `runtime.json` atomically to avoid corrupting state when multiple worker threads update files.
* The dashboard includes read-only resource health telemetry for VELORA-owned Steam/CS2 processes and total system RAM; it does not read game memory or inject into CS2.
* Trade credentials are sent to `looter_core.js` through stdin rather than command-line arguments, so they are not exposed in the process command line.
* `LooterDryRun` defaults to `true`; disable it only after verifying the recipient and inventory settings.
* `LooterMaxItems` can cap the number of items processed per trade (`0` means no cap).
* Keep `logpass.txt`, `mafiles`, session files, and Telegram tokens private. Do not commit or share them.
