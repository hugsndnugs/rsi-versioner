from __future__ import annotations

import logging
import os
from collections.abc import Generator
from pathlib import Path

import pytest

from verse_switcher.core import (
    DetectionResult,
    LivePtuState,
    paths_equal,
    validate_undo_expected_state,
)
from verse_switcher.logging_config import LOGGER_NAME, configure_logging
from verse_switcher.undo_state import UndoRecord, clear_undo_record, load_undo_record, save_undo_record


@pytest.fixture(autouse=True)
def clear_rsi_logger_handlers() -> Generator[None, None, None]:
    log = logging.getLogger(LOGGER_NAME)
    log.handlers.clear()
    yield None
    log.handlers.clear()


def test_validate_undo_expected_state() -> None:
    det = DetectionResult(LivePtuState.PTU_ONLY, None, Path("x"))
    assert validate_undo_expected_state(det, LivePtuState.PTU_ONLY)
    assert not validate_undo_expected_state(det, LivePtuState.LIVE_ONLY)


@pytest.mark.skipif(os.name != "nt", reason="Windows path case semantics")
def test_paths_equal_case_insensitive_windows(tmp_path: Path) -> None:
    a = tmp_path / "StarCitizen"
    a.mkdir()
    assert paths_equal(Path(str(a).upper()), Path(str(a).lower()))


def test_paths_equal_distinct_dirs(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    assert paths_equal(tmp_path / "a", tmp_path / "a")
    assert not paths_equal(tmp_path / "a", tmp_path / "b")


def test_configure_logging_writes_file(tmp_path: Path) -> None:
    configure_logging(log_dir=tmp_path)
    log = logging.getLogger(LOGGER_NAME)
    log.info("event=test_swap root=/tmp/x dry_run=False ok=True action=rename msg=ok")
    log_file = tmp_path / "verse_switcher.log"
    assert log_file.is_file()
    text = log_file.read_text(encoding="utf-8")
    assert "event=test_swap" in text
    assert "INFO" in text


def test_undo_record_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import verse_switcher.undo_state as u

    monkeypatch.setattr(u, "user_config_dir", lambda *a, **k: str(tmp_path))
    clear_undo_record()
    rec = UndoRecord(
        game_root_resolved="C:/games/StarCitizen",
        state_before=LivePtuState.LIVE_ONLY.value,
        state_after=LivePtuState.PTU_ONLY.value,
    )
    save_undo_record(rec)
    loaded = load_undo_record()
    assert loaded is not None
    assert loaded.game_root_resolved == rec.game_root_resolved
    assert loaded.state_before == rec.state_before
    assert loaded.state_after == rec.state_after


def test_undo_record_from_dict_rejects_bad_state() -> None:
    assert UndoRecord.from_dict({}) is None
    assert (
        UndoRecord.from_dict(
            {
                "game_root_resolved": "/x",
                "state_before": "both",
                "state_after": "live_only",
            }
        )
        is None
    )
