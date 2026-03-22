from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from rsi_versioner import config as cfg
from rsi_versioner.core import (
    describe_detection,
    detect_live_ptu,
    path_matches_allowlist,
    resolve_game_root,
    swap_live_ptu,
)


class RsiVersionerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("RSI LIVE / PTU versioner")
        self.minsize(520, 420)
        self._config = cfg.load_config()

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

        self._dry_run = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            main, text="Dry run (preview only, no rename)", variable=self._dry_run
        ).pack(anchor=tk.W, pady=(8, 0))

        action_row = ttk.Frame(main)
        action_row.pack(fill=tk.X, pady=(8, 6))
        ttk.Button(action_row, text="Refresh status", command=self._refresh_status).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(action_row, text="Preview swap", command=self._preview_swap).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(action_row, text="Swap LIVE ↔ PTU", command=self._swap).pack(
            side=tk.LEFT
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

    def _reset_defaults(self) -> None:
        self._config.allow_patterns = cfg.default_allow_patterns()
        self._root_var.set(cfg.default_game_root())
        self._populate_listbox()
        self._refresh_status()

    def _refresh_status(self) -> None:
        root_str = self._root_var.get().strip()
        patterns = self._patterns_from_ui()
        if not root_str:
            self._status_allow.set("Enter a game root path.")
            self._status_detect.set("")
            return
        try:
            resolved = resolve_game_root(root_str)
        except OSError as e:
            self._status_allow.set(f"Could not resolve path: {e}")
            self._status_detect.set("")
            return
        allowed = path_matches_allowlist(resolved, patterns)
        self._status_allow.set(
            f"Resolved: {resolved}\nAllowlist: {'OK — matches a pattern' if allowed else 'BLOCKED — no pattern matches'}"
        )
        det = detect_live_ptu(resolved)
        self._status_detect.set(describe_detection(det))

    def _save_ui_to_config(self) -> None:
        self._config.game_root = self._root_var.get().strip()
        self._config.allow_patterns = self._patterns_from_ui()
        cfg.save_config(self._config)

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
        if not root_str:
            messagebox.showwarning("Missing path", "Set a game root path.", parent=self)
            return
        if not patterns:
            messagebox.showwarning(
                "Allowlist empty",
                "Add at least one allowlist pattern before swapping.",
                parent=self,
            )
            return
        outcome = swap_live_ptu(root_str, patterns, dry_run=dry)
        self._last_result.set(outcome.message)
        self._refresh_status()
        if not outcome.ok:
            messagebox.showerror(
                "Cannot swap",
                outcome.message,
                parent=self,
            )

    def _on_close(self) -> None:
        try:
            self._save_ui_to_config()
        except OSError:
            pass
        self.destroy()


def run_gui() -> None:
    app = RsiVersionerApp()
    app.mainloop()
