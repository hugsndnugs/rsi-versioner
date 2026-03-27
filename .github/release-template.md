## Summary

- First stable (1.0) release: swap LIVE ↔ PTU under the game root with allowlist checks, dry run/preview, one-step undo, and rotating logs.
- Windows-first: portable `rsi-versioner.exe`, installer, and documented Program Files / elevation guidance.
- Source installs via `pip` / setuptools-scm versioning; see `LICENSE` (MIT).

## Artifacts

- `rsi-versioner.exe` (portable)
- `rsi-versioner-setup.exe` (installer)
- `SHA256SUMS.txt`

## Validation

- [ ] `pytest -q --tb=short`
- [ ] Portable executable launch test
- [ ] Installer install/uninstall test
- [ ] `Run-RSI-Versioner.cmd` install-or-run flow test
