## Summary

- First stable (1.0) release: swap LIVE ↔ PTU under the game root with allowlist checks, dry run/preview, one-step undo, and rotating logs.
- Windows-first: portable `verse-switcher.exe`, installer, and documented Program Files / elevation guidance.
- Source installs via `pip` / setuptools-scm versioning; see `LICENSE` (MIT).

## Artifacts

- `verse-switcher.exe` (portable)
- `verse-switcher-setup.exe` (installer)
- `SHA256SUMS.txt`

## Validation

- [ ] `pytest -q --tb=short`
- [ ] Portable executable launch test
- [ ] Installer install/uninstall test
- [ ] `Run-Verse-Switcher.cmd` install-or-run flow test
