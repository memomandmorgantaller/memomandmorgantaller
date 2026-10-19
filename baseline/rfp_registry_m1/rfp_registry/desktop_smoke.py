"""CI exercises the actual demo and Process button, including frozen parser children."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path

from .desktop import RegistryWindow
from .desktop_jobs import RunResult
from .safety import atomic_json


def smoke_test(output: Path, report: Path) -> None:
    root = tk.Tk()
    outcome: dict = {"ok": False, "error": "GUI did not complete"}

    def completed(result: RunResult | None, error: str | None) -> None:
        if result:
            ok = (
                result.intake["entries"] == 8
                and result.intake["failed_entries"] == 0
                and result.extraction == {"documents": 5, "parsed": 4, "exceptions": 1}
                and result.needs_attention
                and not app.running
                and str(app.open_button["state"]) == "normal"
            )
            outcome.update(
                ok=ok,
                output=str(result.output),
                intake=result.intake,
                extraction=result.extraction,
                error=None if ok else "Unexpected demo result",
            )
        else:
            outcome.update(ok=False, error=error)
        root.after(10, root.destroy)

    app = RegistryWindow(root, completed)
    root.report_callback_exception = lambda kind, value, tb: completed(None, str(value))
    app.results_parent.set(str(output))

    def start() -> None:
        app.demo_button.invoke()
        app.process_button.invoke()

    def expired() -> None:
        outcome.update(ok=False, error="Desktop smoke test timed out")
        root.destroy()

    root.after(200, start)
    root.after(150000, expired)
    root.mainloop()
    if app.worker:
        app.worker.join(timeout=25)
    atomic_json(report, outcome)
    if not outcome["ok"]:
        raise SystemExit(1)
