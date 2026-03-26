# Releasing RSI Versioner

This project publishes a GitHub release when a tag matching `v*.*.*` is pushed.

## What gets published

- Python source artifacts (`sdist`, `wheel`)
- `rsi-versioner.exe` (portable Windows app)
- `rsi-versioner-setup.exe` (Windows installer)
- `SHA256SUMS.txt` (SHA256 for Windows binaries)

## Pre-release checklist

1. Ensure CI is green on the target branch.
2. Run local tests:
   - `pytest -q --tb=short`
3. Verify local packaging flow on Windows:
   - `.\scripts\build_portable.ps1`
   - `.\scripts\build_installer.ps1`
4. Smoke test:
   - Launch `dist\rsi-versioner.exe`
   - Install and launch via `dist\rsi-versioner-setup.exe`
   - Launch via `Run-RSI-Versioner.cmd`
5. Update docs for user-visible changes (`README.md`, troubleshooting notes).

## Cut release

1. Create and push the version tag:
   - `git tag v1.0.0`
   - `git push origin v1.0.0`
2. Wait for the `Release` workflow to finish.
3. Confirm release assets are attached and checksums look correct.
4. Publish release notes on GitHub.

## Supported target for v1

- Windows 10/11
- Game roots under:
  - `%ProgramFiles%\Roberts Space Industries\StarCitizen` (may require elevation)
  - User-owned library paths matched by allowlist patterns
