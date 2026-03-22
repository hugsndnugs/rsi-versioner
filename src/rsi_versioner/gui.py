from __future__ import annotations

import logging
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from rsi_versioner import config as cfg
from rsi_versioner.core import (
    LivePtuState,
    describe_detection,
    detect_live_ptu,
    path_matches_allowlist,
    pattern_usable_as_game_root,
    paths_equal,
    resolve_game_root,
    swap_buttons_view,
    swap_live_ptu,
    validate_undo_expected_state,
)
from rsi_versioner.logging_config import log_file_path, LOGGER_NAME
from rsi_versioner.undo_state import (
    UndoRecord,
    clear_undo_record,
    load_undo_record,
    save_undo_record,
)

logger = logging.getLogger(LOGGER_NAME)
_UNDO_MSGBOX_TITLE = "Cannot undo"


def _purge_stale_undo() -> None:
    rec = load_undo_record()
    if rec is None:
        return
    try:
        root = Path(rec.game_root_resolved).resolve(strict=False)
    except OSError:
        clear_undo_record()
        return
    if not root.is_dir():
        clear_undo_record()
        return
    det = detect_live_ptu(root)
    try:
        expected = LivePtuState(rec.state_after)
    except ValueError:
        clear_undo_record()
        return
    if not validate_undo_expected_state(det, expected):
        clear_undo_record()


class RsiVersionerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("RSI LIVE / PTU versioner")
        self.minsize(520, 460)
        self._config = cfg.load_config()
        _purge_stale_undo()

        main = ttk.Frame(self, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Game root (folder containing LIVE / PTU):").pack(
            anchor=tk.W
        )
        row = ttk.Frame(main)
        row.pack(fill=tk.X, pady=(0, 6))
        self._root_var = tk.StringVar(value=self._config.game_root)
        self._root_entry = ttk.Entry(row, textvariable=self._root_var)
        self._root_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        ttk.Button(row, text="Browse…", command=self._browse_root).pack(side=tk.RIGHT)

        ttk.Label(main, text="Allowlist (glob patterns; game root must match one):").pack(
            anchor=tk.W, pady=(8, 0)
        )
        list_frame = ttk.Frame(main)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 6))
        self._listbox = tk.Listbox(
            list_frame, height=6, selectmode=tk.EXTENDED, exportselection=False
        )
        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self._listbox.yview)
        self._listbox.configure(yscrollcommand=scroll.set)
        self._listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._listbox.bind("<<ListboxSelect>>", lambda _e: self._sync_use_selection_button())
        self._listbox.bind("<Double-Button-1>", self._on_listbox_double_click)

        btn_row = ttk.Frame(main)
        btn_row.pack(fill=tk.X)
        ttk.Button(btn_row, text="Add pattern…", command=self._add_pattern).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(btn_row, text="Remove selected", command=self._remove_selected).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(btn_row, text="Reset defaults", command=self._reset_defaults).pack(
            side=tk.LEFT
        )
        self._use_sel_btn = ttk.Button(
            btn_row,
            text="Use selection as game root",
            command=self._use_selection_as_game_root,
            state=tk.DISABLED,
        )
        self._use_sel_btn.pack(side=tk.LEFT, padx=(12, 0))

        self._dry_run = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            main, text="Dry run (preview only, no rename)", variable=self._dry_run
        ).pack(anchor=tk.W, pady=(8, 0))

        action_row = ttk.Frame(main)
        action_row.pack(fill=tk.X, pady=(8, 6))
        ttk.Button(action_row, text="Refresh status", command=self._refresh_status).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        self._preview_btn = ttk.Button(
            action_row, text="Preview swap", command=self._preview_swap
        )
        self._preview_btn.pack(side=tk.LEFT, padx=(0, 6))
        self._swap_btn = ttk.Button(action_row, text="Swap LIVE ↔ PTU", command=self._swap)
        self._swap_btn.pack(side=tk.LEFT, padx=(0, 6))
        self._undo_btn = ttk.Button(
            action_row, text="Undo last rename", command=self._undo, state=tk.DISABLED
        )
        self._undo_btn.pack(side=tk.LEFT)

        log_row = ttk.Frame(main)
        log_row.pack(fill=tk.X, pady=(4, 0))
        ttk.Button(log_row, text="Open log folder", command=self._open_log_folder).pack(
            anchor=tk.W
        )

        self._status_allow = tk.StringVar(value="")
        self._status_detect = tk.StringVar(value="")
        ttk.Label(main, textvariable=self._status_allow, wraplength=480).pack(
            anchor=tk.W, pady=(4, 0)
        )
        ttk.Label(main, textvariable=self._status_detect, wraplength=480).pack(
            anchor=tk.W, pady=(2, 0)
        )
        self._last_result = tk.StringVar(value="")
        ttk.Label(main, textvariable=self._last_result, wraplength=480).pack(
            anchor=tk.W, pady=(6, 0)
        )

        self._populate_listbox()
        self._sync_use_selection_button()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._refresh_status()

    def _patterns_from_ui(self) -> list[str]:
        items = self._listbox.get(0, tk.END)
        return [str(x).strip() for x in items if str(x).strip()]

    def _populate_listbox(self) -> None:
        self._listbox.delete(0, tk.END)
        for p in self._config.allow_patterns:
            self._listbox.insert(tk.END, p)

    def _browse_root(self) -> None:
        initial = self._root_var.get().strip()
        if not initial or not Path(initial).is_dir():
            initial = self._config.game_root
        path = filedialog.askdirectory(
            title="Select StarCitizen game root",
            initialdir=initial if Path(initial).is_dir() else None,
        )
        if path:
            self._root_var.set(path)
            self._refresh_status()

    def _add_pattern(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Add allowlist pattern")
        dialog.transient(self)
        dialog.grab_set()
        var = tk.StringVar()
        ttk.Label(
            dialog,
            text="Glob pattern (forward slashes ok; * matches segments).",
            wraplength=400,
        ).pack(padx=10, pady=(10, 4))
        entry = ttk.Entry(dialog, textvariable=var, width=56)
        entry.pack(padx=10, pady=4, fill=tk.X)

        def ok() -> None:
            text = var.get().strip()
            if text:
                self._listbox.insert(tk.END, text)
                self._sync_use_selection_button()
            dialog.destroy()

        def cancel() -> None:
            dialog.destroy()

        btns = ttk.Frame(dialog)
        btns.pack(pady=10)
        ttk.Button(btns, text="Add", command=ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=4)
        entry.focus_set()
        dialog.bind("<Return>", lambda e: ok())

    def _remove_selected(self) -> None:
        sel = list(self._listbox.curselection())
        if not sel:
            return
        for i in reversed(sel):
            self._listbox.delete(i)
        self._sync_use_selection_button()

    def _sync_use_selection_button(self) -> None:
        sel = self._listbox.curselection()
        ok = (
            len(sel) == 1
            and pattern_usable_as_game_root(str(self._listbox.get(sel[0])))
        )
        self._use_sel_btn.configure(state=tk.NORMAL if ok else tk.DISABLED)

    def _use_selection_as_game_root(self) -> None:
        sel = self._listbox.curselection()
        if len(sel) != 1:
            return
        text = str(self._listbox.get(sel[0]))
        if not pattern_usable_as_game_root(text):
            messagebox.showinfo(
                "Glob pattern",
                "This pattern is a glob; enter or browse to the real folder.",
                parent=self,
            )
            return
        self._root_var.set(text.strip())
        self._refresh_status()

    def _on_listbox_double_click(self, event: tk.Event) -> None:
        idx = self._listbox.nearest(event.y)
        if idx < 0:
            return
        self._listbox.selection_clear(0, tk.END)
        self._listbox.selection_set(idx)
        self._sync_use_selection_button()
        self._use_selection_as_game_root()

    def _apply_swap_preview_labels(
        self, view: tuple[str, bool, str, bool]
    ) -> None:
        swap_t, swap_en, prev_t, prev_en = view
        self._swap_btn.configure(
            text=swap_t, state=tk.NORMAL if swap_en else tk.DISABLED
        )
        self._preview_btn.configure(
            text=prev_t, state=tk.NORMAL if prev_en else tk.DISABLED
        )

    def _reset_defaults(self) -> None:
        self._config.allow_patterns = cfg.default_allow_patterns()
        self._root_var.set(cfg.default_game_root())
        self._populate_listbox()
        self._sync_use_selection_button()
        self._refresh_status()

    def _maybe_clear_stale_undo_for_ui_root(self, resolved_ui: Path) -> None:
        rec = load_undo_record()
        if rec is None:
            return
        try:
            rec_root = Path(rec.game_root_resolved).resolve(strict=False)
        except OSError:
            return
        if not paths_equal(rec_root, resolved_ui):
            return
        det = detect_live_ptu(resolved_ui)
        try:
            expected = LivePtuState(rec.state_after)
        except ValueError:
            clear_undo_record()
            return
        if not validate_undo_expected_state(det, expected):
            clear_undo_record()

    def _update_undo_button(self) -> None:
        rec = load_undo_record()
        if rec is None:
            self._undo_btn.configure(state=tk.DISABLED)
            return
        ui_root_str = self._root_var.get().strip()
        patterns = self._patterns_from_ui()
        if not ui_root_str or not patterns:
            self._undo_btn.configure(state=tk.DISABLED)
            return
        try:
            rec_root = Path(rec.game_root_resolved).resolve(strict=False)
            ui_root = resolve_game_root(ui_root_str)
        except OSError:
            self._undo_btn.configure(state=tk.DISABLED)
            return
        if not paths_equal(rec_root, ui_root):
            self._undo_btn.configure(state=tk.DISABLED)
            return
        if not path_matches_allowlist(rec_root, patterns):
            self._undo_btn.configure(state=tk.DISABLED)
            return
        det = detect_live_ptu(rec_root)
        try:
            expected = LivePtuState(rec.state_after)
        except ValueError:
            self._undo_btn.configure(state=tk.DISABLED)
            return
        if not validate_undo_expected_state(det, expected):
            self._undo_btn.configure(state=tk.DISABLED)
            return
        self._undo_btn.configure(state=tk.NORMAL)

    def _refresh_status(self) -> None:
        root_str = self._root_var.get().strip()
        patterns = self._patterns_from_ui()
        patterns_ok = bool(patterns)
        if not root_str:
            self._status_allow.set("Enter a game root path.")
            self._status_detect.set("")
            self._apply_swap_preview_labels(
                swap_buttons_view(
                    root_non_empty=False,
                    resolve_failed=False,
                    resolved=None,
                    patterns_non_empty=patterns_ok,
                    allowed=False,
                    det=None,
                )
            )
            self._update_undo_button()
            return
        try:
            resolved = resolve_game_root(root_str)
        except OSError as e:
            self._status_allow.set(f"Could not resolve path: {e}")
            self._status_detect.set("")
            self._apply_swap_preview_labels(
                swap_buttons_view(
                    root_non_empty=True,
                    resolve_failed=True,
                    resolved=None,
                    patterns_non_empty=patterns_ok,
                    allowed=False,
                    det=None,
                )
            )
            self._update_undo_button()
            return
        self._maybe_clear_stale_undo_for_ui_root(resolved)
        allowed = path_matches_allowlist(resolved, patterns)
        self._status_allow.set(
            f"Resolved: {resolved}\nAllowlist: {'OK — matches a pattern' if allowed else 'BLOCKED — no pattern matches'}"
        )
        det = detect_live_ptu(resolved)
        self._status_detect.set(describe_detection(det))
        self._apply_swap_preview_labels(
            swap_buttons_view(
                root_non_empty=True,
                resolve_failed=False,
                resolved=resolved,
                patterns_non_empty=patterns_ok,
                allowed=allowed,
                det=det,
            )
        )
        self._update_undo_button()

    def _save_ui_to_config(self) -> None:
        self._config.game_root = self._root_var.get().strip()
        self._config.allow_patterns = self._patterns_from_ui()
        cfg.save_config(self._config)

    def _log_outcome(
        self,
        event: str,
        root_str: str,
        dry: bool,
        outcome_ok: bool,
        action: str,
        message: str,
    ) -> None:
        logger.info(
            "event=%s root=%s dry_run=%s ok=%s action=%s msg=%s",
            event,
            root_str,
            dry,
            outcome_ok,
            action,
            message.replace("\n", " "),
        )

    def _preview_swap(self) -> None:
        self._run_swap(force_dry_run=True)

    def _swap(self) -> None:
        if not self._dry_run.get() and not messagebox.askyesno(
            "Confirm rename",
            "Perform LIVE ↔ PTU folder rename on disk?",
            parent=self,
        ):
            return
        self._run_swap(force_dry_run=False)

    def _run_swap(self, *, force_dry_run: bool) -> None:
        self._refresh_status()
        root_str = self._root_var.get().strip()
        patterns = self._patterns_from_ui()
        dry = force_dry_run or self._dry_run.get()
        event = "preview" if dry else "swap"
        if not root_str:
            messagebox.showwarning("Missing path", "Set a game root path.", parent=self)
            self._log_outcome(event, "", dry, False, "", "missing game root")
            return
        if not patterns:
            messagebox.showwarning(
                "Allowlist empty",
                "Add at least one allowlist pattern before swapping.",
                parent=self,
            )
            self._log_outcome(event, root_str, dry, False, "", "allowlist empty")
            return
        try:
            resolved = resolve_game_root(root_str)
            det_before = None
            if not dry:
                det_before = detect_live_ptu(resolved)
            outcome = swap_live_ptu(root_str, patterns, dry_run=dry)
        except OSError as e:
            logger.exception("event=%s root=%s OSError", event, root_str)
            self._last_result.set(str(e))
            messagebox.showerror("Error", str(e), parent=self)
            self._update_undo_button()
            return
        except Exception as e:
            logger.exception("event=%s root=%s failed", event, root_str)
            self._last_result.set(str(e))
            messagebox.showerror("Error", str(e), parent=self)
            self._update_undo_button()
            return

        self._last_result.set(outcome.message)
        self._log_outcome(
            event,
            str(resolved),
            dry,
            outcome.ok,
            outcome.action or "",
            outcome.message,
        )
        if (
            outcome.ok
            and not outcome.dry_run
            and det_before is not None
            and det_before.state
            in (LivePtuState.LIVE_ONLY, LivePtuState.PTU_ONLY)
        ):
            after = (
                LivePtuState.PTU_ONLY
                if det_before.state == LivePtuState.LIVE_ONLY
                else LivePtuState.LIVE_ONLY
            )
            save_undo_record(
                UndoRecord(
                    game_root_resolved=str(resolved),
                    state_before=det_before.state.value,
                    state_after=after.value,
                )
            )
        self._refresh_status()
        if not outcome.ok:
            messagebox.showerror(
                "Cannot swap",
                outcome.message,
                parent=self,
            )

    def _undo_resolved_root_or_fail(self, rec: UndoRecord, patterns: list[str]) -> Path | None:
        try:
            rec_root = Path(rec.game_root_resolved).resolve(strict=False)
        except OSError as e:
            clear_undo_record()
            messagebox.showerror(_UNDO_MSGBOX_TITLE, str(e), parent=self)
            self._refresh_status()
            return None
        if not path_matches_allowlist(rec_root, patterns):
            clear_undo_record()
            messagebox.showerror(
                _UNDO_MSGBOX_TITLE,
                "Game root no longer matches the allowlist; undo cancelled.",
                parent=self,
            )
            self._refresh_status()
            return None
        det = detect_live_ptu(rec_root)
        try:
            expected = LivePtuState(rec.state_after)
        except ValueError:
            clear_undo_record()
            self._refresh_status()
            return None
        if not validate_undo_expected_state(det, expected):
            clear_undo_record()
            messagebox.showerror(
                _UNDO_MSGBOX_TITLE,
                "Folder state changed since the last rename; undo is no longer safe.",
                parent=self,
            )
            self._refresh_status()
            return None
        return rec_root

    def _undo(self) -> None:
        rec = load_undo_record()
        if rec is None:
            return
        if not messagebox.askyesno(
            "Confirm undo",
            "Reverse the last LIVE ↔ PTU rename on disk?",
            parent=self,
        ):
            return
        patterns = self._patterns_from_ui()
        rec_root = self._undo_resolved_root_or_fail(rec, patterns)
        if rec_root is None:
            return
        try:
            outcome = swap_live_ptu(rec_root, patterns, dry_run=False)
        except OSError as e:
            logger.exception("event=undo root=%s OSError", rec_root)
            self._last_result.set(str(e))
            messagebox.showerror("Error", str(e), parent=self)
            self._update_undo_button()
            return
        except Exception as e:
            logger.exception("event=undo root=%s failed", rec_root)
            self._last_result.set(str(e))
            messagebox.showerror("Error", str(e), parent=self)
            self._update_undo_button()
            return

        self._last_result.set(outcome.message)
        self._log_outcome(
            "undo",
            str(rec_root),
            False,
            outcome.ok,
            outcome.action or "",
            outcome.message,
        )
        if outcome.ok:
            clear_undo_record()
        self._refresh_status()
        if not outcome.ok:
            messagebox.showerror(
                _UNDO_MSGBOX_TITLE,
                outcome.message,
                parent=self,
            )

    def _open_log_folder(self) -> None:
        path = log_file_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        folder = path.parent
        try:
            if os.name == "nt":
                os.startfile(folder)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(["open", str(folder)], check=False)
            else:
                subprocess.run(["xdg-open", str(folder)], check=False)
        except OSError as e:
            messagebox.showerror("Could not open folder", str(e), parent=self)

    def _on_close(self) -> None:
        try:
            self._save_ui_to_config()
        except OSError:
            pass
        self.destroy()


def run_gui() -> None:
    from rsi_versioner.logging_config import configure_logging

    configure_logging()
    app = RsiVersionerApp()
    app.mainloop()
