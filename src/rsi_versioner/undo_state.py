from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from platformdirs import user_config_dir

from rsi_versioner.core import LivePtuState

APP_NAME = "rsi-versioner"
UNDO_FILENAME = "undo.json"


def undo_path() -> Path:
    return Path(user_config_dir(APP_NAME, appauthor=False)) / UNDO_FILENAME


@dataclass
class UndoRecord:
    """Last successful on-disk swap; undo reverses to state_before."""

    game_root_resolved: str
    state_before: str  # LivePtuState value
    state_after: str  # LivePtuState value

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> UndoRecord | None:
        try:
            gr = str(data["game_root_resolved"])
            sb = str(data["state_before"])
            sa = str(data["state_after"])
        except (KeyError, TypeError, ValueError):
            return None
        if sb not in {s.value for s in LivePtuState}:
            return None
        if sa not in {s.value for s in LivePtuState}:
            return None
        if sb not in (LivePtuState.LIVE_ONLY.value, LivePtuState.PTU_ONLY.value):
            return None
        if sa not in (LivePtuState.LIVE_ONLY.value, LivePtuState.PTU_ONLY.value):
            return None
        return cls(game_root_resolved=gr, state_before=sb, state_after=sa)


def load_undo_record() -> UndoRecord | None:
    path = undo_path()
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    return UndoRecord.from_dict(data)


def save_undo_record(record: UndoRecord) -> None:
    path = undo_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(record.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def clear_undo_record() -> None:
    path = undo_path()
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
