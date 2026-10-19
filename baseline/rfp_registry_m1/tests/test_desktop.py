import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from rfp_registry.desktop_jobs import RunRequest, demo_path, run_job, validate_request
from rfp_registry.extraction import extract


def test_desktop_demo_runs_real_pipeline_and_retains_all_sources(tmp_path):
    progress = []
    result = run_job(RunRequest(demo_path(), "DEMO", tmp_path), progress.append)
    assert result.intake["entries"] == 8
    assert result.intake["failed_entries"] == 0
    assert result.extraction == {"documents": 5, "parsed": 4, "exceptions": 1}
    assert result.needs_attention
    assert len(progress) == 2
    assert result.output.parent == tmp_path
    assert "No documents were classified, approved, or uploaded." in result.message
    assert (result.output / "registry.sqlite3").exists()


def test_desktop_repeated_runs_never_overwrite_existing_results(tmp_path):
    source = tmp_path / "note.txt"
    source.write_text("Bidder guidance", encoding="utf-8")
    request = RunRequest(source, "P", tmp_path)
    first = run_job(request)
    second = run_job(request)
    assert first.output != second.output
    assert not first.needs_attention
    assert not second.needs_attention
    assert (first.output / "manifest.json").exists()
    assert (second.output / "manifest.json").exists()


def test_desktop_requires_operator_selected_project_and_separate_output(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    with pytest.raises(ValueError, match="project"):
        validate_request(RunRequest(source, " ", tmp_path / "out"))
    with pytest.raises(ValueError, match="outside"):
        validate_request(RunRequest(source, "P", source / "out"))
    with pytest.raises(ValueError, match="outside"):
        validate_request(RunRequest(source, "P", source))


def test_desktop_failed_archive_stays_visible(tmp_path):
    source = tmp_path / "broken.zip"
    source.write_bytes(b"invalid archive")
    result = run_job(RunRequest(source, "P", tmp_path))
    assert result.needs_attention
    assert result.intake["failed_entries"] == 1
    assert not result.intake["enumeration_complete"]
    assert "Intake failures: 1" in result.message


def test_frozen_parser_launches_worker_dispatch_and_uses_file_ipc(tmp_path):
    source = tmp_path / "input with spaces.bin"
    source.write_text("evidence", encoding="utf-8")
    calls = []

    def worker(command, **kwargs):
        calls.append(command)
        assert command[:2] == [sys.executable, "--parse-worker"]
        assert command[2:4] == [str(source), "original name.txt"]
        result = {
            "status": "parsed",
            "detected_type": "txt",
            "text": "evidence",
            "evidence": [{"locator": "line:1", "start": 0, "end": 8}],
        }
        Path(command[4]).write_text(json.dumps(result), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    with (
        patch.object(sys, "frozen", True, create=True),
        patch("rfp_registry.extraction.subprocess.run", side_effect=worker),
    ):
        parsed = extract(source, "original name.txt")
    assert parsed.status == "parsed"
    assert parsed.text == "evidence"
    assert len(calls) == 1
    assert not Path(calls[0][4]).parent.exists()


def test_frozen_worker_does_not_open_another_window_on_failure(tmp_path):
    with (
        patch.object(sys, "frozen", True, create=True),
        patch(
            "rfp_registry.extraction.subprocess.run",
            return_value=subprocess.CompletedProcess([], 1),
        ),
    ):
        assert extract(tmp_path / "missing", "name.txt").error == "PARSER_PROCESS_FAILED"


def test_worker_dispatch_without_stdout(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("worker evidence", encoding="utf-8")
    report = tmp_path / "worker.json"
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "rfp_registry.desktop_entry",
            "--parse-worker",
            str(source),
            "source.txt",
            str(report),
        ],
        capture_output=True,
        check=False,
    )
    assert process.returncode == 0
    assert not process.stdout
    assert json.loads(report.read_text(encoding="utf-8"))["text"] == "worker evidence\n"


@pytest.mark.skipif(
    sys.platform != "win32" and not os.environ.get("DISPLAY"), reason="requires a desktop display"
)
def test_native_desktop_buttons_process_demo(tmp_path):
    report = tmp_path / "smoke.json"
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "rfp_registry.desktop_entry",
            "--smoke-test",
            "--output",
            str(tmp_path / "results"),
            "--result",
            str(report),
        ],
        timeout=180,
        capture_output=True,
        check=False,
    )
    assert process.returncode == 0, process.stderr.decode(errors="replace")
    assert json.loads(report.read_text(encoding="utf-8"))["ok"] is True


@pytest.mark.parametrize("root_key", ["SystemRoot", "SYSTEMROOT", "systemroot"])
def test_packaged_smoke_environment_is_windows_case_insensitive(root_key):
    from ci.verify_windows_distribution import runtime_environment

    environment = runtime_environment(
        {
            root_key: r"C:\Windows",
            "Path": r"C:\developer-python",
            "PythonPath": "developer source",
            "Tcl_Library": "external Tk",
        }
    )
    assert environment["PATH"] == r"C:\Windows\System32;C:\Windows"
    assert "PYTHONPATH" not in environment
    assert "TCL_LIBRARY" not in environment


def test_packaged_smoke_environment_requires_windows_root():
    from ci.verify_windows_distribution import runtime_environment

    with pytest.raises(ValueError, match="SYSTEMROOT"):
        runtime_environment({"PATH": "developer Python"})
