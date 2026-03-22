from __future__ import annotations

from pathlib import Path

from rsi_versioner.core import (
    DetectionResult,
    LivePtuState,
    pattern_usable_as_game_root,
    preview_label_from_swap,
    swap_buttons_view,
)


def test_preview_label_from_swap() -> None:
    assert preview_label_from_swap("Swap (set game root)") == "Preview (set game root)"
    assert preview_label_from_swap("Swap: LIVE → PTU") == "Preview: LIVE → PTU"
    assert preview_label_from_swap("Swap: PTU → LIVE") == "Preview: PTU → LIVE"


def test_pattern_usable_as_game_root() -> None:
    assert pattern_usable_as_game_root("C:/Program Files/Roberts Space Industries/StarCitizen")
    assert pattern_usable_as_game_root("  D:/games/foo  ")
    assert not pattern_usable_as_game_root("")
    assert not pattern_usable_as_game_root("   ")
    assert not pattern_usable_as_game_root("*/Roberts Space Industries/StarCitizen")
    assert not pattern_usable_as_game_root("C:/foo?/bar")
    assert not pattern_usable_as_game_root("C:/foo[1]/bar")


def test_swap_buttons_no_root() -> None:
    st, en, _, pn = swap_buttons_view(
        root_non_empty=False,
        resolve_failed=False,
        resolved=None,
        patterns_non_empty=True,
        allowed=False,
        det=None,
    )
    assert not en and not pn
    assert "set game root" in st.lower()


def test_swap_buttons_resolve_failed() -> None:
    st, en, *_ = swap_buttons_view(
        root_non_empty=True,
        resolve_failed=True,
        resolved=None,
        patterns_non_empty=True,
        allowed=False,
        det=None,
    )
    assert not en
    assert "invalid" in st.lower()


def test_swap_buttons_allowlist_empty(tmp_path: Path) -> None:
    d = tmp_path / "root"
    d.mkdir()
    st, en, _, _ = swap_buttons_view(
        root_non_empty=True,
        resolve_failed=False,
        resolved=d,
        patterns_non_empty=False,
        allowed=False,
        det=DetectionResult(LivePtuState.NEITHER, None, None),
    )
    assert not en
    assert "allowlist empty" in st.lower()


def test_swap_buttons_not_dir(tmp_path: Path) -> None:
    p = tmp_path / "file.txt"
    p.write_text("x", encoding="utf-8")
    st, en, _, _ = swap_buttons_view(
        root_non_empty=True,
        resolve_failed=False,
        resolved=p,
        patterns_non_empty=True,
        allowed=True,
        det=DetectionResult(LivePtuState.NEITHER, None, None),
    )
    assert not en
    assert "not a directory" in st.lower()


def test_swap_buttons_blocked_allowlist(tmp_path: Path) -> None:
    d = tmp_path / "g"
    d.mkdir()
    st, en, _, _ = swap_buttons_view(
        root_non_empty=True,
        resolve_failed=False,
        resolved=d,
        patterns_non_empty=True,
        allowed=False,
        det=DetectionResult(LivePtuState.LIVE_ONLY, d / "LIVE", None),
    )
    assert not en
    assert "allowlist" in st.lower()


def test_swap_buttons_both_and_neither(tmp_path: Path) -> None:
    d = tmp_path / "both"
    d.mkdir()
    st, en, _, _ = swap_buttons_view(
        root_non_empty=True,
        resolve_failed=False,
        resolved=d,
        patterns_non_empty=True,
        allowed=True,
        det=DetectionResult(LivePtuState.BOTH, d / "LIVE", d / "PTU"),
    )
    assert not en
    assert "both" in st.lower()

    st2, en2, _, _ = swap_buttons_view(
        root_non_empty=True,
        resolve_failed=False,
        resolved=d,
        patterns_non_empty=True,
        allowed=True,
        det=DetectionResult(LivePtuState.NEITHER, None, None),
    )
    assert not en2
    assert "no LIVE" in st2 or "PTU" in st2


def test_swap_buttons_live_and_ptu_enabled(tmp_path: Path) -> None:
    d = tmp_path / "live"
    d.mkdir()
    st, en, pt, pn = swap_buttons_view(
        root_non_empty=True,
        resolve_failed=False,
        resolved=d,
        patterns_non_empty=True,
        allowed=True,
        det=DetectionResult(LivePtuState.LIVE_ONLY, d / "LIVE", None),
    )
    assert en and pn
    assert "LIVE" in st and "PTU" in st
    assert st.startswith("Swap:")
    assert pt.startswith("Preview:")

    d2 = tmp_path / "ptu"
    d2.mkdir()
    st2, en2, _, _ = swap_buttons_view(
        root_non_empty=True,
        resolve_failed=False,
        resolved=d2,
        patterns_non_empty=True,
        allowed=True,
        det=DetectionResult(LivePtuState.PTU_ONLY, None, d2 / "PTU"),
    )
    assert en2
    assert "PTU" in st2 and "LIVE" in st2
