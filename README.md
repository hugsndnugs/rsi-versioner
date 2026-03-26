# RSI LIVE / PTU versioner

[![CI](https://github.com/hugsndnugs/rsi-versioner/actions/workflows/ci.yml/badge.svg)](https://github.com/hugsndnugs/rsi-versioner/actions/workflows/ci.yml)

Small Python GUI for swapping which Star Citizen build folder the RSI Launcher uses by renaming the **LIVE** and **PTU** directories under your **game root** (the folder that contains those two names as direct children).

## v1 Quick start (Windows)

If you downloaded the repo or release bundle, double-click:

- `Run-RSI-Versioner.cmd`

That launcher calls `scripts/Install-or-Run.ps1`, which installs RSI Versioner if needed and then opens the app.

## Downloads (v1+)

Each GitHub release publishes:

- `rsi-versioner.exe` (portable single-file app)
- `rsi-versioner-setup.exe` (installer)
- `SHA256SUMS.txt` (checksums)

## Install

```bash
pip install .
```

Optional dev dependencies: `pip install .[dev]`

## Run

```bash
rsi-versioner-gui
```

Or:

```bash
python -m rsi_versioner
```

Portable release artifact:

```powershell
.\rsi-versioner.exe
```

## Defaults and permissions

- **Default game root (Windows):** `%ProgramFiles%\Roberts Space Industries\StarCitizen`
- If the game lives under `Program Files`, renames may require running the app **as Administrator**, or set the game root to a library folder your user owns.
- If SmartScreen warns on first launch of a downloaded artifact, verify `SHA256SUMS.txt` from the release and allow the app once.

## Safety: allowlist (wildcard patterns)

Before any rename, the resolved absolute game root must match **at least one** glob pattern in the allowlist. Patterns use forward slashes; on Windows matching is **case-insensitive**. Default patterns include the standard RSI path and `*/Roberts Space Industries/StarCitizen` for other drives.

Add patterns for custom install locations. If nothing matches, the tool **blocks** the operation.

**Concrete path rows** (no `*`, `?`, or `[` in the pattern) can be applied as the game root with **Use selection as game root** or by double-clicking the row. Glob-only patterns cannot be used as a literal folder path.

## Behavior

| Folders under game root | Result |
|-------------------------|--------|
| Only `LIVE` | Renames `LIVE` → `PTU` |
| Only `PTU` | Renames `PTU` → `LIVE` |
| Both | Refused (duplicate installs) |
| Neither | Refused (wrong folder or not installed) |

Enable **Dry run** to preview without renaming. **Preview** always runs as a dry run. The **Swap** and **Preview** button labels update with the current folder state (e.g. `Swap: LIVE → PTU`) and are disabled when the action is not possible.

Settings (game root and allowlist) are saved under your user config directory when you close the window.

## Undo last rename

After a successful **non-dry** swap, the app stores a one-step undo record (resolved game root and the folder layout after the rename). **Undo last rename** reverses that single operation using the same allowlist and safety checks as Swap.

- The button is only enabled when the current **game root** matches that recorded path, the allowlist still matches, and the folders on disk still match the **post-swap** state. If you changed folders manually or pointed at another directory, undo is disabled or cancelled.
- Undo still requires a matching allowlist pattern (same as any rename).
- Another successful real swap **replaces** the undo record (only the latest rename is undoable).
- If the on-disk state no longer matches the record, the stale record is cleared when you refresh or when you start the app.

## Logging

Operations (preview, swap, undo) are appended to a **rotating log file** under the OS log directory for `rsi-versioner` (see [platformdirs](https://pypi.org/project/platformdirs/) `user_log_dir`), file name `rsi_versioner.log`. Use **Open log folder** in the GUI to open that directory. Timestamps are logged in UTC.

## Tests

```bash
pytest
```

## Build release artifacts locally (Windows)

```powershell
.\scripts\build_portable.ps1
.\scripts\build_installer.ps1
```
