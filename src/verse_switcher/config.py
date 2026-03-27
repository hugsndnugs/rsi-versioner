from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

from platformdirs import user_config_dir

APP_NAME = "verse-switcher"
CONFIG_FILENAME = "config.json"


def default_game_root() -> str:
    if os.name == "nt":
        return str(
            Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
            / "Roberts Space Industries"
            / "StarCitizen"
        )
    return str(Path.home() / "Games" / "StarCitizen")


def default_allow_patterns() -> list[str]:
    root = default_game_root().replace("\\", "/")
    return [
        root,
        "*/Roberts Space Industries/StarCitizen",
    ]


@dataclass
class AppConfig:
    game_root: str = field(default_factory=default_game_root)
    allow_patterns: list[str] = field(default_factory=default_allow_patterns)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> AppConfig:
        return cls(
            game_root=str(data.get("game_root", default_game_root())),
            allow_patterns=list(
                data.get("allow_patterns") or default_allow_patterns()
            ),
        )


def config_path() -> Path:
    return Path(user_config_dir(APP_NAME, appauthor=False)) / CONFIG_FILENAME


def load_config() -> AppConfig:
    path = config_path()
    if not path.is_file():
        return AppConfig()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return AppConfig()
        return AppConfig.from_dict(data)
    except (OSError, ValueError, TypeError):
        return AppConfig()


def save_config(cfg: AppConfig) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(cfg.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
