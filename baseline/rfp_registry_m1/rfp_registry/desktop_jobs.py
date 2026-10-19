"""Desktop workflow independent of the window toolkit; preserves engine policy."""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .engine import Processor
from .pipeline import register
from .safety import reject_link_chain


@dataclass(frozen=True)
class RunRequest:
    source: Path
    project: str
    results_parent: Path


@dataclass(frozen=True)
class RunResult:
    output: Path
    intake: dict[str, Any]
    extraction: dict[str, Any]

    @property
    def needs_attention(self) -> bool:
        return bool(
            self.intake["failed_entries"]
            or self.extraction["exceptions"]
            or not self.intake["enumeration_complete"]
        )

    @property
    def message(self) -> str:
        heading = (
            "Completed — some items need attention."
            if self.needs_attention
            else "Completed — ready for human review."
        )
        return (
            f"{heading}\n\n"
            f"Inventory entries: {self.intake['entries']}\n"
            f"Retained files: {self.intake['stored_files']}\n"
            f"Intake failures: {self.intake['failed_entries']}\n"
            f"Documents with extracted text: {self.extraction['parsed']}\n"
            f"Documents needing attention: {self.extraction['exceptions']}\n\n"
            "No documents were classified, approved, or uploaded.\n"
            f"Results saved in:\n{self.output}"
        )


def demo_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(vars(sys)["_MEIPASS"]) / "assets" / "synthetic_vertical_slice.zip"
    return Path(__file__).resolve().parents[1] / "examples" / "synthetic_vertical_slice.zip"


def validate_request(request: RunRequest) -> None:
    if not request.project.strip():
        raise ValueError("Enter the project or RFP name you selected for this package.")
    if len(request.project.strip()) > 200:
        raise ValueError("Keep the project name to 200 characters or fewer.")
    reject_link_chain(request.source.absolute())
    reject_link_chain(request.results_parent.absolute())
    source = request.source.resolve(strict=True)
    parent = request.results_parent.resolve()
    if not source.is_file() and not source.is_dir():
        raise ValueError("Choose an existing file or folder to process.")
    if parent.exists() and not parent.is_dir():
        raise ValueError("Choose a folder for results, not a file.")
    if source == parent or source in parent.parents:
        raise ValueError("Choose a results folder outside the source package or folder.")


def run_job(request: RunRequest, progress: Callable[[str], None] = lambda _: None) -> RunResult:
    validate_request(request)
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    output = request.results_parent / f"run-{stamp}-{uuid.uuid4().hex[:8]}"
    progress("Retaining originals and inventorying files…")
    intake = Processor(request.source, output, request.project.strip()).run()
    progress("Extracting document text locally…")
    extraction = register(output)
    return RunResult(output, intake, extraction)


def open_results(path: Path) -> None:
    """Only launch the OS folder viewer; never execute document content."""
    reject_link_chain(path.absolute())
    path = path.resolve(strict=True)
    if not path.is_dir():
        raise ValueError("The results folder is not available.")
    if sys.platform == "win32":
        os.startfile(str(path))
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])
