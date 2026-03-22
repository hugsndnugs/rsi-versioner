from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class LivePtuState(str, Enum):
    LIVE_ONLY = "live_only"
    PTU_ONLY = "ptu_only"
    BOTH = "both"
    NEITHER = "neither"


@dataclass(frozen=True)
class DetectionResult:
    state: LivePtuState
    live_path: Path | None
    ptu_path: Path | None


@dataclass(frozen=True)
class SwapOutcome:
    ok: bool
    message: str
    dry_run: bool
    action: str | None  # e.g. "rename LIVE -> PTU"


def _norm_for_glob(s: str) -> str:
    s = s.replace("\\", "/")
    if os.name == "nt":
        s = s.lower()
    return s.rstrip("/")


def path_matches_allowlist(resolved_root: Path, patterns: list[str]) -> bool:
    """True if the resolved game root matches at least one glob pattern."""
    if not patterns:
        return False
    candidate = _norm_for_glob(str(resolved_root))
    for raw in patterns:
        pat = _norm_for_glob(str(raw).strip())
        if not pat:
            continue
        if fnmatch.fnmatch(candidate, pat):
            return True
    return False


def resolve_game_root(game_root: str | Path) -> Path:
    p = Path(game_root).expanduser()
    return p.resolve(strict=False)


def detect_live_ptu(game_root: Path) -> DetectionResult:
    live: Path | None = None
    ptu: Path | None = None
    if not game_root.is_dir():
        return DetectionResult(LivePtuState.NEITHER, None, None)
    for child in game_root.iterdir():
        if not child.is_dir():
            continue
        name = child.name.casefold()
        if name == "live":
            live = child
        elif name == "ptu":
            ptu = child
    if live and ptu:
        state = LivePtuState.BOTH
    elif live:
        state = LivePtuState.LIVE_ONLY
    elif ptu:
        state = LivePtuState.PTU_ONLY
    else:
        state = LivePtuState.NEITHER
    return DetectionResult(state, live, ptu)


def paths_equal(a: Path, b: Path) -> bool:
    """True if two paths refer to the same location (case-insensitive on Windows)."""
    ar = a.resolve(strict=False)
    br = b.resolve(strict=False)
    if os.name == "nt":
        return os.path.normcase(ar) == os.path.normcase(br)
    return ar == br


def validate_undo_expected_state(
    det: DetectionResult, expected_after: LivePtuState
) -> bool:
    """True if current disk state matches the post-swap state we recorded for undo."""
    return det.state == expected_after


def describe_detection(d: DetectionResult) -> str:
    match d.state:
        case LivePtuState.LIVE_ONLY:
            return "LIVE folder present; PTU absent."
        case LivePtuState.PTU_ONLY:
            return "PTU folder present; LIVE absent."
        case LivePtuState.BOTH:
            return "Both LIVE and PTU exist; remove or rename one before swapping."
        case LivePtuState.NEITHER:
            return "Neither LIVE nor PTU found under this game root."


def pattern_usable_as_game_root(s: str) -> bool:
    """True if the string can be copied into the game root field (not a glob pattern)."""
    t = s.strip()
    if not t:
        return False
    for ch in "*?[":
        if ch in t:
            return False
    return True


def preview_label_from_swap(swap_label: str) -> str:
    """Mirror the swap button label for the preview button."""
    if swap_label.startswith("Swap"):
        return "Preview" + swap_label[4:]
    return "Preview swap"


def swap_buttons_view(
    *,
    root_non_empty: bool,
    resolve_failed: bool,
    resolved: Path | None,
    patterns_non_empty: bool,
    allowed: bool,
    det: DetectionResult | None,
) -> tuple[str, bool, str, bool]:
    """
    (swap_text, swap_enabled, preview_text, preview_enabled) for toolbar buttons.
    """

    def pack(swap_t: str, en: bool) -> tuple[str, bool, str, bool]:
        p = preview_label_from_swap(swap_t)
        return (swap_t, en, p, en)

    if not root_non_empty:
        return pack("Swap (set game root)", False)
    if resolve_failed:
        return pack("Swap (invalid path)", False)
    if not patterns_non_empty:
        return pack("Swap (allowlist empty)", False)
    assert resolved is not None
    if not resolved.is_dir():
        return pack("Swap (not a directory)", False)
    if not allowed:
        return pack("Swap (blocked by allowlist)", False)
    assert det is not None
    if det.state == LivePtuState.BOTH:
        return pack("Swap (LIVE and PTU both present)", False)
    if det.state == LivePtuState.NEITHER:
        return pack("Swap (no LIVE or PTU folder)", False)
    if det.state == LivePtuState.LIVE_ONLY:
        return pack("Swap: LIVE → PTU", True)
    assert det.state == LivePtuState.PTU_ONLY
    return pack("Swap: PTU → LIVE", True)


def swap_live_ptu(
    game_root: str | Path,
    allow_patterns: list[str],
    *,
    dry_run: bool = False,
) -> SwapOutcome:
    """
    Rename LIVE<->PTU under game_root if exactly one exists and path is allowlisted.
    """
    root = resolve_game_root(game_root)
    if not path_matches_allowlist(root, allow_patterns):
        return SwapOutcome(
            ok=False,
            message="Game root does not match any allowlist pattern. Add a matching pattern or fix the path.",
            dry_run=dry_run,
            action=None,
        )
    if not root.is_dir():
        return SwapOutcome(
            ok=False,
            message=f"Game root is not a directory or does not exist: {root}",
            dry_run=dry_run,
            action=None,
        )
    det = detect_live_ptu(root)
    if det.state == LivePtuState.BOTH:
        return SwapOutcome(
            ok=False,
            message=describe_detection(det),
            dry_run=dry_run,
            action=None,
        )
    if det.state == LivePtuState.NEITHER:
        return SwapOutcome(
            ok=False,
            message=describe_detection(det),
            dry_run=dry_run,
            action=None,
        )
    if det.state == LivePtuState.LIVE_ONLY:
        assert det.live_path is not None
        dest = root / "PTU"
        action = "rename LIVE -> PTU"
        if dry_run:
            return SwapOutcome(
                ok=True,
                message=f"Would {action} at {root}",
                dry_run=True,
                action=action,
            )
        det.live_path.rename(dest)
        return SwapOutcome(
            ok=True,
            message=f"Renamed LIVE to PTU under {root}",
            dry_run=False,
            action=action,
        )
    assert det.state == LivePtuState.PTU_ONLY and det.ptu_path is not None
    dest = root / "LIVE"
    action = "rename PTU -> LIVE"
    if dry_run:
        return SwapOutcome(
            ok=True,
            message=f"Would {action} at {root}",
            dry_run=True,
            action=action,
        )
    det.ptu_path.rename(dest)
    return SwapOutcome(
        ok=True,
        message=f"Renamed PTU to LIVE under {root}",
        dry_run=False,
        action=action,
    )
