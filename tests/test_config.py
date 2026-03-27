from __future__ import annotations

from pathlib import Path

import pytest

from verse_switcher.config import AppConfig, load_config, save_config


def test_save_load_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import verse_switcher.config as c

    monkeypatch.setattr(c, "user_config_dir", lambda *a, **k: str(tmp_path))
    cfg = AppConfig(game_root="D:/games/StarCitizen", allow_patterns=["D:/games/*"])
    save_config(cfg)
    loaded = load_config()
    assert loaded.game_root == "D:/games/StarCitizen"
    assert loaded.allow_patterns == ["D:/games/*"]


def test_load_corrupt_returns_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import verse_switcher.config as c

    monkeypatch.setattr(c, "user_config_dir", lambda *a, **k: str(tmp_path))
    p = tmp_path / "config.json"
    p.write_text("not json", encoding="utf-8")
    loaded = load_config()
    assert isinstance(loaded.allow_patterns, list)
    assert loaded.game_root
