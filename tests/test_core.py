from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from rsi_versioner.core import (
    LivePtuState,
    detect_live_ptu,
    path_matches_allowlist,
    resolve_game_root,
    swap_live_ptu,
)


def test_path_matches_allowlist_exact(tmp_path: Path) -> None:
    root = tmp_path / "Roberts Space Industries" / "StarCitizen"
    root.mkdir(parents=True)
    resolved = resolve_game_root(root)
    pat = str(resolved).replace("\\", "/")
    assert path_matches_allowlist(resolved, [pat])


def test_path_matches_allowlist_star_prefix(tmp_path: Path) -> None:
    root = tmp_path / "x" / "Roberts Space Industries" / "StarCitizen"
    root.mkdir(parents=True)
    resolved = resolve_game_root(root)
    assert path_matches_allowlist(
        resolved,
        ["*/Roberts Space Industries/StarCitizen"],
    )


def test_path_matches_allowlist_rejects(tmp_path: Path) -> None:
    root = tmp_path / "unsafe" / "StarCitizen"
    root.mkdir(parents=True)
    resolved = resolve_game_root(root)
    assert not path_matches_allowlist(
        resolved,
        ["*/Roberts Space Industries/StarCitizen"],
    )


def test_detect_live_only(tmp_path: Path) -> None:
    game = tmp_path / "StarCitizen"
    game.mkdir()
    (game / "LIVE").mkdir()
    d = detect_live_ptu(game)
    assert d.state == LivePtuState.LIVE_ONLY
    assert d.live_path is not None
    assert d.ptu_path is None


def test_detect_ptu_only(tmp_path: Path) -> None:
    game = tmp_path / "StarCitizen"
    game.mkdir()
    (game / "ptu").mkdir()
    d = detect_live_ptu(game)
    assert d.state == LivePtuState.PTU_ONLY


def test_detect_both(tmp_path: Path) -> None:
    game = tmp_path / "StarCitizen"
    game.mkdir()
    (game / "LIVE").mkdir()
    (game / "PTU").mkdir()
    d = detect_live_ptu(game)
    assert d.state == LivePtuState.BOTH


def test_detect_neither(tmp_path: Path) -> None:
    game = tmp_path / "StarCitizen"
    game.mkdir()
    d = detect_live_ptu(game)
    assert d.state == LivePtuState.NEITHER


def test_swap_live_to_ptu(tmp_path: Path) -> None:
    game = tmp_path / "Roberts Space Industries" / "StarCitizen"
    game.mkdir(parents=True)
    live = game / "LIVE"
    live.mkdir()
    pat = str(resolve_game_root(game)).replace("\\", "/")
    out = swap_live_ptu(game, [pat], dry_run=False)
    assert out.ok
    assert (game / "PTU").is_dir()
    assert not live.exists()


def test_swap_ptu_to_live(tmp_path: Path) -> None:
    game = tmp_path / "Roberts Space Industries" / "StarCitizen"
    game.mkdir(parents=True)
    ptu = game / "PTU"
    ptu.mkdir()
    pat = str(resolve_game_root(game)).replace("\\", "/")
    out = swap_live_ptu(game, [pat], dry_run=False)
    assert out.ok
    assert (game / "LIVE").is_dir()
    assert not ptu.exists()


def test_swap_dry_run_no_change(tmp_path: Path) -> None:
    game = tmp_path / "Roberts Space Industries" / "StarCitizen"
    game.mkdir(parents=True)
    (game / "LIVE").mkdir()
    pat = str(resolve_game_root(game)).replace("\\", "/")
    out = swap_live_ptu(game, [pat], dry_run=True)
    assert out.ok
    assert (game / "LIVE").is_dir()
    assert not (game / "PTU").exists()


def test_swap_blocked_without_allowlist(tmp_path: Path) -> None:
    game = tmp_path / "StarCitizen"
    game.mkdir()
    (game / "LIVE").mkdir()
    out = swap_live_ptu(game, ["*/Roberts Space Industries/StarCitizen"], dry_run=True)
    assert not out.ok


def test_swap_both_folders_refused(tmp_path: Path) -> None:
    game = tmp_path / "Roberts Space Industries" / "StarCitizen"
    game.mkdir(parents=True)
    (game / "LIVE").mkdir()
    (game / "PTU").mkdir()
    pat = str(resolve_game_root(game)).replace("\\", "/")
    out = swap_live_ptu(game, [pat], dry_run=True)
    assert not out.ok


def test_swap_permission_error_returns_friendly_message(tmp_path: Path) -> None:
    game = tmp_path / "Roberts Space Industries" / "StarCitizen"
    game.mkdir(parents=True)
    (game / "LIVE").mkdir()
    pat = str(resolve_game_root(game)).replace("\\", "/")
    with patch("pathlib.Path.rename", side_effect=PermissionError("denied")):
        out = swap_live_ptu(game, [pat], dry_run=False)
    assert not out.ok
    assert "Permission denied" in out.message


def test_swap_rename_oserror_is_reported(tmp_path: Path) -> None:
    game = tmp_path / "Roberts Space Industries" / "StarCitizen"
    game.mkdir(parents=True)
    (game / "PTU").mkdir()
    pat = str(resolve_game_root(game)).replace("\\", "/")
    with patch("pathlib.Path.rename", side_effect=OSError("disk error")):
        out = swap_live_ptu(game, [pat], dry_run=False)
    assert not out.ok
    assert "Rename failed" in out.message
