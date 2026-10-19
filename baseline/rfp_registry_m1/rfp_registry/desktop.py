"""Local desktop UI. All processing is off the Tk thread; no network services."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from . import __version__
from .desktop_jobs import RunRequest, RunResult, demo_path, open_results, run_job, validate_request


class RegistryWindow:
    def __init__(
        self, root: tk.Tk, completed: Callable[[RunResult | None, str | None], None] | None = None
    ):
        self.root = root
        self.completed = completed
        self.running = False
        self.result: RunResult | None = None
        self.worker: threading.Thread | None = None
        self.events: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.source = tk.StringVar()
        self.project = tk.StringVar()
        self.results_parent = tk.StringVar(value=str(Path.home() / "RFPRegistryResults"))
        self.status = tk.StringVar(
            value="Choose a package and project, or try the built-in demonstration."
        )
        root.title(f"RFP Document Registry {__version__}")
        root.geometry("850x720")
        root.minsize(700, 650)
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.report_callback_exception = self.callback_error
        style = ttk.Style(root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Step.TLabel", font=("Segoe UI", 11, "bold"))
        main = ttk.Frame(root, padding=24)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)
        ttk.Label(main, text="RFP Document Registry", style="Title.TLabel").grid(row=0, sticky="w")
        ttk.Label(
            main, text="Retain originals, inventory packages, and extract text on this computer."
        ).grid(row=1, sticky="w", pady=(4, 16))
        self.demo_button = ttk.Button(
            main, text="Try the built-in demonstration", command=self.use_demo
        )
        self.demo_button.grid(row=2, sticky="w", pady=(0, 14))
        ttk.Label(main, text="1. Choose the source package", style="Step.TLabel").grid(
            row=3, sticky="w"
        )
        ttk.Entry(main, textvariable=self.source, state="readonly").grid(row=4, sticky="ew", pady=5)
        browse = ttk.Frame(main)
        browse.grid(row=5, sticky="w")
        self.file_button = ttk.Button(
            browse, text="Choose ZIP or document…", command=self.choose_file
        )
        self.file_button.pack(side="left", padx=(0, 8))
        self.folder_button = ttk.Button(browse, text="Choose folder…", command=self.choose_folder)
        self.folder_button.pack(side="left")
        ttk.Label(main, text="2. Enter the project / RFP name", style="Step.TLabel").grid(
            row=6, sticky="w", pady=(14, 0)
        )
        self.project_entry = ttk.Entry(main, textvariable=self.project)
        self.project_entry.grid(row=7, sticky="ew", pady=5)
        ttk.Label(main, text="3. Choose where to save results", style="Step.TLabel").grid(
            row=8, sticky="w", pady=(10, 0)
        )
        ttk.Entry(main, textvariable=self.results_parent, state="readonly").grid(
            row=9, sticky="ew", pady=5
        )
        self.results_button = ttk.Button(
            main, text="Change results folder…", command=self.choose_results
        )
        self.results_button.grid(row=10, sticky="w")
        ttk.Label(
            main, text="Each run creates a new results folder. Original files stay in place."
        ).grid(row=11, sticky="w", pady=(4, 12))
        actions = ttk.Frame(main)
        actions.grid(row=12, sticky="ew")
        self.process_button = ttk.Button(actions, text="Process package", command=self.start)
        self.process_button.pack(side="left", padx=(0, 12))
        self.open_button = ttk.Button(
            actions, text="Open results folder", command=self.open_folder, state="disabled"
        )
        self.open_button.pack(side="left")
        self.progress = ttk.Progressbar(main, mode="indeterminate")
        self.progress.grid(row=13, sticky="ew", pady=(14, 8))
        ttk.Label(main, textvariable=self.status, wraplength=760).grid(row=14, sticky="w")
        summary_frame = ttk.Frame(main)
        summary_frame.grid(row=15, sticky="nsew", pady=(8, 8))
        self.summary = tk.Text(
            summary_frame, height=9, wrap="word", state="disabled", font=("Segoe UI", 10)
        )
        scroll = ttk.Scrollbar(summary_frame, orient="vertical", command=self.summary.yview)
        self.summary.configure(yscrollcommand=scroll.set)
        self.summary.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        main.rowconfigure(15, weight=1)
        ttk.Label(
            main,
            text="Use synthetic or approved sanitized files. Classification, approval and SharePoint publishing are not enabled.",
            wraplength=760,
        ).grid(row=16, sticky="w")
        self.controls = [
            self.demo_button,
            self.file_button,
            self.folder_button,
            self.results_button,
            self.project_entry,
            self.process_button,
        ]
        self.poll_id = root.after(100, self.poll)

    def choose_file(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.root,
            title="Choose a source ZIP or document",
            filetypes=[
                ("Documents and ZIP packages", "*.zip *.pdf *.docx *.xlsx *.txt"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.source.set(path)

    def choose_folder(self) -> None:
        path = filedialog.askdirectory(parent=self.root, title="Choose the source folder")
        if path:
            self.source.set(path)

    def choose_results(self) -> None:
        path = filedialog.askdirectory(
            parent=self.root, title="Choose where new result folders will be saved"
        )
        if path:
            self.results_parent.set(path)

    def use_demo(self) -> None:
        self.source.set(str(demo_path()))
        self.project.set("SYNTHETIC-DEMO")
        self.status.set(
            "Demonstration selected: four supported documents and one deliberately unsupported CAD file. Click Process package."
        )

    def set_summary(self, text: str) -> None:
        self.summary.configure(state="normal")
        self.summary.delete("1.0", "end")
        self.summary.insert("1.0", text)
        self.summary.configure(state="disabled")

    def start(self) -> None:
        if self.running:
            return
        try:
            if not self.source.get():
                raise ValueError(
                    "Choose a source ZIP, document or folder first, or use the demonstration."
                )
            request = RunRequest(
                Path(self.source.get()), self.project.get(), Path(self.results_parent.get())
            )
            validate_request(request)
        except (ValueError, OSError) as error:
            messagebox.showerror("Check your selection", str(error), parent=self.root)
            return
        self.running = True
        self.result = None
        for widget in self.controls:
            widget["state"] = "disabled"
        self.open_button.configure(state="disabled")
        self.set_summary("Processing locally. You can leave this window open while it works.")
        self.status.set("Starting…")
        self.progress.start(12)
        self.worker = threading.Thread(target=self.work, args=(request,), daemon=False)
        self.worker.start()

    def work(self, request: RunRequest) -> None:
        try:
            result = run_job(request, lambda text: self.events.put(("progress", text)))
            self.events.put(("done", result))
        except Exception as error:
            # No document text is logged or sent anywhere. Detailed results remain local.
            self.events.put(("error", f"{type(error).__name__}: {error}"))

    def poll(self) -> None:
        try:
            while True:
                event, value = self.events.get_nowait()
                if event == "progress":
                    self.status.set(value)
                elif event in ("done", "error"):
                    self.running = False
                    self.progress.stop()
                    for widget in self.controls:
                        widget["state"] = "normal"
                    if event == "done":
                        self.result = value
                        self.set_summary(value.message)
                        self.status.set(
                            "Completed with items needing attention."
                            if value.needs_attention
                            else "Completed. Results are ready for human review."
                        )
                        self.open_button.configure(state="normal")
                    else:
                        self.status.set("Processing stopped. No files were approved or uploaded.")
                        self.set_summary(
                            "The package could not be completed.\n\n"
                            + value
                            + "\n\nKeep any partial results for troubleshooting. Use a new run after correcting the issue."
                        )
                    if self.completed:
                        self.completed(self.result, value if event == "error" else None)
        except queue.Empty:
            pass
        if self.root.winfo_exists():
            self.poll_id = self.root.after(100, self.poll)

    def open_folder(self) -> None:
        if self.result:
            try:
                open_results(self.result.output)
            except (OSError, ValueError) as error:
                messagebox.showerror("Could not open results", str(error), parent=self.root)

    def callback_error(self, kind: type[BaseException], value: BaseException, tb: Any) -> None:
        messagebox.showerror(
            "Application error",
            "The action could not be completed.\n" + str(value),
            parent=self.root,
        )

    def close(self) -> None:
        if self.running:
            messagebox.showinfo(
                "Processing in progress",
                "Please wait for this run to finish so the inventory and evidence can be saved.",
                parent=self.root,
            )
            return
        self.root.after_cancel(self.poll_id)
        self.root.destroy()


def launch() -> None:
    root = tk.Tk()
    RegistryWindow(root)
    root.mainloop()
